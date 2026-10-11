import json,hashlib
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
P=R/"work/v435_ltc/search_v1/V57_V435_LTC_SEARCH_RESULT_V1.final_4096_corrected.json"
def main():
 pre=json.loads((S/"ltc_scientist_preflight_v1.json").read_text());x=json.loads(P.read_text())
 if pre.get("status")!="PASS" or pre.get("evaluation_started") is not False:raise RuntimeError("PREFLIGHT_INVALID")
 if x.get("market")!="LTCUSD" or x.get("status")!="COMPLETE" or x.get("budget")!=4096 or x.get("completed_candidates")!=4096:raise RuntimeError("HISTORICAL_INCOMPLETE")
 counts=x.get("status_counts",{})
 if sum(counts.values())!=4096 or x.get("exact_pass")!=0 or x.get("champion") is not None:raise RuntimeError("HISTORICAL_EVIDENCE_MISMATCH")
 integ=x.get("research_integrity",{})
 if any(integ.get(k) is not False for k in ("holdout_read","holdout_evaluated","real_orders_allowed","september_2026_data_accessed")):raise RuntimeError("INTEGRITY_GATE")
 doc={"schema_version":1,"kind":"V57_LTC_EVIDENCE_GATE_V1","status":"SAFE_STOP","market":"LTCUSD","historical_result_sha256":hashlib.sha256(P.read_bytes()).hexdigest(),"historical_budget":4096,"historical_evaluated":counts.get("EVALUATED"),"historical_prefilter_reject":counts.get("PREFILTER_REJECT"),"historical_exact_pass":0,"repeat_unconstrained_search_allowed":False,"next_gate":"DISTINCT_EVIDENCE_BACKED_HYPOTHESIS","evaluation_started":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"ltc_evidence_gate_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"ltc_evidence_gate_v1.json")
 print("ALL PASS|LTC_EVIDENCE_GATE_V1|HISTORICAL=4096|EXACT=0|REPEAT=DENIED|NEXT=SAFE_STOP")
if __name__=="__main__":main()
