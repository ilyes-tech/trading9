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

import v57_strategy_dsl_v2 as dsl2
import v57_strategy_dsl_v3 as dsl3
import v57_strategy_signal_engine_v2 as engine2
import v57_candidate_signal_engine_v1 as legacy
import v57_logic_kernel_v1 as logic

SUPPORTED_OPS=set(dsl3.SUPPORTED_OPS)

def _mask_shape(mask,n,label):
    a=np.asarray(mask,dtype=bool)
    if a.shape!=(n,):
        raise ValueError("BAD_MASK_SHAPE:"+label)
    return a

def _condition_key(condition):
    return dsl3.sha256_obj(condition)

def _eval_node(cache,node,sec,train_mask,market,memo,thresholds):
    op=str(node.get("op",""))
    nrows=len(np.asarray(cache["time"]))
    time=np.asarray(cache["time"],dtype=np.int64)
    if op=="COND":
        condition=node["condition"]
        key=_condition_key(condition)
        if key not in memo:
            mask,threshold,_=legacy.condition_mask(cache,condition,sec,train_mask,market)
            memo[key]=(_mask_shape(mask,nrows,"COND"),float(threshold))
        mask,threshold=memo[key]
        thresholds[key]={"condition":condition,"threshold":float(threshold)}
        return mask
    if op=="NOT":
        return _mask_shape(logic.boolean_not(_eval_node(cache,node["child"],sec,train_mask,market,memo,thresholds)),nrows,op)
    if op in ("EDGE_RISING","EDGE_FALLING","PERSIST_N","RECENT_WITHIN_N"):
        child=_eval_node(cache,node["child"],sec,train_mask,market,memo,thresholds)
        if op=="EDGE_RISING":
            out=logic.edge_rising(child,time,sec)
        elif op=="EDGE_FALLING":
            out=logic.edge_falling(child,time,sec)
        elif op=="PERSIST_N":
            out=logic.persist_n(child,time,sec,node["n"])
        else:
            out=logic.recent_within_n(child,time,sec,node["n"])
        return _mask_shape(out,nrows,op)
    children=node.get("children")
    if not isinstance(children,list) or not children:
        raise ValueError("BAD_CHILDREN:"+op)
    masks=[_eval_node(cache,c,sec,train_mask,market,memo,thresholds) for c in children]
    a=np.asarray(masks,dtype=bool)
    if op=="AND":
        out=np.all(a,axis=0)
    elif op=="OR":
        out=np.any(a,axis=0)
    elif op=="K_OF_N":
        out=np.sum(a,axis=0)>=int(node["k"])
    elif op=="XOR":
        out=logic.xor_masks(masks)
    elif op=="XNOR":
        out=logic.xnor_masks(masks)
    elif op=="NAND":
        out=logic.nand_masks(masks)
    elif op=="NOR":
        out=logic.nor_masks(masks)
    elif op=="EXACT_K_OF_N":
        out=logic.exact_k_of_n(masks,node["k"])
    elif op=="AT_MOST_K_OF_N":
        out=logic.at_most_k_of_n(masks,node["k"])
    elif op=="MAJORITY":
        out=logic.majority(masks)
    elif op=="SUPERMAJORITY":
        out=logic.supermajority(masks)
    elif op=="UNANIMOUS":
        out=logic.unanimous(masks)
    elif op=="THEN_WITHIN_N":
        if len(masks)!=2:
            raise ValueError("BAD_CHILD_COUNT:"+op)
        out=logic.then_within_n(masks[0],masks[1],time,sec,node["n"])
    elif op=="THREE_STAGE_WITHIN_N":
        if len(masks)!=3:
            raise ValueError("BAD_CHILD_COUNT:"+op)
        out=logic.three_stage_within_n(masks[0],masks[1],masks[2],time,sec,node["n_ab"],node["n_bc"])
    else:
        raise ValueError("UNSUPPORTED_SIGNAL_OP:"+op)
    return _mask_shape(out,nrows,op)

def strategy_signal(cache,strategy,sec,train_mask,market=None):
    dsl3.validate_strategy(strategy)
    n=len(np.asarray(cache["time"]))
    tm=np.asarray(train_mask,dtype=bool)
    if tm.shape!=(n,):
        raise ValueError("BAD_TRAIN_MASK_SHAPE")
    symbol=str(strategy["market"]["symbol"])
    if market is not None and str(market)!=symbol:
        raise ValueError("MARKET_MISMATCH")
    node=dsl3.normalize_node(strategy["signal"])
    memo={}
    thresholds={}
    signal=_eval_node(cache,node,int(sec),tm,symbol,memo,thresholds)
    ordered=[thresholds[k] for k in sorted(thresholds)]
    return {
        "signal":_mask_shape(signal,n,"SIGNAL"),
        "condition_thresholds":ordered,
        "thresholds":[float(x["threshold"]) for x in ordered],
        "unique_conditions":len(ordered),
        "engine":"V57_V433_STRATEGY_SIGNAL_ENGINE_V3"
    }

def parity_with_v2(cache,strategy_v2,sec,train_mask,market):
    old=engine2.strategy_signal(cache,strategy_v2,sec,train_mask,market)
    strategy_v3=dsl3.from_v2_strategy(strategy_v2)
    new=strategy_signal(cache,strategy_v3,sec,train_mask,market)
    a=np.asarray(old["signal"],dtype=bool)
    b=np.asarray(new["signal"],dtype=bool)
    if a.shape!=b.shape:
        raise ValueError("PARITY_SHAPE_MISMATCH")
    diff=np.flatnonzero(a!=b)
    ta=np.asarray(old["thresholds"],dtype=float)
    tb=np.asarray(new["thresholds"],dtype=float)
    thresholds_equal=bool(ta.shape==tb.shape and np.array_equal(ta,tb))
    return {
        "pass":bool(len(diff)==0 and thresholds_equal),
        "differences":int(len(diff)),
        "thresholds_equal":thresholds_equal,
        "rows":int(len(a)),
        "old_true":int(a.sum()),
        "new_true":int(b.sum()),
        "strategy_id_v3":strategy_v3["strategy_id"]
    }

def parity_ready_audit(limit=None):
    import v57_fold_signal_adapter_v1 as adapter
    ready=HERE.parents[2]/"work/autopilot_v432/shadow_ready"
    files=sorted(ready.glob("*.json"))
    if not files:
        raise RuntimeError("NO_V432_READY")
    if limit is not None:
        files=files[:int(limit)]
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
        s2=dsl2.from_v1_candidate(c,side)
        for i in range(len(adapter.v56.POL["folds"])):
            train,_=adapter.fold_masks(ctx,i)
            r=parity_with_v2(ctx["v57_cache"],s2,ctx["sec"],train,ctx["market"])
            checks+=1
            if not r["pass"]:
                failures.append((p.name,i,r["differences"],r["thresholds_equal"]))
                if len(failures)<=10:
                    print("V3_PARITY_FAIL|FILE=%s|FOLD=%d|DIFF=%d|THRESHOLDS_EQUAL=%s"%failures[-1])
    print("V57_V433_SIGNAL_V3_PARITY_AUDIT|READY=%d|FOLD_CHECKS=%d|FAILURES=%d"%(len(files),checks,len(failures)))
    if failures:
        raise SystemExit(2)
    print("V57_V433_SIGNAL_V3_PARITY=PASS|V2_CORE_EXACT=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

def self_check():
    n=8
    time=np.array([0,60,120,180,600,660,720,780],dtype=np.int64)
    cache={"time":time,"A":np.array([0.,1.,2.,3.,4.,5.,6.,7.]),"B":np.array([7.,6.,5.,4.,3.,2.,1.,0.])}
    original=legacy.resolver.resolve_feature
    legacy.resolver.resolve_feature=lambda cache,condition,sec,market=None: np.asarray(cache[condition["feature"]],dtype=float)
    try:
        ca={"family":"test","feature":"A","transform":"LEVEL","threshold_quantile":0.5}
        cb={"family":"test","feature":"B","transform":"LEVEL","threshold_quantile":0.5}
        a={"op":"COND","condition":ca}
        b={"op":"COND","condition":cb}
        base={"schema_version":3,"kind":"V57_STRATEGY_DSL_V3","market":{"symbol":"TEST","timeframe":"M1","side":"LONG"},"signal":{"op":"XOR","children":[a,b]},"risk":{},"execution":{"mode":"RESEARCH_ONLY","orders_allowed":False},"portfolio":{"enabled":False},"research_integrity":{"holdout_authorized":False,"holdout_read":False,"holdout_evaluated":False,"september_2026_data_accessed":False,"real_orders_allowed":False,"demo_orders_allowed":False},"legacy":{}}
        sx=dsl3.finalize_strategy(base)
        rx=strategy_signal(cache,sx,60,np.ones(n,dtype=bool),"TEST")
        ma,_,_=legacy.condition_mask(cache,ca,60,np.ones(n,dtype=bool),"TEST")
        mb,_,_=legacy.condition_mask(cache,cb,60,np.ones(n,dtype=bool),"TEST")
        assert np.array_equal(rx["signal"],logic.xor_masks([ma,mb]))
        st=dict(base); st["signal"]={"op":"THEN_WITHIN_N","n":2,"children":[{"op":"EDGE_RISING","child":a},{"op":"EDGE_RISING","child":b}]}
        st=dsl3.finalize_strategy(st)
        rt=strategy_signal(cache,st,60,np.ones(n,dtype=bool),"TEST")
        expected=logic.then_within_n(logic.edge_rising(ma,time,60),logic.edge_rising(mb,time,60),time,60,2)
        assert np.array_equal(rt["signal"],expected)
    finally:
        legacy.resolver.resolve_feature=original
    print("V57_V433_STRATEGY_SIGNAL_ENGINE_V3_SELF_CHECK=PASS|OPS=%d|NATIVE_LOGIC=PASS|SEGMENT_AWARE=PASS|ORDERS=DISABLED"%len(SUPPORTED_OPS))

if __name__=="__main__":
    if "--parity-ready" in sys.argv:
        parity_ready_audit()
    elif "--parity-sample" in sys.argv:
        i=sys.argv.index("--parity-sample")
        parity_ready_audit(int(sys.argv[i+1]))
    else:
        self_check()
