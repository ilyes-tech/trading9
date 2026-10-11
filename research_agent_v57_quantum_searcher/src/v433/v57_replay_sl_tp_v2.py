from pathlib import Path
import json
import math
import sys
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_strategy_dsl_v2 as dsl
import v57_strategy_signal_engine_v2 as signal_engine
import v57_replay_sl_tp_v1 as reference
import v57_replay_evaluator_v1 as legacy_replay
import v57_candidate_schema_v1 as legacy_schema
import v57_fold_signal_adapter_v1 as adapter

v56=legacy_replay.v56

def _seg_end(valid,e):
    j=int(e)
    while j+1<len(valid) and bool(valid[j+1]):
        j+=1
    return j

def _arrays_to_boundary(z,end_time):
    mt=np.asarray(z["m1_time"],dtype=np.int64)
    dm=int(np.searchsorted(mt,int(end_time),side="left"))
    if dm<len(mt):
        return (mt,z["m1_open"],z["m1_high"],z["m1_low"],z["m1_close"],z["spread"],z["scheduled"],dm)
    if dm!=len(mt) or len(mt)==0 or int(end_time)<=int(mt[-1]):
        raise ValueError("BAD_CENSOR_BOUNDARY")
    last=float(z["m1_close"][-1])
    t=np.r_[mt,np.int64(end_time)]
    o=np.r_[z["m1_open"],last]
    h=np.r_[z["m1_high"],last]
    l=np.r_[z["m1_low"],last]
    c=np.r_[z["m1_close"],last]
    sp=np.r_[z["spread"],0.0]
    sched=np.r_[z["scheduled"],bool(int(end_time)-int(mt[-1])!=60)]
    return (t,o,h,l,c,sp,sched,len(mt))

def _validate_context_strategy(ctx,strategy):
    dsl.validate_strategy(strategy)
    sm=strategy["market"]
    symbol=str(sm["symbol"])
    timeframe=str(sm["timeframe"])
    side=str(sm["side"]).upper()
    if symbol!=ctx["market"] or timeframe!=ctx["timeframe"]:
        raise ValueError("CONTEXT_STRATEGY_MISMATCH")
    if side not in ("LONG","SHORT"):
        raise ValueError("BAD_SIDE:"+side)
    risk=strategy.get("risk")
    legacy_schema.validate_risk_model(risk,timeframe)
    return symbol,timeframe,side,risk

def _risk_levels(ctx,risk,signal_i,entry_m1,side,atr_series):
    return legacy_replay._risk_levels(
        ctx,
        {"risk_model":risk},
        int(signal_i),
        int(entry_m1),
        side,
        atr_series,
    )

def evaluate_fold(ctx,strategy,fold_index):
    symbol,timeframe,side,risk=_validate_context_strategy(ctx,strategy)
    train,valid=adapter.fold_masks(ctx,fold_index)
    valid=np.asarray(valid,dtype=bool)
    sig=signal_engine.strategy_signal(ctx["v57_cache"],strategy,ctx["sec"],train,symbol)
    signals=np.flatnonzero(np.asarray(sig["signal"],dtype=bool)&valid)
    z=dict(ctx)
    z["spread"]=v56.fold_spread(ctx,fold_index)
    atr=legacy_replay._risk_atr(z["v57_cache"],z["sec"],risk["atr_window"])
    pre=[]
    rejected=0
    for s in signals:
        e=int(s)+1
        if e>=len(valid) or not valid[e]:
            continue
        a=int(z["tf_to_m1"][s])
        em=int(z["tf_to_m1"][e])
        if em<=a or np.any(z["unexpected"][a:em]):
            continue
        end_tf=_seg_end(valid,e)
        end_time=int(z["tf_time"][end_tf])+int(z["sec"])
        t,o,h,l,c,sp,sched,dm=_arrays_to_boundary(z,end_time)
        lv=_risk_levels(z,risk,int(s),em,side,atr)
        if lv is None:
            rejected+=1
            continue
        q=v56.base.replay.replay_trade(
            z["market"],side,t,o,h,l,c,sp,em,dm,
            float(lv["stop"]),float(lv["target"]),sched
        )
        if not q.get("eligible",False):
            rejected+=1
            continue
        q["signal_tf_i"]=int(s)
        if q["reason"]!="TIME":
            q=v56.base.replay.apply_costs(z["asset_class"],q)
        pre.append(q)
    selected=v56.select_nonoverlap(pre)
    censored=[q for q in selected if q["reason"]=="TIME"]
    resolved=[q for q in selected if q["reason"]!="TIME"]
    base=np.asarray([q["base_net_bps"] for q in resolved],dtype=float)
    stress=np.asarray([q["stress_net_bps"] for q in resolved],dtype=float)
    days=float(valid.sum()*z["sec"]/86400.0)
    out=v56.fold_summary(base,stress,days,z["timeframe"])
    gate=json.loads((HERE.parents[2]/"config/V57_QUANTUM_SEARCHER_CONTRACT_V1.json").read_text())["gate"]
    out["pass"]=bool(
        len(base)>=int(gate["min_trades_per_fold"])
        and out["tpd"]>=float(gate["min_active_market_tpd"])
        and out["base_avg_bps"] is not None
        and out["base_avg_bps"]>float(gate["base_avg_bps_gt"])
        and out["base_pf"]>=float(gate["base_pf_gte"])
        and out["stress_avg_bps"] is not None
        and out["stress_avg_bps"]>float(gate["stress_avg_bps_gt"])
        and out["stress_pf"]>=float(gate["stress_pf_gte"])
    )
    out["gate_source"]="V57_QUANTUM_SEARCHER_CONTRACT_V1"
    out["fold_index"]=int(fold_index)
    out["side"]=side
    out["signal_events"]=int(len(signals))
    out["selected_trades"]=int(len(resolved))
    out["right_censored"]=int(len(censored))
    out["rejected"]=int(rejected)
    out["thresholds"]=[float(x) for x in sig["thresholds"]]
    out["exit_counts"]={k:int(sum(1 for q in resolved if q["reason"]==k)) for k in ("STOP","STOP_GAP","TARGET","TARGET_GAP")}
    out["signal_engine"]=sig["engine"]
    return out

def evaluate_strategy(ctx,strategy):
    symbol,timeframe,side,_=_validate_context_strategy(ctx,strategy)
    folds=[evaluate_fold(ctx,strategy,i) for i in range(len(v56.POL["folds"]))]
    cv=lambda x:(-float("inf") if x is None else float(x))
    return {
        "strategy_id":strategy["strategy_id"],
        "legacy_candidate_id":strategy.get("legacy",{}).get("candidate_id"),
        "market":symbol,
        "timeframe":timeframe,
        "side":side,
        "exit_semantics":"SL_TP_ONLY_RIGHT_CENSOR",
        "folds":folds,
        "exact_pass":bool(all(f["pass"] for f in folds)),
        "worst_stress_avg_bps":min(cv(f["stress_avg_bps"]) for f in folds),
        "min_stress_pf":min(float(f["stress_pf"]) for f in folds),
        "worst_base_avg_bps":min(cv(f["base_avg_bps"]) for f in folds),
        "min_base_pf":min(float(f["base_pf"]) for f in folds),
        "mean_stress_avg_bps":float(np.mean([cv(f["stress_avg_bps"]) for f in folds])),
        "mean_base_avg_bps":float(np.mean([cv(f["base_avg_bps"]) for f in folds])),
        "worst_drawdown_bps":min(float(f["drawdown_bps"]) for f in folds),
        "total_selected_trades":int(sum(f["selected_trades"] for f in folds)),
        "total_right_censored":int(sum(f["right_censored"] for f in folds)),
    }

def _same_value(a,b):
    if a is None or b is None:
        return a is b
    if isinstance(a,(bool,str,int)) or isinstance(b,(bool,str,int)):
        return a==b
    try:
        af=float(a); bf=float(b)
        if math.isnan(af) and math.isnan(bf):
            return True
        return af==bf
    except Exception:
        return a==b

def _fold_diff(old,new):
    keys=(
        "pass","base_avg_bps","base_pf","stress_avg_bps","stress_pf",
        "drawdown_bps","tpd","signal_events","selected_trades",
        "right_censored","rejected","exit_counts"
    )
    diffs=[]
    for k in keys:
        if k=="exit_counts":
            if old.get(k)!=new.get(k):
                diffs.append(k)
        elif not _same_value(old.get(k),new.get(k)):
            diffs.append(k)
    if sorted(float(x) for x in old.get("thresholds",[]))!=sorted(float(x) for x in new.get("thresholds",[])):
        diffs.append("thresholds")
    return diffs

def parity_bundle(ctx,bundle):
    candidate=bundle["candidate"]
    side=str(bundle.get("side") or candidate.get("side") or "LONG").upper()
    strategy=dsl.from_v1_candidate(candidate,side)
    old=reference.evaluate_candidate(ctx,candidate,side)
    new=evaluate_strategy(ctx,strategy)
    failures=[]
    if len(old["folds"])!=len(new["folds"]):
        failures.append("fold_count")
    else:
        for i,(a,b) in enumerate(zip(old["folds"],new["folds"])):
            d=_fold_diff(a,b)
            if d:
                failures.append("fold%d:%s"%(i,",".join(d)))
    for k in (
        "exact_pass","worst_stress_avg_bps","min_stress_pf",
        "worst_base_avg_bps","min_base_pf","mean_stress_avg_bps",
        "mean_base_avg_bps","worst_drawdown_bps","total_selected_trades",
        "total_right_censored"
    ):
        if not _same_value(old.get(k),new.get(k)):
            failures.append("summary:"+k)
    return {
        "pass":not failures,
        "failures":failures,
        "strategy_id":strategy["strategy_id"],
        "candidate_id":candidate.get("candidate_id"),
        "market":candidate["market"],
        "timeframe":candidate["timeframe"],
        "side":side,
    }

def parity_ready_audit(limit=None):
    ready=HERE.parents[2]/"work/autopilot_v432/shadow_ready"
    files=sorted(ready.glob("*.json"))
    if not files:
        raise RuntimeError("NO_V432_READY")
    if limit is not None:
        files=files[:int(limit)]
    contexts={}
    failures=[]
    for j,p in enumerate(files,1):
        z=json.loads(p.read_text())
        c=z["candidate"]
        key=(c["market"],c["timeframe"])
        if key not in contexts:
            contexts[key]=adapter.prepare_context(*key)
        r=parity_bundle(contexts[key],z)
        if not r["pass"]:
            failures.append((p.name,r["failures"]))
            print("REPLAY_PARITY_FAIL|FILE=%s|DETAIL=%s"%(p.name,";".join(r["failures"])))
        if j%10==0 or j==len(files):
            print("REPLAY_PARITY_PROGRESS|DONE=%d|TOTAL=%d|FAILURES=%d"%(j,len(files),len(failures)),flush=True)
    checks=len(files)*len(v56.POL["folds"])
    print("V57_V433_REPLAY_V2_PARITY_AUDIT|READY=%d|FOLD_CHECKS=%d|FAILURES=%d"%(len(files),checks,len(failures)))
    if failures:
        raise SystemExit(2)
    print("V57_V433_REPLAY_V2_PARITY=PASS|EXIT=SL_TP_ONLY_RIGHT_CENSOR|HOLDOUT=UNREAD|ORDERS=DISABLED")

def self_check():
    import inspect
    src=inspect.getsource(evaluate_fold)
    assert "signal_engine.strategy_signal" in src
    assert "time_stop_bars" not in src
    assert 'q["reason"]!="TIME"' in src
    assert "_risk_levels(z,risk" in src
    print("V57_V433_REPLAY_SL_TP_V2_SELF_CHECK=PASS|DSL_SIGNAL_ENGINE=V2|TIME_STOP=ABSENT|RIGHT_CENSOR=PASS|ORDERS=DISABLED")

if __name__=="__main__":
    if "--parity-ready" in sys.argv:
        parity_ready_audit()
    elif "--parity-sample" in sys.argv:
        i=sys.argv.index("--parity-sample")
        if i+1>=len(sys.argv):
            raise SystemExit("MISSING_SAMPLE_SIZE")
        parity_ready_audit(int(sys.argv[i+1]))
    else:
        self_check()
