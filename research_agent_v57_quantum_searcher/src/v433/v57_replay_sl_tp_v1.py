from pathlib import Path
import sys
import numpy as np

SRC=(Path("research_agent_v57_quantum_searcher")/"src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

import v57_replay_evaluator_v1 as old
import v57_candidate_schema_v1 as schema
import v57_fold_signal_adapter_v1 as adapter

v56=old.v56

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

def evaluate_fold(ctx,candidate,fold_index,side):
    schema.validate_candidate(candidate)
    side=str(side).upper()
    if side not in ("LONG","SHORT"):
        raise ValueError("BAD_SIDE:"+side)
    train,valid=adapter.fold_masks(ctx,fold_index)
    valid=np.asarray(valid,dtype=bool)
    sig=adapter.signal_engine.candidate_signal(ctx["v57_cache"],candidate,ctx["sec"],train,ctx["market"])
    signals=np.flatnonzero(np.asarray(sig["signal"],dtype=bool)&valid)
    z=dict(ctx)
    z["spread"]=v56.fold_spread(ctx,fold_index)
    atr=old._risk_atr(z["v57_cache"],z["sec"],candidate["risk_model"]["atr_window"])
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
        lv=old._risk_levels(z,candidate,int(s),em,side,atr)
        if lv is None:
            rejected+=1
            continue
        q=v56.base.replay.replay_trade(z["market"],side,t,o,h,l,c,sp,em,dm,float(lv["stop"]),float(lv["target"]),sched)
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
    out=v56.fold_summary(base,stress,days,z["timeframe"]); g=__import__("json").loads(Path("research_agent_v57_quantum_searcher/config/V57_QUANTUM_SEARCHER_CONTRACT_V1.json").read_text())["gate"]; out["pass"]=bool(len(base)>=int(g["min_trades_per_fold"]) and out["tpd"]>=float(g["min_active_market_tpd"]) and out["base_avg_bps"] is not None and out["base_avg_bps"]>float(g["base_avg_bps_gt"]) and out["base_pf"]>=float(g["base_pf_gte"]) and out["stress_avg_bps"] is not None and out["stress_avg_bps"]>float(g["stress_avg_bps_gt"]) and out["stress_pf"]>=float(g["stress_pf_gte"])); out["gate_source"]="V57_QUANTUM_SEARCHER_CONTRACT_V1"
    out["fold_index"]=int(fold_index)
    out["side"]=side
    out["signal_events"]=int(len(signals))
    out["selected_trades"]=int(len(resolved))
    out["right_censored"]=int(len(censored))
    out["rejected"]=int(rejected)
    out["thresholds"]=[float(x) for x in sig["thresholds"]]
    out["exit_counts"]={k:int(sum(1 for q in resolved if q["reason"]==k)) for k in ("STOP","STOP_GAP","TARGET","TARGET_GAP")}
    return out

def evaluate_candidate(ctx,candidate,side):
    folds=[evaluate_fold(ctx,candidate,i,side) for i in range(len(v56.POL["folds"]))]
    cv=lambda x:(-float("inf") if x is None else float(x))
    return {"candidate_id":candidate.get("candidate_id",schema.candidate_id(candidate)),"market":candidate["market"],"timeframe":candidate["timeframe"],"side":str(side).upper(),"exit_semantics":"SL_TP_ONLY_RIGHT_CENSOR","folds":folds,"exact_pass":bool(all(f["pass"] for f in folds)),"worst_stress_avg_bps":min(cv(f["stress_avg_bps"]) for f in folds),"min_stress_pf":min(float(f["stress_pf"]) for f in folds),"worst_base_avg_bps":min(cv(f["base_avg_bps"]) for f in folds),"min_base_pf":min(float(f["base_pf"]) for f in folds),"mean_stress_avg_bps":float(np.mean([cv(f["stress_avg_bps"]) for f in folds])),"mean_base_avg_bps":float(np.mean([cv(f["base_avg_bps"]) for f in folds])),"worst_drawdown_bps":min(float(f["drawdown_bps"]) for f in folds),"total_selected_trades":int(sum(f["selected_trades"] for f in folds)),"total_right_censored":int(sum(f["right_censored"] for f in folds))}

def _self_check():
    import inspect
    src=inspect.getsource(evaluate_fold)
    assert "due=e+hold" not in src
    assert "time_stop_bars" not in src
    assert "q[\"reason\"]!=\"TIME\"" in src
    print("V57_V433_REPLAY_SL_TP_V1_SELF_CHECK=PASS|TIME_STOP_PARAMETER=ABSENT|TIME_PNL=ABSENT|RIGHT_CENSOR=PASS")

if __name__=="__main__":
    _self_check()
