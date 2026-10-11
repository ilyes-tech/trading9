from pathlib import Path
import collections,hashlib,json,sys,numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parent
ROOT=SRC.parent
for p in (HERE,SRC):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
import v57_search_replay_v1 as new
import v57_replay_evaluator_v2 as old
import v57_strategy_dsl_v3 as dsl3
import v57_fold_signal_adapter_v2 as adapter2
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert H(HERE/"v57_search_replay_v1.py")=="4732f4e824f5af4b2942733367239fecbef8198750c0a7af6f96f68d27bf8706"
assert H(HERE/"v57_strategy_signal_engine_v5.py")=="8d0714ef291760baede7fdff47344925c616184196002b95124d9ccb448ace43"
assert H(ROOT/"config/v433/V57_V433_STRATEGY_SIGNAL_ENGINE_V5_FREEZE_V1.json")=="25bc34a33be9c9c5e2dc0baf3443837503f9001950cb3277bdb3e128c86d6913"
assert H(HERE/"v57_fold_signal_adapter_v2.py")=="ace33c4f7eaf1c7c42ca002c38f34c08860a34dd5c56874593444e5721788506"
READY=ROOT/"work/autopilot_v432/shadow_ready"
files=sorted(READY.glob("READY_*.json"))
assert len(files)==179,("READY_COUNT",len(files))
ctxs={}; stores={}; strategies=fold_checks=paired_errors=failures=0; errtypes=collections.Counter()
FF=("trades","tpd","base_avg_bps","base_pf","stress_avg_bps","stress_pf","drawdown_bps","signal_events","eligible_pre_nonoverlap","selected_trades","pass")
RF=("exact_pass","worst_stress_avg_bps","min_stress_pf","worst_base_avg_bps","min_base_pf","mean_stress_avg_bps","mean_base_avg_bps","worst_drawdown_bps","total_selected_trades")
def same(a,b):
    if a is None or b is None: return a is b
    if isinstance(a,(float,np.floating)) or isinstance(b,(float,np.floating)):
        try:
            x=float(a); y=float(b); return (np.isnan(x) and np.isnan(y)) or x==y
        except Exception: return False
    return a==b
for i,p in enumerate(files,1):
    z=json.loads(p.read_text()); c=z["candidate"]; side=str(z["side"]).upper(); key=(c["market"],c["timeframe"])
    if key not in ctxs:
        ctxs[key]=adapter2.prepare_context(*key); stores[key]=new.signal5.bitcache.MaskBitsetCache()
    ctx=ctxs[key]; st=dsl3.from_v1_candidate(c,side); strategies+=1
    try:
        a=old.evaluate_candidate(ctx,c,side)
    except Exception as e1:
        try: new.evaluate_strategy(ctx,st,stores[key])
        except Exception as e2:
            if type(e1) is not type(e2) or str(e1)!=str(e2): raise AssertionError(("ERROR_PARITY",p.name,type(e1).__name__,str(e1),type(e2).__name__,str(e2)))
            paired_errors+=1; errtypes[type(e1).__name__+":"+str(e1)]+=1
        else: raise AssertionError(("OLD_ERROR_NEW_PASS",p.name,type(e1).__name__,str(e1)))
    else:
        b=new.evaluate_strategy(ctx,st,stores[key])
        assert len(a["folds"])==len(b["folds"])==3
        for x,y in zip(a["folds"],b["folds"]):
            for k in FF:
                if not same(x.get(k),y.get(k)): raise AssertionError(("FOLD_PARITY",p.name,k,x.get(k),y.get(k)))
            fold_checks+=1
        for k in RF:
            if not same(a.get(k),b.get(k)): raise AssertionError(("RESULT_PARITY",p.name,k,a.get(k),b.get(k)))
    if i%20==0 or i==len(files): print("V57_V433_SEARCH_REPLAY_AUDIT_PROGRESS|READY=%d/%d|FOLD_CHECKS=%d|PAIRED_ERRORS=%d"%(i,len(files),fold_checks,paired_errors),flush=True)
base=json.loads(files[0].read_text()); c=base["candidate"]; side=str(base["side"]).upper(); key=(c["market"],c["timeframe"]); ctx=ctxs[key]; st=dsl3.from_v1_candidate(c,side)
ca={"family":"momentum","feature":"STOCHASTIC","parameters":{"window":14},"transform":"LEVEL","threshold_quantile":0.4}
cb={"family":"momentum","feature":"ROC","parameters":{"window":10},"transform":"LEVEL","threshold_quantile":0.6}
native=[]
for node in ({"op":"PERSIST_N","n":2,"child":{"op":"COND","condition":ca}},{"op":"THEN_WITHIN_N","n":3,"children":[{"op":"COND","condition":ca},{"op":"COND","condition":cb}]},{"op":"NAND","children":[{"op":"COND","condition":ca},{"op":"COND","condition":cb}]}):
    q=dict(st); q.pop("strategy_id",None); q["signal"]=dsl3.normalize_node(node); q=dsl3.finalize_strategy(q); r=new.evaluate_strategy(ctx,q,stores[key]); assert len(r["folds"])==3; native.append(q["signal"]["op"])
print("V57_V433_SEARCH_REPLAY_FULL_AUDIT|READY=179|STRATEGIES=%d|FOLD_CHECKS=%d|PAIRED_ERRORS=%d|CONTEXTS=%d|NATIVE_AST=3"%(strategies,fold_checks,paired_errors,len(ctxs)))
print("V57_V433_SEARCH_REPLAY_FULL_AUDIT=PASS|LEGACY_REPLAY_EXACT=PASS|CANONICAL_CACHE_V2=PASS|V5_SIGNAL=PASS|NEW_FEATURE_NATIVE_AST=PASS|NATIVE_OPS="+",".join(native)+"|HOLDOUT=UNREAD|ORDERS=DISABLED")
print("PAIRED_ERROR_TYPES="+json.dumps(dict(errtypes),sort_keys=True))
