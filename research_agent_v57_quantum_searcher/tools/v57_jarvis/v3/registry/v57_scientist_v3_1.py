import v57_hypothesis_generator_v3 as H
import v57_constrained_generator_v3_2 as G
import v57_qd_orchestrator_engine_v435_v1 as O
ENGINE="V57_JARVIS_SCIENTIST_V3_1"
SUPPORTED_MARKETS=("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")
SUPPORTED_TIMEFRAMES=("M5","M15","M30","H1")
def experiment(hypothesis,start=0,count=1,evaluate=False,seed=574351):
    start=int(start); count=int(count); seed=int(seed)
    if start<0 or count<1 or count>32: raise ValueError("BAD_RANGE")
    spec=H.parse(hypothesis)
    if not spec.get("market"): raise ValueError("MARKET_REQUIRED")
    if not spec.get("timeframe"): raise ValueError("TIMEFRAME_REQUIRED")
    if not spec.get("side"): raise ValueError("SIDE_REQUIRED")
    if spec["market"] not in SUPPORTED_MARKETS: raise ValueError("UNSUPPORTED_MARKET")
    if spec["timeframe"] not in SUPPORTED_TIMEFRAMES: raise ValueError("UNSUPPORTED_TIMEFRAME")
    pairs=G.generate(spec,count,seed,start)
    items=[{"strategy":s,"meta":m,"parent_strategy_id":None,"lineage":{"kind":"JARVIS_V3_RESEARCH_ONLY","hypothesis_id":spec["hypothesis_id"],"seed":seed,"index":start+i}} for i,(s,m) in enumerate(pairs)]
    if evaluate:
        records=O.evaluate_items(items,"JARVIS_V3_RESEARCH_ONLY",start)
    else:
        records=[]
    return {"engine":ENGINE,"status":"COMPLETED","hypothesis":spec,"generated_count":len(items),"evaluated":bool(evaluate),"items":items if not evaluate else [],"records":records,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False,"holdout_allowed":False,"mutation_allowed":False}
