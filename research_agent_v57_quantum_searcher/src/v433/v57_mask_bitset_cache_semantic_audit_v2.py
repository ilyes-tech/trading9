from pathlib import Path
import hashlib,sys,numpy as np
HERE=Path(__file__).resolve(); V433=HERE.parent; SRC=HERE.parents[1]; ROOT=SRC.parent
V56=(Path("research_agent_v56_strategy_factory")/"src").resolve()
for p in (V433,SRC,V56):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_mask_bitset_cache_v2 as m2
import v57_feature_resolver_v2 as r2
import v57_transform_engine_v1 as tr
import v56_fold_evaluator_v3 as v56
MASK_SHA="267099b5275008a0e3a8298f96ef2767d64a46aa61eb1b5258ca340cb4e6320e"
FREEZE_SHA="96586473fd36baee26aa41248ef7ec8a6a38c41513b578d52854dbd13383ad70"
MAN_SHA="b2273621beb98e6204dec42c450b78c9f5047417b71347738462394330998b4b"
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(V433/"v57_mask_bitset_cache_v2.py")==MASK_SHA
assert H(ROOT/"config/v433/V57_V433_FEATURE_CACHE_RESOLVER_FREEZE_V1.json")==FREEZE_SHA
assert H(ROOT/"config/v433/V57_V433_FEATURE_CACHE_V2_MANIFEST_V2.json")==MAN_SHA
assert len(v56.POL["folds"])==3
MS=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
TFS={"M5":300,"M15":900,"M30":1800,"H1":3600}
FEATURES=[
("momentum","STOCHASTIC",{"window":14}),("momentum","ROC",{"window":10}),("momentum","CCI",{"window":20}),
("momentum","WILLIAMS_R",{"window":14}),("momentum","ULTIMATE_OSCILLATOR",{"parameter_set":[7,14,28]}),
("momentum","FISHER_TRANSFORM",{"window":10}),("trend","SMA",{"window":20}),("trend","EMA",{"window":20}),
("trend","ADX",{"window":14}),("trend","PLUS_DI",{"window":14}),("trend","MINUS_DI",{"window":14}),
("volatility","ATR",{"window":14}),("volatility","NATR",{"window":14}),("volume","CMF",{"window":20}),
("volume","MFI",{"window":14}),("volume","VWAP_DISTANCE",{}),("time","weekday_sin",{}),("time","weekday_cos",{})]
TRANS=("LEVEL","DELTA","PCT_CHANGE","MEAN","STD","ZSCORE","MIN","MAX","SLOPE","RANK","CROSS_UP","CROSS_DOWN","ABOVE","BELOW")
def same(a,b):
    a=np.asarray(a); b=np.asarray(b)
    return a.shape==b.shape and np.array_equal(a,b,equal_nan=True)
def train_threshold(series,tm,q):
    x=np.asarray(series,float); g=np.asarray(tm,bool)&np.isfinite(x)
    if not np.any(g): return None
    return float(np.quantile(x[g],float(q)))
def mask_oracle(series,time,sec,th,q,kind):
    x=np.asarray(series,float); t=np.asarray(time,np.int64); finite=np.isfinite(x)
    if kind=="ABOVE": return finite&(x>th)
    if kind=="BELOW": return finite&(x<th)
    if kind in ("CROSS_UP","CROSS_DOWN"):
        out=np.zeros(len(x),bool)
        if len(x)>1:
            good=(t[1:]-t[:-1]==int(sec))&np.isfinite(x[:-1])&np.isfinite(x[1:])
            cross=(x[:-1]<=th)&(x[1:]>th) if kind=="CROSS_UP" else (x[:-1]>=th)&(x[1:]<th)
            out[1:]=good&cross
        return out
    return finite&(x<=th) if q<0.5 else finite&(x>=th)
contexts=folds=feature_series=feature_outcomes=feature_masks=feature_failclosed=transform_series=transform_masks=warm_hits=pack_checks=0
ctx_keys=set(); train_keys=set(); store=m2.MaskBitsetCache(); expected_masks=0
for market in MS:
    for tf,sec in TFS.items():
        p=ROOT/"work/feature_cache_v2"/market/(market+"_"+tf+"_V57_FEATURE_CACHE_V2.npz")
        with np.load(p,allow_pickle=False) as z: cache={k:z[k] for k in z.files}
        ctx=v56.prepare_context(market,tf)
        assert same(cache["time"],ctx["tf_time"]),("TIME_ALIGNMENT",market,tf)
        cid=market+"|"+tf+"|CACHE_V2"; ck=m2.cache_v1.context_key(cache,sec,market,cid)
        assert ck not in ctx_keys,("CONTEXT_KEY_COLLISION",market,tf); ctx_keys.add(ck); contexts+=1
        foldm=[]
        for fi,fspec in enumerate(v56.POL["folds"]):
            tm,vm=v56.fold_masks(ctx,fspec)
            assert tm.shape==cache["time"].shape and vm.shape==tm.shape and np.any(tm) and np.any(vm)
            tk=m2.cache_v1.train_key(tm)
            assert (ck,tk) not in train_keys,("TRAIN_KEY_COLLISION",market,tf,fi)
            train_keys.add((ck,tk)); foldm.append(tm); folds+=1
        for j,(fam,feat,params) in enumerate(FEATURES):
            cond={"family":fam,"feature":feat,"parameters":params,"transform":"LEVEL","threshold_quantile":0.4 if j%2==0 else 0.6}
            base=np.asarray(r2.resolve_feature(cache,cond,sec,market),float)
            s=np.asarray(m2.condition_series_v2(cache,cond,sec,market),float)
            assert same(base,s),("RESOLVER_SERIES",market,tf,feat); feature_series+=1
            for fi,tm in enumerate(foldm):
                th=train_threshold(s,tm,cond["threshold_quantile"]); feature_outcomes+=1
                if th is None:
                    try: store.condition_mask(cache,cond,sec,tm,market,cid)
                    except ValueError as e:
                        assert "NO_FINITE_TRAIN_VALUES" in str(e),("WRONG_FAIL_CLOSED",market,tf,fi,feat,str(e)); feature_failclosed+=1
                    else: raise AssertionError(("EXPECTED_NO_FINITE_FAIL",market,tf,fi,feat))
                else:
                    exp=mask_oracle(s,cache["time"],sec,th,cond["threshold_quantile"],"LEVEL")
                    got,gth=store.condition_mask(cache,cond,sec,tm,market,cid)
                    assert gth==th and np.array_equal(got,exp),("FEATURE_MASK",market,tf,fi,feat)
                    feature_masks+=1; expected_masks+=1
        warm={"family":"time","feature":"weekday_sin","parameters":{},"transform":"LEVEL","threshold_quantile":0.4}
        before=store.stats()["mask_hits"]; store.condition_mask(cache,warm,sec,foldm[0],market,cid)
        assert store.stats()["mask_hits"]==before+1,("WARM_HIT",market,tf); warm_hits+=1
        base_cond={"family":"time","feature":"hour_cos","parameters":{}}
        base=np.asarray(r2.resolve_feature(cache,base_cond,sec,market),float)
        for j,kind in enumerate(TRANS):
            q=0.4 if j%2==0 else 0.6
            cond=dict(base_cond,transform=kind,threshold_quantile=q)
            if kind not in ("LEVEL","CROSS_UP","CROSS_DOWN","ABOVE","BELOW"): cond["lookback"]=5
            s=np.asarray(m2.condition_series_v2(cache,cond,sec,market),float)
            exp_series=base if kind in ("CROSS_UP","CROSS_DOWN","ABOVE","BELOW") else tr.transform(base,np.asarray(cache["time"],np.int64),sec,kind,None if kind=="LEVEL" else 5)
            assert same(s,exp_series),("TRANSFORM_SERIES",market,tf,kind); transform_series+=1
            for fi,tm in enumerate(foldm):
                th=train_threshold(s,tm,q)
                assert th is not None,("TRANSFORM_NO_FINITE",market,tf,fi,kind)
                exp=mask_oracle(s,cache["time"],sec,th,q,kind)
                got,gth=store.condition_mask(cache,cond,sec,tm,market,cid)
                assert gth==th and np.array_equal(got,exp),("TRANSFORM_MASK",market,tf,fi,kind)
                transform_masks+=1; expected_masks+=1
        probe=np.arange(len(cache["time"]))%3==0; packed,n=m2.cache_v1.pack_mask(probe)
        assert np.array_equal(m2.cache_v1.unpack_mask(packed,n),probe); pack_checks+=1
st=store.stats()
assert contexts==24 and folds==72 and feature_series==432 and feature_outcomes==1296
assert feature_masks+feature_failclosed==feature_outcomes
assert transform_series==336 and transform_masks==1008 and warm_hits==24 and pack_checks==24
assert len(ctx_keys)==24 and len(train_keys)==72
assert st["series_entries"]==24*32,("SERIES_ENTRIES",st)
assert st["mask_entries"]==expected_masks,("MASK_ENTRIES",st,expected_masks)
assert st["mask_hits"]>=24 and st["series_hits"]>0
print("V57_V433_MASK_BITSET_CACHE_V2_REAL_DATA_AUDIT|CONTEXTS=%d|FOLDS=%d|FEATURE_SERIES=%d|FEATURE_FOLD_OUTCOMES=%d|FEATURE_MASK_PASS=%d|NO_FINITE_FAIL_CLOSED=%d|TRANSFORM_SERIES=%d|TRANSFORM_MASKS=%d|WARM_HITS=%d|CONTEXT_KEYS=%d|TRAIN_KEYS=%d|PACKBITS=%d"%(contexts,folds,feature_series,feature_outcomes,feature_masks,feature_failclosed,transform_series,transform_masks,warm_hits,len(ctx_keys),len(train_keys),pack_checks))
print("V57_V433_MASK_BITSET_CACHE_V2_REAL_DATA_AUDIT=PASS|18_FEATURES_X_24=SERIES_EXACT|3_FOLDS=ISOLATED|14_TRANSFORMS_X_24_X_3=PASS|NO_FINITE=FAIL_CLOSED|TRAIN_ONLY_THRESHOLDS=PASS|EVENT_GAP_RESET=PASS|CONTEXT_ISOLATION=PASS|WARM_CACHE=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")
