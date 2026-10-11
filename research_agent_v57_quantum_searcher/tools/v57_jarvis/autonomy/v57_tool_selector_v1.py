import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
TOOLS={"MEMORY":{"cost":1,"purpose":"remember evidence"},"REFLECTION":{"cost":1,"purpose":"reason over evidence"},"DIAGNOSIS":{"cost":1,"purpose":"explain failed gates"},"CAUSAL_DESIGN":{"cost":1,"purpose":"design bounded experiment"},"REPLAY":{"cost":2,"purpose":"verify known candidate"},"DEEP_VALIDATOR":{"cost":3,"purpose":"robustness validation"},"SEARCHER":{"cost":8,"purpose":"discover candidates"}}
def main():
 r=json.loads((S/"reflection_v2.json").read_text());d=json.loads((S/"failure_diagnosis_v2.json").read_text())
 # Selection is advisory; downstream authorization remains mandatory.
 try:
  objective=json.loads((S/"bounded_objective_v1.json").read_text())
  causal=json.loads((S/"causal_family_admission_v2.json").read_text())
  evidence=json.loads((S/"independent_evidence_verifier_v2.json").read_text())
  discovery=(objective.get("status")=="OPEN_REVIEW_ONLY" and objective.get("objective_type") in ("HYPOTHESIS_REVIEW","FEEDBACK_REVIEW") and causal.get("new_family_admitted") is True and causal.get("research_execution_authorized") is True and evidence.get("causal_novelty_proven") is True and evidence.get("new_research_authorized") is True)
 except (OSError,ValueError,TypeError):discovery=False
 if discovery:selected=["SEARCHER"];reason="CAUSAL_DISCOVERY_ADMITTED_REQUIRES_EXECUTION_GATE"
 elif d.get("status")=="DIAGNOSED": selected=["DIAGNOSIS","CAUSAL_DESIGN"];reason="KNOWN_FAILURE_USE_CHEAP_CAUSAL_TOOLS_FIRST"
 elif r.get("next_action")=="ANALYZE_EXISTING_DEEP_EVIDENCE":selected=["REPLAY","DEEP_VALIDATOR"];reason="VERIFY_EXISTING_EVIDENCE"
 else:selected=["MEMORY","REFLECTION"];reason="NO_JUSTIFIED_EXPENSIVE_ACTION"
 out={"schema_version":1,"kind":"JARVIS_TOOL_SELECTOR_V1","status":"PASS","selected":selected,"reason":reason,"catalog":TOOLS,
 "selection_rule":"MINIMUM_SUFFICIENT_TOOL; SEARCHER_ONLY_WHEN_DISCOVERY_IS_JUSTIFIED","searcher_selected":"SEARCHER" in selected,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"tool_selection_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"tool_selection_v1.json")
 print("ALL PASS|TOOL_SELECTOR_V1|SELECTED="+",".join(selected)+"|SEARCHER="+str("SEARCHER" in selected).upper())
if __name__=="__main__":main()
