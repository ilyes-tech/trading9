from pathlib import Path
import collections,copy,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
for p in (HERE,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_native_strategy_generator_v1 as gen
import v57_search_runtime_v2 as runtime
import v57_search_replay_v1 as replay
import v57_strategy_signal_engine_v5 as signal5
import v57_fold_signal_adapter_v2 as adapter2
import v57_strategy_dsl_v3 as dsl3
import v57_logic_registry_compiler_v2 as compiler
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(HERE/"v57_native_strategy_generator_v1.py")=="2d0698578dcb1e09eeb935cf96db672b8b41d55a96edd6704b03d2d93adb0afd"
assert H(ROOT/"config/v433/V57_V433_SEARCH_RUNTIME_V2_FREEZE_V1.json")=="2c572b23a1386a898fe57029beec4cbfa82487120e12d9973ae7cb4b31229714"
assert H(HERE/"v57_search_replay_v1.py")=="4732f4e824f5af4b2942733367239fecbef8198750c0a7af6f96f68d27bf8706"
assert H(HERE/"v57_strategy_signal_engine_v5.py")=="8d0714ef291760baede7fdff47344925c616184196002b95124d9ccb448ace43"
assert H(HERE/"v57_fold_signal_adapter_v2.py")=="ace33c4f7eaf1c7c42ca002c38f34c08860a34dd5c56874593444e5721788506"
assert H(HERE/"v57_strategy_dsl_v3.py")=="8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b"
assert H(HERE/"v57_logic_registry_compiler_v2.py")=="a5f1dcd7d557dac35940bbdcf0faffcdcc6ed460f97cf0e28aa183c0fbf37077"
gen._ensure(); runtime._ensure()
N=184
built=gen.generate(N,57433103,0)
assert len(built)==N
logic_counts=collections.Counter(); market_counts=collections.Counter(); active_features=collections.Counter(); ids=[]
def walk(n):
    if not isinstance(n,dict): return
    if n.get("op")=="COND":
        c=n["condition"]; active_features[(c.get("family"),c.get("feature"))]+=1
    if "child" in n: walk(n["child"])
    for x in n.get("children",[]): walk(x)
for st,m in built:
    assert dsl3.validate_strategy(st)
    ids.append(st["strategy_id"]); logic_counts[m["logic"]]+=1; market_counts[(m["market"],m["timeframe"])]+=1; walk(st["signal"])
    assert st["execution"]["orders_allowed"] is False
    ri=st["research_integrity"]
    assert ri["holdout_read"] is False and ri["holdout_evaluated"] is False and ri["september_2026_data_accessed"] is False and ri["real_orders_allowed"] is False and ri["demo_orders_allowed"] is False
assert len(set(ids))==N
assert set(logic_counts)==set(gen.READY)
assert all(logic_counts[x]==4 for x in gen.READY)
assert any(x in active_features for x in gen.NEW_FEATURES)
assert all(f!="crypto_microstructure" for f,_ in gen.feature_pool("EURUSD"))
assert all(f!="crypto_microstructure" for f,_ in gen.feature_pool("XAUUSD"))
forced_rows=gen._rows(len(gen.NEW_FEATURES),57433104)
forced=[]
ctx=adapter2.prepare_context("XAUUSD","M5"); store=signal5.bitcache.MaskBitsetCache(); base=gen.build_strategy(gen._rows(1,57433105)[0],0)[0]
for i,(fam,feat) in enumerate(gen.NEW_FEATURES):
    c=gen.condition_for_feature(fam,feat,forced_rows[i],0); gen._validate_new_condition(c); c=copy.deepcopy(c); c["transform"]="LEVEL"; node=compiler.condition_node(c); q=copy.deepcopy(base); q.pop("strategy_id",None); q["market"]={"symbol":"XAUUSD","timeframe":"M5","side":"LONG"}; q["signal"]=node; q["legacy"]=copy.deepcopy(q.get("legacy",{})); q["legacy"]["generator_audit_forced_feature"]=feat; q=dsl3.finalize_strategy(q); assert dsl3.validate_strategy(q)
    ok=0
    for fi in range(3):
        train,valid=adapter2.fold_masks(ctx,fi); sig=signal5.strategy_signal(ctx["v57_cache"],q,ctx["sec"],np.asarray(train,dtype=bool),"XAUUSD",store,"XAUUSD|M5|NATIVE_GEN_AUDIT"); assert np.asarray(sig["signal"],dtype=bool).shape==np.asarray(valid,dtype=bool).shape; ok+=1
    forced.append(feat)
assert set(forced)=={x[1] for x in gen.NEW_FEATURES}
ctxs={}; stores={}; evaluated=rejected=no_finite=errors=0; error_types=collections.Counter()
for i,(st,m) in enumerate(built,1):
    key=(m["market"],m["timeframe"])
    if key not in ctxs: ctxs[key]=adapter2.prepare_context(*key); stores[key]=signal5.bitcache.MaskBitsetCache()
    try:
        pf=runtime.signal_prefilter(ctxs[key],st,stores[key])
        if not pf["pass"]: rejected+=1
        else:
            r=replay.evaluate_strategy(ctxs[key],st,stores[key]); assert isinstance(r,dict) and len(r["folds"])==3; evaluated+=1
    except ValueError as e:
        if str(e)=="NO_FINITE_TRAIN_VALUES": no_finite+=1
        else: errors+=1; error_types[type(e).__name__+":"+str(e)]+=1
    except Exception as e:
        errors+=1; error_types[type(e).__name__+":"+str(e)]+=1
    if i%23==0 or i==N: print("V57_V433_NATIVE_GENERATOR_AUDIT_PROGRESS|DONE=%d/%d|EVALUATED=%d|PREFILTER_REJECT=%d|NO_FINITE=%d|ERRORS=%d"%(i,N,evaluated,rejected,no_finite,errors),flush=True)
assert errors==0,dict(error_types)
assert evaluated>0
assert evaluated+rejected+no_finite==N
assert len(ctxs)>0
print("V57_V433_NATIVE_STRATEGY_GENERATOR_FULL_AUDIT|STRATEGIES=%d|LOGICS=46|LOGIC_REPETITIONS=4|UNIQUE_IDS=%d|CONTEXTS=%d|EVALUATED=%d|PREFILTER_REJECT=%d|NO_FINITE_FAIL_CLOSED=%d|ERRORS=0|FORCED_NEW18=18|FORCED_FOLD_CHECKS=54"%(N,len(set(ids)),len(ctxs),evaluated,rejected,no_finite))
print("V57_V433_NATIVE_STRATEGY_GENERATOR_FULL_AUDIT=PASS|GENERATOR_NATIVE=PASS|DSL3=PASS|COMPILE_READY_46=PASS|NEW18_PARAMETERS=PASS|NEW18_V5_SIGNAL=PASS|MICRO_CRYPTO_ONLY=PASS|SEARCH_REPLAY_PATH=PASS|NO_FINITE_FAIL_CLOSED=PASS|HOLDOUT=UNREAD|ORDERS=DISABLED")
