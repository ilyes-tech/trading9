from pathlib import Path
import argparse
import json
import sys
import time as _time
import numpy as np

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_strategy_dsl_v2 as dsl2
import v57_strategy_dsl_v3 as dsl3
import v57_strategy_signal_engine_v3 as engine3
import v57_logic_kernel_v1 as logic
import v57_mask_bitset_cache_v2 as bitcache

ENGINE="V57_V433_STRATEGY_SIGNAL_ENGINE_V5"
SUPPORTED_OPS={"COND","AND","OR","K_OF_N","NOT","XOR","XNOR","NAND","NOR","EXACT_K_OF_N","AT_MOST_K_OF_N","MAJORITY","SUPERMAJORITY","UNANIMOUS","EDGE_RISING","EDGE_FALLING","PERSIST_N","RECENT_WITHIN_N","THEN_WITHIN_N","THREE_STAGE_WITHIN_N"}

def _mask_shape(mask,n,label):
    a=np.asarray(mask,dtype=bool)
    if a.shape!=(int(n),):
        raise ValueError("BAD_MASK_SHAPE:"+str(label))
    return a

def _condition_key(condition):
    return dsl3.sha256_obj(condition)

def _eval_node(cache,node,sec,train_mask,market,shared_cache,context_id,thresholds):
    op=str(node.get("op",""))
    nrows=len(np.asarray(cache["time"]))
    time=np.asarray(cache["time"],dtype=np.int64)

    if op=="COND":
        condition=node["condition"]
        key=_condition_key(condition)
        mask,threshold=shared_cache.condition_mask(
            cache,condition,int(sec),train_mask,market,context_id
        )
        thresholds[key]={"condition":condition,"threshold":float(threshold)}
        return _mask_shape(mask,nrows,"COND")

    if op=="NOT":
        return _mask_shape(
            logic.boolean_not(
                _eval_node(cache,node["child"],sec,train_mask,market,shared_cache,context_id,thresholds)
            ),
            nrows,op
        )

    if op in ("EDGE_RISING","EDGE_FALLING","PERSIST_N","RECENT_WITHIN_N"):
        child=_eval_node(cache,node["child"],sec,train_mask,market,shared_cache,context_id,thresholds)
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
    masks=[
        _eval_node(cache,c,sec,train_mask,market,shared_cache,context_id,thresholds)
        for c in children
    ]
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
        out=logic.three_stage_within_n(
            masks[0],masks[1],masks[2],time,sec,node["n_ab"],node["n_bc"]
        )
    else:
        raise ValueError("UNSUPPORTED_SIGNAL_OP:"+op)
    return _mask_shape(out,nrows,op)

def strategy_signal(cache,strategy,sec,train_mask,market=None,shared_cache=None,context_id=None):
    dsl3.validate_strategy(strategy)
    n=len(np.asarray(cache["time"]))
    tm=np.asarray(train_mask,dtype=bool)
    if tm.shape!=(n,):
        raise ValueError("BAD_TRAIN_MASK_SHAPE")
    symbol=str(strategy["market"]["symbol"])
    if market is not None and str(market)!=symbol:
        raise ValueError("MARKET_MISMATCH")
    store=shared_cache if shared_cache is not None else bitcache.MaskBitsetCache()
    cid=context_id if context_id is not None else "PYOBJ:%d"%id(cache)
    node=dsl3.normalize_node(strategy["signal"])
    thresholds={}
    signal=_eval_node(cache,node,int(sec),tm,symbol,store,cid,thresholds)
    ordered=[thresholds[k] for k in sorted(thresholds)]
    return {
        "signal":_mask_shape(signal,n,"SIGNAL"),
        "condition_thresholds":ordered,
        "thresholds":[float(x["threshold"]) for x in ordered],
        "unique_conditions":len(ordered),
        "engine":ENGINE,
        "cache_engine":bitcache.ENGINE
    }

def parity_with_v3(cache,strategy_v3,sec,train_mask,market,shared_cache,context_id=None):
    old=engine3.strategy_signal(cache,strategy_v3,sec,train_mask,market)
    new=strategy_signal(
        cache,strategy_v3,sec,train_mask,market,
        shared_cache=shared_cache,context_id=context_id
    )
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
        "new_true":int(b.sum())
    }

def _ready_items(limit=None):
    ready=HERE.parents[2]/"work/autopilot_v432/shadow_ready"
    files=sorted(ready.glob("*.json"))
    if not files:
        raise RuntimeError("NO_V432_READY")
    if limit is not None:
        files=files[:int(limit)]
    return files

def parity_ready_audit(limit=None):
    import v57_fold_signal_adapter_v2 as adapter
    files=_ready_items(limit)
    contexts={}
    stores={}
    checks=0
    failures=[]
    for p in files:
        z=json.loads(p.read_text())
        c=z["candidate"]
        key=(c["market"],c["timeframe"])
        if key not in contexts:
            contexts[key]=adapter.prepare_context(*key)
            stores[key]=bitcache.MaskBitsetCache()
        ctx=contexts[key]
        store=stores[key]
        side=str(z.get("side") or c.get("side") or "LONG").upper()
        s2=dsl2.from_v1_candidate(c,side)
        s3=dsl3.from_v2_strategy(s2)
        context_id="%s|%s"%(ctx["market"],c["timeframe"])
        for i in range(len(adapter.v56.POL["folds"])):
            train,_=adapter.fold_masks(ctx,i)
            r=parity_with_v3(
                ctx["v57_cache"],s3,ctx["sec"],train,ctx["market"],
                shared_cache=store,context_id=context_id
            )
            checks+=1
            if not r["pass"]:
                failures.append((p.name,i,r["differences"],r["thresholds_equal"]))
                if len(failures)<=10:
                    print("V5_PARITY_FAIL|FILE=%s|FOLD=%d|DIFF=%d|THRESHOLDS_EQUAL=%s"%failures[-1])
    totals={"series_hits":0,"series_misses":0,"mask_hits":0,"mask_misses":0,
            "series_entries":0,"mask_entries":0,"packed_mask_bytes":0,"series_bytes":0}
    for store in stores.values():
        st=store.stats()
        for k in totals:
            totals[k]+=int(st[k])
    print("V57_V433_SIGNAL_V5_PARITY_AUDIT|READY=%d|FOLD_CHECKS=%d|FAILURES=%d"%(len(files),checks,len(failures)))
    print("V57_V433_SIGNAL_V5_CACHE|SERIES_HITS=%d|SERIES_MISSES=%d|MASK_HITS=%d|MASK_MISSES=%d|MASK_ENTRIES=%d|PACKED_BYTES=%d"%(
        totals["series_hits"],totals["series_misses"],totals["mask_hits"],totals["mask_misses"],
        totals["mask_entries"],totals["packed_mask_bytes"]))
    if failures:
        raise SystemExit(2)
    print("V57_V433_SIGNAL_V5_PARITY=PASS|V3_EXACT=PASS|FOLD_ISOLATED_CACHE=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

def benchmark_ready(limit=None,repeats=2):
    import v57_fold_signal_adapter_v2 as adapter
    files=_ready_items(limit)
    items=[]
    contexts={}
    for p in files:
        z=json.loads(p.read_text())
        c=z["candidate"]
        key=(c["market"],c["timeframe"])
        if key not in contexts:
            contexts[key]=adapter.prepare_context(*key)
        ctx=contexts[key]
        side=str(z.get("side") or c.get("side") or "LONG").upper()
        s3=dsl3.from_v2_strategy(dsl2.from_v1_candidate(c,side))
        for i in range(len(adapter.v56.POL["folds"])):
            train,_=adapter.fold_masks(ctx,i)
            items.append((key,ctx,s3,train,"%s|%s"%key))

    t0=_time.perf_counter()
    for key,ctx,s3,train,cid in items:
        engine3.strategy_signal(ctx["v57_cache"],s3,ctx["sec"],train,ctx["market"])
    v3_seconds=_time.perf_counter()-t0

    stores={}
    t0=_time.perf_counter()
    for key,ctx,s3,train,cid in items:
        store=stores.setdefault(key,bitcache.MaskBitsetCache())
        strategy_signal(ctx["v57_cache"],s3,ctx["sec"],train,ctx["market"],store,cid)
    cold_seconds=_time.perf_counter()-t0

    warm_runs=[]
    for _ in range(int(repeats)):
        t0=_time.perf_counter()
        for key,ctx,s3,train,cid in items:
            strategy_signal(ctx["v57_cache"],s3,ctx["sec"],train,ctx["market"],stores[key],cid)
        warm_runs.append(_time.perf_counter()-t0)
    warm_seconds=min(warm_runs) if warm_runs else float("nan")
    speedup=(v3_seconds/warm_seconds) if warm_seconds>0 else float("inf")
    print("V57_V433_SIGNAL_V5_BENCHMARK|CHECKS=%d|V3_SECONDS=%.6f|V5_COLD_SECONDS=%.6f|V4_WARM_SECONDS=%.6f|WARM_SPEEDUP_X=%.3f"%(
        len(items),v3_seconds,cold_seconds,warm_seconds,speedup))
    print("V57_V433_SIGNAL_V5_BENCHMARK=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")

def self_check():
    n=8
    time=np.array([0,60,120,180,600,660,720,780],dtype=np.int64)
    cache={"time":time,"A":np.array([0.,1.,2.,3.,4.,5.,6.,7.]),"B":np.array([7.,6.,5.,4.,3.,2.,1.,0.])}
    legacy=bitcache.legacy
    original=legacy.resolver.resolve_feature
    legacy.resolver.resolve_feature=lambda cache,condition,sec,market=None: np.asarray(cache[condition["feature"]],dtype=float)
    try:
        ca={"family":"test","feature":"A","transform":"LEVEL","threshold_quantile":0.5}
        cb={"family":"test","feature":"B","transform":"LEVEL","threshold_quantile":0.5}
        node=dsl3.normalize_node({
            "op":"XOR",
            "children":[{"op":"COND","condition":ca},{"op":"COND","condition":cb}]
        })
        tm=np.ones(n,dtype=bool)
        old_thresholds={}
        old=engine3._eval_node(cache,node,60,tm,"TEST",{},old_thresholds)
        store=bitcache.MaskBitsetCache()
        new_thresholds={}
        new=_eval_node(cache,node,60,tm,"TEST",store,"TEST|M1",new_thresholds)
        repeat_thresholds={}
        repeat=_eval_node(cache,node,60,tm,"TEST",store,"TEST|M1",repeat_thresholds)
        if not np.array_equal(old,new):
            raise AssertionError("V3_PARITY")
        if not np.array_equal(new,repeat):
            raise AssertionError("CACHE_REPEAT_PARITY")
        a=[old_thresholds[k]["threshold"] for k in sorted(old_thresholds)]
        b=[new_thresholds[k]["threshold"] for k in sorted(new_thresholds)]
        if not np.array_equal(np.asarray(a,dtype=float),np.asarray(b,dtype=float)):
            raise AssertionError("THRESHOLD_PARITY")
        st=store.stats()
        if st["mask_hits"]<2 or st["mask_misses"]!=2:
            raise AssertionError("WARM_CACHE_STATS:"+str(st))
    finally:
        legacy.resolver.resolve_feature=original
    print("V57_V433_STRATEGY_SIGNAL_ENGINE_V5_SELF_CHECK=PASS|OPS=%d|V3_PARITY=PASS|SHARED_CACHE=PASS|WARM_HIT=PASS|ORDERS=DISABLED"%len(SUPPORTED_OPS))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--parity-sample",type=int,default=None)
    ap.add_argument("--parity-ready",action="store_true")
    ap.add_argument("--benchmark-ready",action="store_true")
    ap.add_argument("--benchmark-sample",type=int,default=None)
    ap.add_argument("--repeats",type=int,default=2)
    args=ap.parse_args()
    if args.parity_ready:
        parity_ready_audit(None)
    elif args.parity_sample is not None:
        parity_ready_audit(args.parity_sample)
    elif args.benchmark_ready:
        benchmark_ready(None,args.repeats)
    elif args.benchmark_sample is not None:
        benchmark_ready(args.benchmark_sample,args.repeats)
    else:
        self_check()

if __name__=="__main__":
    main()
