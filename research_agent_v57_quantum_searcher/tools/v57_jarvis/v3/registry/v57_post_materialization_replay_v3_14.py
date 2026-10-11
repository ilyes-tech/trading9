from pathlib import Path
import sys,numpy as np
ROOT=Path("research_agent_v57_quantum_searcher"); SRC=ROOT/"src"; V433=SRC/"v433"; V435=SRC/"v435"
for p in (SRC,V433,V435):
    if str(p.resolve()) not in sys.path: sys.path.insert(0,str(p.resolve()))
import v57_search_replay_v371_v1 as R
import v57_mask_bitset_cache_v3 as M
import v57_mask_bitset_cache_v1 as C
import v57_candidate_signal_engine_v1 as legacy
class FixedThresholdCache:
    def __init__(self,materialization):
        if materialization.get("kind")!="V57_JARVIS_MATERIALIZATION_V3_13" or materialization.get("materialized") is not True: raise ValueError("BAD_MATERIALIZATION")
        ri=materialization.get("research_integrity",{})
        if ri.get("holdout_read") is not False or ri.get("september_2026_data_accessed") is not False or ri.get("orders_allowed") is not False: raise ValueError("MATERIALIZATION_INTEGRITY_FAIL")
        self.thresholds={str(k):float(v) for k,v in materialization["thresholds_by_condition_key"].items()}
        self._series={}
    def condition_mask(self,cache,condition,sec,train_mask,market=None,context_id=None):
        n=len(np.asarray(cache["time"])); tm=np.asarray(train_mask,dtype=bool)
        if tm.shape!=(n,): raise ValueError("BAD_TRAIN_MASK_SHAPE")
        key=C.condition_key(condition)
        if key not in self.thresholds: raise ValueError("FIXED_THRESHOLD_MISSING:"+key)
        th=float(self.thresholds[key])
        skey=(C.context_key(cache,sec,market,context_id),C.series_condition_key(condition))
        series=self._series.get(skey)
        if series is None:
            series=np.asarray(M.condition_series_v2(cache,condition,int(sec),market),dtype=float)
            if series.shape!=(n,): raise ValueError("BAD_CONDITION_SERIES_SHAPE")
            self._series[skey]=series
        kind=str(condition["transform"]); q=float(condition["threshold_quantile"])
        if kind in legacy.EVENT_TRANSFORMS: mask=legacy.event_threshold_mask(series,cache["time"],int(sec),th,kind)
        elif kind in legacy.NUMERIC_TRANSFORMS: mask=legacy.numeric_threshold_mask(series,th,q)
        else: raise ValueError("UNKNOWN_TRANSFORM:"+kind)
        return np.asarray(mask,dtype=bool),th
def evaluate(strategy,ctx,materialization):
    sid=strategy.get("strategy_id") or R.dsl3.strategy_id(strategy)
    if materialization.get("strategy_id")!=sid: raise ValueError("STRATEGY_ID_MISMATCH")
    fixed=R.evaluate_strategy(ctx,strategy,shared_cache=FixedThresholdCache(materialization))
    return {"schema_version":1,"kind":"V57_JARVIS_POST_MATERIALIZATION_REPLAY_V3_14","strategy_id":sid,"scope":"DEVELOPMENT_FOLDS_ONLY","intervention":"REPLACE_FOLD_FITTED_THRESHOLDS_WITH_EXACT_FULL_DEVELOPMENT_MATERIALIZED_THRESHOLDS","materialized":True,"fixed_replay":fixed,"conclusion":"POST_MATERIALIZATION_REPLAY_PASS" if fixed["exact_pass"] else "POST_MATERIALIZATION_REPLAY_FAIL","research_integrity":{"holdout_read":False,"september_2026_data_accessed":False,"orders_allowed":False,"demo_orders_allowed":False,"real_orders_allowed":False,"mt5_launch_allowed":False}}
def self_check():
    src=Path(__file__).read_text()
    assert "fit"+"_threshold(" not in src
    assert "FixedThresholdCache(materialization)" in src
    assert "R.evaluate_strategy(ctx,strategy,shared_cache=" in src
    print("ALL PASS|V314_POST_MATERIALIZATION_REPLAY|FIXED_THRESHOLDS|NO_REFIT|NO_HOLDOUT|NO_ORDERS")
if __name__=="__main__": self_check()
