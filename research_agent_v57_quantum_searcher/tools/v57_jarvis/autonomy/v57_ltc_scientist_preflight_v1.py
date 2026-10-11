import json,sys
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
sys.path.insert(0,str(R/"research_agent_v57_quantum_searcher/src/v435_ltc"))
def main():
 a=json.loads((S/"ltc_capability_adapter_v1.json").read_text())
 if a.get("status")!="DISCOVERED" or a.get("market")!="LTCUSD" or a.get("evaluation_authorized") is not False:raise RuntimeError("CAPABILITY_GATE")
 import v57_v435_ltc_search_v1 as L
 L.ensure_integrity()
 pairs=L.lgen.generate(4,seed=574351,start=0)
 if len(pairs)!=4 or len({s["strategy_id"] for s,m in pairs})!=4:raise RuntimeError("GENERATION_FAILED")
 if any(s["market"]["symbol"]!="LTCUSD" or s["execution"]["orders_allowed"] is not False for s,m in pairs):raise RuntimeError("RESEARCH_ONLY_GATE")
 if any(m["timeframe"] not in a["timeframes"] for s,m in pairs):raise RuntimeError("TIMEFRAME_GATE")
 doc={"schema_version":1,"kind":"V57_LTC_SCIENTIST_PREFLIGHT_V1","status":"PASS","market":"LTCUSD","sample_candidates":4,"integrity":"FROZEN_HASHES_PASS","evaluation_started":False,"evaluation_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"next_gate":"EVIDENCE_BACKED_HYPOTHESIS_REQUIRED"}
 q=S/"ltc_scientist_preflight_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"ltc_scientist_preflight_v1.json")
 print("ALL PASS|LTC_SCIENTIST_PREFLIGHT_V1|FROZEN=PASS|GENERATED=4|EVALUATION=FALSE|NEXT=HYPOTHESIS_GATE")
if __name__=="__main__":main()
