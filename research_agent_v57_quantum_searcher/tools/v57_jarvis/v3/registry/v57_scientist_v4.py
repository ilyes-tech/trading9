import v57_hypothesis_generator_v4 as H
import v57_constrained_generator_v4 as G
import v57_qd_orchestrator_engine_v438_v1 as O
import v57_post_search_fidelity_v1 as F
import importlib.util
from pathlib import Path
_ADMISSION_PATH=Path(__file__).resolve().parents[2]/"autonomy"/"v57_searcher_admission_v1.py"
def _admit(record):
    spec=importlib.util.spec_from_file_location("j57_searcher_admission",_ADMISSION_PATH); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.admit_record(record)
ENGINE="V57_JARVIS_SCIENTIST_V4"
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
    items=[{"strategy":s,"meta":m,"parent_strategy_id":None,"lineage":{"kind":"JARVIS_V4_RESEARCH_ONLY","hypothesis_id":spec["hypothesis_id"],"seed":seed,"index":start+i}} for i,(s,m) in enumerate(pairs)]
    if evaluate:
        records=O.evaluate_items(items,"JARVIS_V4_RESEARCH_ONLY",start)
        for record in records:
            result=record.get("result") if isinstance(record,dict) else None
            if record.get("status")=="EVALUATED" and isinstance(result,dict) and result.get("exact_pass") is True:
                try:
                    record["post_search_fidelity"]=F.qualify_record(record); record["searcher_admission"]=_admit(record)
                    if bool(record["searcher_admission"].get("admitted")) != bool(record["post_search_fidelity"].get("deployment_exact_pass")): raise RuntimeError("FIDELITY_ADMISSION_MISMATCH")
                except Exception as e:
                    record["post_search_fidelity"]={"status":"ERROR","reason":type(e).__name__+":"+str(e),"deployment_exact_pass":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
                    record["searcher_admission"]={"status":"DENIED","reason":"FIDELITY_ERROR","admitted":False,"execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
    else: records=[]
    return {"engine":ENGINE,"status":"COMPLETED","hypothesis":spec,"generated_count":len(items),"evaluated":bool(evaluate),"items":items if not evaluate else [],"records":records,"promotion_allowed":False,"orders_allowed":False,"mt5_launch_allowed":False,"holdout_allowed":False,"mutation_allowed":False}
