#!/usr/bin/env python3
import argparse,datetime,hashlib,json,os,sys,time
from pathlib import Path

for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[k]="1"

import numpy as np

REPO=Path.home()/"TradingAI-HF-Lab"
R=REPO/"research_agent_v57_quantum_searcher"
SRC=R/"src"
if str(SRC) not in sys.path:
    sys.path.insert(0,str(SRC))

import v57_replay_evaluator_v1 as r1
import v57_replay_evaluator_v2 as r2
import v57_fold_signal_adapter_v1 as adapter
import v57_screening_runner_v2 as screen

READY=R/"work/autopilot_v432/shadow_ready"
OUT=R/"work/deep_validation_v45"
RESULTS=OUT/"results"
STATUS=OUT/"status.json"
LEADER=OUT/"leaderboard.json"
CUTOFF=1782864000
METRICS=("total_selected_trades","worst_base_avg_bps","min_base_pf","worst_stress_avg_bps","min_stress_pf")
BOOT_N=1000
MIN_BOOT_MEAN_PROB=0.90
MIN_BOOT_PF_PROB=0.80
MIN_POSITIVE_HALVES=4
MAX_TRADE_PROFIT_SHARE=0.35
MAX_DAY_PROFIT_SHARE=0.50

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def H(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p,d=None):
    p=Path(p)
    return json.loads(p.read_text()) if p.exists() else d

def save(p,x):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    t=Path(str(p)+".tmp")
    t.write_text(json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+"\n")
    os.replace(t,p)

def pf(x):
    a=np.asarray(x,dtype=float)
    w=float(a[a>0].sum()); l=float(-a[a<0].sum())
    if w>0 and l==0: return 999999.0
    return float(w/l) if l>0 else 0.0

def collect_fold(ctx,c,fi,side):
    train,valid=adapter.fold_masks(ctx,fi)
    sig=adapter.signal_engine.candidate_signal(ctx["v57_cache"],c,ctx["sec"],train,ctx["market"])
    signals=np.flatnonzero(np.asarray(sig["signal"],dtype=bool)&valid)
    z=dict(ctx); z["spread"]=r1.v56.fold_spread(ctx,fi)
    atr=r1._risk_atr(z["v57_cache"],z["sec"],c["risk_model"]["atr_window"])
    hold=int(c["risk_model"]["time_stop_bars"]); pre=[]
    for s in signals:
        e=int(s)+1; due=e+hold
        if due>=len(z["tf_time"]) or not valid[e] or not valid[due]: continue
        a=int(z["tf_to_m1"][s]); b=int(z["tf_to_m1"][e])
        if b<=a or np.any(z["unexpected"][a:b]): continue
        em=int(z["tf_to_m1"][e]); dm=int(z["tf_to_m1"][due])
        lv=r1._risk_levels(z,c,int(s),em,side,atr)
        if lv is None: continue
        q=r1.v56.base.replay.replay_trade(z["market"],side,z["m1_time"],z["m1_open"],z["m1_high"],z["m1_low"],z["m1_close"],z["spread"],em,dm,float(lv["stop"]),float(lv["target"]),z["scheduled"])
        if q.get("eligible",False):
            q=r1.v56.base.replay.apply_costs(z["asset_class"],q)
            q["signal_tf_i"]=int(s); pre.append(q)
    sel=r1.v56.select_nonoverlap(pre)
    out=[]
    for q in sel:
        out.append({"entry_time":int(z["m1_time"][q["entry_i"]]),"exit_time":int(z["m1_time"][q["exit_i"]]),"reason":str(q["reason"]),"base":float(q["base_net_bps"]),"stress":float(q["stress_net_bps"])})
    return out

def bootstrap_days(trades,seed):
    by={}
    for q in trades:
        day=int(q["entry_time"])//86400
        by.setdefault(day,[]).append(float(q["stress"]))
    groups=[np.asarray(by[k],dtype=float) for k in sorted(by)]
    if len(groups)<2:
        return {"days":len(groups),"p_mean_gt0":0.0,"p_pf_ge1":0.0,"mean_p05":-999.0,"pf_p05":0.0}
    rng=np.random.default_rng(seed); means=[]; pfs=[]
    n=len(groups)
    for _ in range(BOOT_N):
        ids=rng.integers(0,n,size=n)
        a=np.concatenate([groups[int(i)] for i in ids])
        means.append(float(a.mean()) if len(a) else -999.0)
        pfs.append(pf(a))
    return {"days":n,"p_mean_gt0":float(np.mean(np.asarray(means)>0)),"p_pf_ge1":float(np.mean(np.asarray(pfs)>=1.0)),"mean_p05":float(np.quantile(means,0.05)),"pf_p05":float(np.quantile(pfs,0.05))}

def concentration(trades):
    a=np.asarray([q["stress"] for q in trades],dtype=float)
    if len(a)==0: return {"max_trade_profit_share":1.0,"max_day_profit_share":1.0}
    pos=a[a>0]; total=float(pos.sum())
    mt=1.0 if total<=0 else float(pos.max()/total)
    d={}
    for q in trades: d[int(q["entry_time"])//86400]=d.get(int(q["entry_time"])//86400,0.0)+float(q["stress"])
    dp=np.asarray([x for x in d.values() if x>0],dtype=float); dt=float(dp.sum())
    md=1.0 if dt<=0 else float(dp.max()/dt)
    return {"max_trade_profit_share":mt,"max_day_profit_share":md}

def half_stats(trades):
    if not trades: return []
    ts=np.asarray([q["entry_time"] for q in trades],dtype=np.int64)
    mid=int((int(ts.min())+int(ts.max()))//2)
    out=[]
    for name,rows in (("H1",[q for q in trades if q["entry_time"]<=mid]),("H2",[q for q in trades if q["entry_time"]>mid])):
        a=np.asarray([q["stress"] for q in rows],dtype=float)
        out.append({"half":name,"trades":int(len(a)),"stress_avg_bps":None if len(a)==0 else float(a.mean()),"stress_pf":pf(a)})
    return out

def validate_dsl3(strategy,ctx,replay_result):
    sid=strategy["strategy_id"]
    if not replay_result.get("exact_pass"): return {"status":"DEEP_REJECT","strategy_id":sid,"reason":"NOT_EXACT_PASS"}
    folds=[]; positive_halves=0; max_trade=0.0; max_day=0.0; pmean=[]; ppf=[]
    seed0=int(sid[:16],16)%(2**32)
    for fi in range(3):
        rf=replay_result["folds"][fi]; raw=rf["selected_trade_records"]
        if len(raw)!=int(rf["selected_trades"]): raise RuntimeError("TRADE_COUNT_MISMATCH_FOLD_"+str(fi))
        tr=[{"entry_time":int(ctx["m1_time"][int(q["entry_i"])]),"stress":float(q["stress_net_bps"])} for q in raw]
        bs=bootstrap_days(tr,seed0+fi); co=concentration(tr); hs=half_stats(tr)
        positive_halves+=sum(1 for x in hs if x["trades"]>=10 and x["stress_avg_bps"] is not None and x["stress_avg_bps"]>0)
        max_trade=max(max_trade,co["max_trade_profit_share"]); max_day=max(max_day,co["max_day_profit_share"]); pmean.append(bs["p_mean_gt0"]); ppf.append(bs["p_pf_ge1"])
        folds.append({"fold_index":fi,"trades":len(tr),"bootstrap":bs,"concentration":co,"halves":hs})
    deep_pass=bool(min(pmean)>=MIN_BOOT_MEAN_PROB and min(ppf)>=MIN_BOOT_PF_PROB and positive_halves>=MIN_POSITIVE_HALVES and max_trade<=MAX_TRADE_PROFIT_SHARE and max_day<=MAX_DAY_PROFIT_SHARE)
    return {"schema_version":1,"kind":"V57_JARVIS_DSL3_DEEP_VALIDATION_V3_8","status":"DEEP_PASS" if deep_pass else "DEEP_REJECT","strategy_id":sid,"replay":{"exact_pass":True,"total_selected_trades":replay_result["total_selected_trades"],"worst_stress_avg_bps":replay_result["worst_stress_avg_bps"],"min_stress_pf":replay_result["min_stress_pf"]},"deep":{"bootstrap_draws":BOOT_N,"min_boot_mean_positive_probability":float(min(pmean)),"min_boot_pf_ge1_probability":float(min(ppf)),"positive_half_segments":int(positive_halves),"max_trade_profit_share":float(max_trade),"max_day_profit_share":float(max_day),"folds":folds},"orders_allowed":False,"demo_orders_allowed":False,"real_orders_allowed":False,"research_integrity":{"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False}}

def rebuild_leaderboard():
    rows=[]
    for p in RESULTS.glob("*.json"):
        x=load(p,{})
        if x.get("kind")=="V57_DEEP_VALIDATION_V45":
            rows.append(x)
    rows.sort(key=lambda x:(x.get("status")=="DEEP_PASS",float(x.get("deep",{}).get("min_boot_mean_positive_probability",-1)),float(x.get("deep",{}).get("min_boot_pf_ge1_probability",-1)),float(x.get("replay",{}).get("worst_stress_avg_bps",-999)),float(x.get("replay",{}).get("min_stress_pf",-999)),float(x.get("robustness",{}).get("exact_fraction_valid",-1))),reverse=True)
    out=[]
    for i,x in enumerate(rows,1):
        out.append({"rank":i,"status":x["status"],"variant_id":x["variant_id"],"market":x["market"],"side":x["side"],"timeframe":x["timeframe"],"min_boot_mean_prob":x["deep"]["min_boot_mean_positive_probability"],"min_boot_pf_prob":x["deep"]["min_boot_pf_ge1_probability"],"positive_halves":x["deep"]["positive_half_segments"],"worst_stress_avg_bps":x["replay"]["worst_stress_avg_bps"],"min_stress_pf":x["replay"]["min_stress_pf"],"robust_exact_fraction":x.get("robustness",{}).get("exact_fraction_valid")})
    save(LEADER,{"schema_version":1,"kind":"V57_DEEP_VALIDATION_LEADERBOARD_V45","updated_at_utc":now(),"total":len(out),"passed":sum(1 for x in out if x["status"]=="DEEP_PASS"),"rows":out})
    return out

def cycle():
    RESULTS.mkdir(parents=True,exist_ok=True)
    done=0; errors=0
    for p in sorted(READY.glob("READY_*.json")):
        vid=load(p,{}).get("variant_id")
        if not vid: continue
        out=RESULTS/(vid+".json")
        if out.exists(): continue
        try:
            save(out,validate_bundle(p)); done+=1
        except Exception as e:
            save(out,{"schema_version":1,"kind":"V57_DEEP_VALIDATION_V45_ERROR","created_at_utc":now(),"status":"ERROR","variant_id":vid,"source_bundle":str(p.relative_to(REPO)),"error":type(e).__name__+":"+str(e),"orders_allowed":False,"real_orders_allowed":False}); errors+=1
    rows=rebuild_leaderboard()
    st={"updated_at_utc":now(),"ready_seen":len(list(READY.glob("READY_*.json"))),"validated":len(rows),"passed":sum(1 for x in rows if x["status"]=="DEEP_PASS"),"new_this_cycle":done,"errors_this_cycle":errors,"mode":"ENGINEERING_ONLY_NO_HOLDOUT_NO_ORDERS"}
    save(STATUS,st)
    return st,rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--self-check",action="store_true"); ap.add_argument("--once",action="store_true"); a=ap.parse_args()
    if a.self_check:
        print("V45_SELF_CHECK=PASS|READY="+str(READY)+"|OUT="+str(OUT)+"|HOLDOUT=BLOCKED|SEPTEMBER=BLOCKED|ORDERS=BLOCKED"); return
    while True:
        st,rows=cycle()
        print("V45|VALIDATED="+str(st["validated"])+"|PASS="+str(st["passed"])+"|NEW="+str(st["new_this_cycle"])+"|ERRORS="+str(st["errors_this_cycle"]),flush=True)
        if a.once: return
        time.sleep(60)

if __name__=="__main__":
    main()
