from pathlib import Path
import json
import sys
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_strategy_dsl_v2 as dsl
import v57_candidate_signal_engine_v1 as legacy

SUPPORTED_OPS={"COND","AND","OR","K_OF_N"}

def _mask_shape(mask,n,label):
    a=np.asarray(mask,dtype=bool)
    if a.shape!=(n,):
        raise ValueError("BAD_MASK_SHAPE:"+label)
    return a

def _condition_key(condition):
    return dsl.sha256_obj(condition)

def _eval_node(cache,node,sec,train_mask,market,memo,thresholds):
    op=str(node.get("op",""))
    n=len(np.asarray(cache["time"]))
    if op=="COND":
        condition=node["condition"]
        key=_condition_key(condition)
        if key not in memo:
            mask,threshold,_=legacy.condition_mask(cache,condition,sec,train_mask,market)
            memo[key]=(_mask_shape(mask,n,"COND"),float(threshold))
        mask,threshold=memo[key]
        thresholds[key]={"condition":condition,"threshold":float(threshold)}
        return mask
    children=node.get("children")
    if not isinstance(children,list) or not children:
        raise ValueError("BAD_CHILDREN:"+op)
    masks=[_eval_node(cache,c,sec,train_mask,market,memo,thresholds) for c in children]
    a=np.asarray(masks,dtype=bool)
    if op=="AND":
        return np.all(a,axis=0)
    if op=="OR":
        return np.any(a,axis=0)
    if op=="K_OF_N":
        k=int(node["k"])
        return np.sum(a,axis=0)>=k
    raise ValueError("UNSUPPORTED_SIGNAL_OP:"+op)

def strategy_signal(cache,strategy,sec,train_mask,market=None):
    dsl.validate_strategy(strategy)
    n=len(np.asarray(cache["time"]))
    tm=np.asarray(train_mask,dtype=bool)
    if tm.shape!=(n,):
        raise ValueError("BAD_TRAIN_MASK_SHAPE")
    sm=strategy["market"]
    symbol=str(sm["symbol"])
    if market is not None and str(market)!=symbol:
        raise ValueError("MARKET_MISMATCH")
    signal_node=dsl.normalize_node(strategy["signal"])
    memo={}
    thresholds={}
    signal=_eval_node(cache,signal_node,int(sec),tm,symbol,memo,thresholds)
    ordered=[thresholds[k] for k in sorted(thresholds)]
    return {
        "signal":_mask_shape(signal,n,"SIGNAL"),
        "condition_thresholds":ordered,
        "thresholds":[float(x["threshold"]) for x in ordered],
        "unique_conditions":len(ordered),
        "engine":"V57_V433_STRATEGY_SIGNAL_ENGINE_V2"
    }

def parity_with_v1(cache,candidate,sec,train_mask,market,side):
    strategy=dsl.from_v1_candidate(candidate,side)
    old=legacy.candidate_signal(cache,candidate,sec,train_mask,market)
    new=strategy_signal(cache,strategy,sec,train_mask,market)
    a=np.asarray(old["signal"],dtype=bool)
    b=np.asarray(new["signal"],dtype=bool)
    if a.shape!=b.shape:
        raise ValueError("PARITY_SHAPE_MISMATCH")
    diff=np.flatnonzero(a!=b)
    return {
        "pass":bool(len(diff)==0),
        "differences":int(len(diff)),
        "rows":int(len(a)),
        "old_true":int(a.sum()),
        "new_true":int(b.sum()),
        "strategy_id":strategy["strategy_id"]
    }

def parity_ready_audit():
    import v57_fold_signal_adapter_v1 as adapter
    ready=HERE.parents[2]/"work/autopilot_v432/shadow_ready"
    files=sorted(ready.glob("*.json"))
    if not files:
        raise RuntimeError("NO_V432_READY")
    contexts={}
    checks=0
    failures=[]
    for p in files:
        z=json.loads(p.read_text())
        c=z["candidate"]
        key=(c["market"],c["timeframe"])
        if key not in contexts:
            contexts[key]=adapter.prepare_context(*key)
        ctx=contexts[key]
        side=str(z.get("side") or c.get("side") or "LONG").upper()
        for i in range(len(adapter.v56.POL["folds"])):
            train,_=adapter.fold_masks(ctx,i)
            r=parity_with_v1(ctx["v57_cache"],c,ctx["sec"],train,ctx["market"],side)
            checks+=1
            if not r["pass"]:
                failures.append((p.name,i,r["differences"]))
                if len(failures)<=10:
                    print("PARITY_FAIL|FILE=%s|FOLD=%d|DIFF=%d"%failures[-1])
    print("V57_V433_V1_PARITY_AUDIT|READY=%d|CHECKS=%d|FAILURES=%d"%(len(files),checks,len(failures)))
    if failures:
        raise SystemExit(2)
    print("V57_V433_V1_PARITY=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

def self_check():
    n=8
    a=np.array([0.,1.,2.,3.,4.,5.,6.,7.])
    cache={"time":np.arange(n,dtype=np.int64)*60,"X":a}
    c={"family":"test","feature":"X","transform":"LEVEL","threshold_quantile":0.5}
    original=legacy.resolver.resolve_feature
    legacy.resolver.resolve_feature=lambda cache,condition,sec,market=None: np.asarray(cache[condition["feature"]],dtype=float)
    try:
        node={"op":"COND","condition":c}
        s={"schema_version":2,"kind":"V57_STRATEGY_DSL_V2","market":{"symbol":"TEST","timeframe":"M1","side":"LONG"},"signal":node,"risk":{},"execution":{"mode":"RESEARCH_ONLY","orders_allowed":False},"portfolio":{"enabled":False},"research_integrity":{"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"real_orders_allowed":False,"demo_orders_allowed":False},"legacy":{}}
        s=dsl.finalize_strategy(s)
        r=strategy_signal(cache,s,60,np.ones(n,dtype=bool),"TEST")
        assert r["signal"].shape==(n,)
        assert r["unique_conditions"]==1
        aa={"op":"COND","condition":dict(c,threshold_quantile=0.25)}
        bb={"op":"COND","condition":dict(c,threshold_quantile=0.75)}
        s2=dict(s); s2.pop("strategy_id",None); s2["signal"]={"op":"K_OF_N","k":1,"children":[aa,bb]}; s2=dsl.finalize_strategy(s2)
        r2=strategy_signal(cache,s2,60,np.ones(n,dtype=bool),"TEST")
        assert r2["signal"].shape==(n,)
    finally:
        legacy.resolver.resolve_feature=original
    print("V57_V433_STRATEGY_SIGNAL_ENGINE_V2_SELF_CHECK=PASS|OPS=4|ORDERS=DISABLED")

if __name__=="__main__":
    if "--parity-ready" in sys.argv:
        parity_ready_audit()
    else:
        self_check()
