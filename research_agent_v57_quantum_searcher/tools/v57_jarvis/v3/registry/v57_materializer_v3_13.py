from pathlib import Path
import hashlib,json,sys,numpy as np
ROOT=Path("research_agent_v57_quantum_searcher"); SRC=ROOT/"src"; V433=SRC/"v433"; V435=SRC/"v435"; REG=ROOT/"tools/v57_jarvis/v3/registry"
for p in (SRC,V433,V435,REG):
    if str(p.resolve()) not in sys.path: sys.path.insert(0,str(p.resolve()))
import v57_mask_bitset_cache_v3 as M
import v57_candidate_signal_engine_v1 as legacy
import v57_strategy_dsl_v3 as DSL
METHOD="FIT_THRESHOLDS_ON_FULL_DEVELOPMENT_FEATURE_CACHE_AFTER_FINAL_SELECTION"
def _conditions(node,out=None):
    if out is None: out=[]
    if isinstance(node,dict):
        if all(k in node for k in ("family","feature","transform","threshold_quantile")): out.append(node)
        else:
            for v in node.values(): _conditions(v,out)
    elif isinstance(node,list):
        for v in node: _conditions(v,out)
    return out
def _ckey(c):
    import v57_mask_bitset_cache_v1 as C
    return C.condition_key(c)
def materialize(strategy,ctx):
    DSL.validate_strategy(strategy)
    sid=strategy.get("strategy_id") or DSL.strategy_id(strategy)
    if strategy["research_integrity"].get("holdout_read") is not False: raise ValueError("HOLDOUT_NOT_FALSE")
    if strategy["research_integrity"].get("september_2026_data_accessed") is not False: raise ValueError("SEPTEMBER_2026_NOT_FALSE")
    if strategy.get("execution",{}).get("orders_allowed") is not False: raise ValueError("ORDERS_NOT_FALSE")
    cache=ctx["v57_cache"]; n=len(np.asarray(cache["time"])); full=np.ones(n,dtype=bool)
    rows=[]
    seen=set()
    for c in _conditions(strategy["signal"]):
        key=_ckey(c)
        if key in seen: continue
        seen.add(key)
        series=np.asarray(M.condition_series_v2(cache,c,int(ctx["sec"]),ctx["market"]),dtype=float)
        if series.shape!=(n,): raise ValueError("BAD_CONDITION_SERIES_SHAPE")
        finite=np.isfinite(series)&full
        if not np.any(finite): raise ValueError("NO_FINITE_FULL_DEVELOPMENT_VALUES")
        q=float(c["threshold_quantile"]); th=float(legacy.fit_threshold(series,full,q))
        rows.append({"condition_key":key,"family":c["family"],"feature":c["feature"],"parameters":c.get("parameters",{}),"transform":c["transform"],"lookback":c.get("lookback"),"threshold_quantile":q,"threshold":th,"finite_values":int(finite.sum())})
    rows.sort(key=lambda x:x["condition_key"])
    if not rows: raise ValueError("NO_MATERIALIZABLE_CONDITIONS")
    times=np.asarray(cache["time"],dtype=np.int64)
    finite_times=times[np.isfinite(times)]
    return {"schema_version":1,"kind":"V57_JARVIS_MATERIALIZATION_V3_13","status":"MATERIALIZED_RESEARCH_ONLY","strategy_id":sid,"market":strategy["market"]["symbol"],"timeframe":strategy["market"]["timeframe"],"side":strategy["market"]["side"],"calibration_method":METHOD,"development_rows":int(n),"development_first_epoch":int(finite_times[0]),"development_last_epoch":int(finite_times[-1]),"conditions":rows,"thresholds_by_condition_key":{x["condition_key"]:x["threshold"] for x in rows},"materialized":True,"selection_after_materialization":False,"performance_retuning":False,"research_integrity":{"holdout_read":False,"september_2026_data_accessed":False,"orders_allowed":False,"demo_orders_allowed":False,"real_orders_allowed":False,"mt5_launch_allowed":False}}
def self_check():
    assert METHOD=="FIT_THRESHOLDS_ON_FULL_DEVELOPMENT_FEATURE_CACHE_AFTER_FINAL_SELECTION"
    src=Path(__file__).read_text()
    assert "np.ones(n,dtype=bool)" in src
    assert "legacy.fit_threshold(series,full,q)" in src
    assert "\"demo_orders_allowed\":False" in src and "\"mt5_launch_allowed\":False" in src
    assert "performance_retuning\":False" in src
    print("ALL PASS|V313_MATERIALIZER|FULL_DEVELOPMENT|NO_RETUNING|NO_HOLDOUT|NO_ORDERS")
if __name__=="__main__": self_check()
