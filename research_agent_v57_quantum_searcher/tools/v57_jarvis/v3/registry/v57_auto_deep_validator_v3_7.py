import hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
SRC=ROOT/"src"
for p in (SRC,SRC/"v435",Path(__file__).parent):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_constrained_generator_v3_2 as G
import v57_search_replay_v435_v1 as R
BOOT_N=1000
MIN_MEAN=.90
MIN_PF=.80
MIN_HALVES=4
MAX_TRADE=.35
MAX_DAY=.50
CUTOFF=1782864000
def pf(a):
    a=np.asarray(a,dtype=float); w=float(a[a>0].sum()); l=float(-a[a<0].sum())
    return 999999.0 if w>0 and l==0 else float(w/l) if l>0 else 0.0
def collect(ctx,s,fi,store):
    train,valid=R.adapter2.fold_masks(ctx,fi)
    sig=R.signal5.strategy_signal(ctx["v57_cache"],s,ctx["sec"],train,ctx["market"],store,ctx["market"]+"|"+ctx["timeframe"]+"|SEARCH_REPLAY_V435_V1")
    signals=np.flatnonzero(np.asarray(sig["signal"],dtype=bool)&valid)
    z=dict(ctx); z["spread"]=R.v56.fold_spread(ctx,fi)
    risk=R._risk(s,z["timeframe"]); atr=R._risk_atr(z["v57_cache"],z["sec"],risk["atr_window"])
    hold=int(risk["time_stop_bars"]); pre=[]
    side=s["market"]["side"]
    for x in signals:
        e=int(x)+1; due=e+hold
        if due>=len(z["tf_time"]) or not valid[e] or not valid[due]: continue
        a=int(z["tf_to_m1"][x]); b=int(z["tf_to_m1"][e])
        if b<=a or np.any(z["unexpected"][a:b]): continue
        em=int(z["tf_to_m1"][e]); dm=int(z["tf_to_m1"][due])
        lv=R._risk_levels(z,risk,int(x),em,side,atr)
        if lv is None: continue
        q=R.v56.base.replay.replay_trade(z["market"],side,z["m1_time"],z["m1_open"],z["m1_high"],z["m1_low"],z["m1_close"],z["spread"],em,dm,float(lv["stop"]),float(lv["target"]),z["scheduled"])
        if q.get("eligible",False):
            q=R.v56.base.replay.apply_costs(z["asset_class"],q); pre.append(q)
    out=[]
    for q in R.v56.select_nonoverlap(pre): out.append({"entry_time":int(z["m1_time"][q["entry_i"]]),"stress":float(q["stress_net_bps"])})
    return out
def boot(t,seed):
    by={}
    for q in t: by.setdefault(q["entry_time"]//86400,[]).append(q["stress"])
    g=[np.asarray(by[k],float) for k in sorted(by)]
    if len(g)<2:return 0.,0.
    rng=np.random.default_rng(seed); m=[]; p=[]
    for _ in range(BOOT_N):
        a=np.concatenate([g[int(i)] for i in rng.integers(0,len(g),size=len(g))]); m.append(float(a.mean())); p.append(pf(a))
    return float(np.mean(np.asarray(m)>0)),float(np.mean(np.asarray(p)>=1))
def validate(spec,seed,index,expected_sid):
    s=G.generate(spec,1,seed,index)[0][0]
    if s["strategy_id"]!=expected_sid: raise RuntimeError("SID_MISMATCH")
    ctx=R.adapter2.prepare_context(s["market"]["symbol"],s["market"]["timeframe"])
    if len(ctx["tf_time"])==0 or int(np.max(ctx["tf_time"]))>=CUTOFF: raise RuntimeError("DATA_CUTOFF_FAIL")
    store=R.signal5.bitcache.MaskBitsetCache(); q=R.evaluate_strategy(ctx,s,store)
    if not q.get("exact_pass"): return {"status":"DEEP_REJECT","reason":"REPLAY_NOT_EXACT_PASS","strategy_id":expected_sid}
    pm=[]; pp=[]; halves=0; mt=0.; md=0.
    seed0=int(expected_sid[:16],16)%(2**32)
    for fi in range(3):
        t=collect(ctx,s,fi,store)
        if len(t)!=int(q["folds"][fi]["selected_trades"]): raise RuntimeError("TRADE_COUNT_MISMATCH_FOLD_"+str(fi))
        a=np.asarray([x["stress"] for x in t],float); pos=a[a>0]; total=float(pos.sum()); mt=max(mt,1. if total<=0 else float(pos.max()/total))
        days={}
        for x in t: days[x["entry_time"]//86400]=days.get(x["entry_time"]//86400,0.)+x["stress"]
        dp=np.asarray([x for x in days.values() if x>0],float); dt=float(dp.sum()); md=max(md,1. if dt<=0 else float(dp.max()/dt))
        ts=np.asarray([x["entry_time"] for x in t],np.int64); mid=(int(ts.min())+int(ts.max()))//2
        for h in ([x["stress"] for x in t if x["entry_time"]<=mid],[x["stress"] for x in t if x["entry_time"]>mid]):
            if len(h)>=10 and float(np.mean(h))>0: halves+=1
        x,y=boot(t,seed0+fi); pm.append(x); pp.append(y)
    ok=min(pm)>=MIN_MEAN and min(pp)>=MIN_PF and halves>=MIN_HALVES and mt<=MAX_TRADE and md<=MAX_DAY
    return {"status":"DEEP_PASS" if ok else "DEEP_REJECT","strategy_id":expected_sid,"exact_pass":True,"trades":q["aggregate"]["total_selected_trades"],"min_boot_mean":min(pm),"min_boot_pf":min(pp),"positive_halves":halves,"max_trade_share":mt,"max_day_share":md}
if __name__=="__main__":
    spec={"market":"XAUUSD","timeframe":"M15","side":"SHORT","families":["momentum","trend"]}
    sid="51f8f8bd3ec55d84805f0ca01d7695afd93075f4127ed77a03458a1a39ef1e60"
    try:
        x=validate(spec,574352,27,sid); print("ALL PASS|"+str(x) if x["status"]=="DEEP_PASS" else "STOP|"+str(x))
    except Exception as e: print("STOP|FAIL|"+type(e).__name__+"|"+str(e)); raise SystemExit(1)
