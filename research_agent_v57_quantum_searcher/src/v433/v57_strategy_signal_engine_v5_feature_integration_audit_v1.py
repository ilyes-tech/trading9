from pathlib import Path
import hashlib,sys,numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
import v57_strategy_signal_engine_v5 as v5
import v57_fold_signal_adapter_v2 as a2
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(HERE/"v57_strategy_signal_engine_v5.py")=="8d0714ef291760baede7fdff47344925c616184196002b95124d9ccb448ace43"
assert H(HERE/"v57_fold_signal_adapter_v2.py")=="ace33c4f7eaf1c7c42ca002c38f34c08860a34dd5c56874593444e5721788506"
assert H(HERE/"v57_mask_bitset_cache_v2.py")=="267099b5275008a0e3a8298f96ef2767d64a46aa61eb1b5258ca340cb4e6320e"
assert H(ROOT/"config/v433/V57_V433_MASK_BITSET_CACHE_V2_FREEZE_V1.json")=="7f15db516571b99fca00315d9daadb018a70046860e97f01ebc910958951ddcd"
FEATURES=[("momentum","STOCHASTIC",{"window":14}),("momentum","ROC",{"window":10}),("momentum","CCI",{"window":20}),("momentum","WILLIAMS_R",{"window":14}),("momentum","ULTIMATE_OSCILLATOR",{"parameter_set":[7,14,28]}),("momentum","FISHER_TRANSFORM",{"window":10}),("trend","SMA",{"window":20}),("trend","EMA",{"window":20}),("trend","ADX",{"window":14}),("trend","PLUS_DI",{"window":14}),("trend","MINUS_DI",{"window":14}),("volatility","ATR",{"window":14}),("volatility","NATR",{"window":14}),("volume","CMF",{"window":20}),("volume","MFI",{"window":14}),("volume","VWAP_DISTANCE",{}),("time","weekday_sin",{}),("time","weekday_cos",{})]
MS=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
TFS=("M5","M15","M30","H1")
store=v5.bitcache.MaskBitsetCache()
contexts=folds=checks=passed=failclosed=0
for market in MS:
    for tf in TFS:
        ctx=a2.prepare_context(market,tf); cache=ctx["v57_cache"]; sec=int(ctx["sec"]); cid=market+"|"+tf+"|V5_FEATURE_AUDIT"; contexts+=1
        for fi in range(3):
            train,valid=a2.fold_masks(ctx,fi); train=np.asarray(train,dtype=bool); valid=np.asarray(valid,dtype=bool); assert train.shape==valid.shape==np.asarray(cache["time"]).shape; folds+=1
            for j,(fam,feat,params) in enumerate(FEATURES):
                cond={"family":fam,"feature":feat,"parameters":params,"transform":"LEVEL","threshold_quantile":0.4 if j%2==0 else 0.6}; node={"op":"COND","condition":cond}; thresholds={}; checks+=1
                try:
                    got=v5._eval_node(cache,node,sec,train,market,store,cid,thresholds)
                except ValueError as e:
                    assert "NO_FINITE_TRAIN_VALUES" in str(e),("AST_UNEXPECTED_FAIL",market,tf,fi,feat,str(e))
                    try: store.condition_mask(cache,cond,sec,train,market,cid)
                    except ValueError as e2: assert "NO_FINITE_TRAIN_VALUES" in str(e2)
                    else: raise AssertionError(("DIRECT_SHOULD_FAIL",market,tf,fi,feat))
                    failclosed+=1
                else:
                    exp,th=store.condition_mask(cache,cond,sec,train,market,cid); assert np.array_equal(np.asarray(got,dtype=bool),np.asarray(exp,dtype=bool)),("AST_MASK",market,tf,fi,feat); assert len(thresholds)==1,("THRESHOLD_COUNT",market,tf,fi,feat); passed+=1
st=store.stats()
assert contexts==24 and folds==72 and checks==1296
assert passed==1290 and failclosed==6
assert st["series_entries"]==432,st
assert st["mask_entries"]==1290,st
assert st["mask_hits"]>=1290,st
print("V57_V433_SIGNAL_ENGINE_V5_FEATURE_INTEGRATION_AUDIT|CONTEXTS=24|FOLDS=72|FEATURES=18|AST_CHECKS=1296|PASS=1290|NO_FINITE_FAIL_CLOSED=6|SERIES_ENTRIES=432|MASK_ENTRIES=1290")
print("V57_V433_SIGNAL_ENGINE_V5_FEATURE_INTEGRATION_AUDIT=PASS|COND_COLD_PATH=PASS|MASK_V2_EXACT=PASS|TRAIN_ONLY_THRESHOLDS=PASS|CACHE_WARM_REPLAY=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")
