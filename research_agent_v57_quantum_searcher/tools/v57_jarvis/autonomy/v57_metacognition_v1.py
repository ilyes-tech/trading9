import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 names=["reflection_v2.json","failure_diagnosis_v2.json","refined_hypothesis_v1.json","experiment_plan_v1.json","causal_operator_v1.json","executive_v2.json"]
 x={n:json.loads((S/n).read_text()) for n in names}
 contradictions=[]
 if x["executive_v2.json"].get("research_execution_authorized"):contradictions.append("EXECUTION_UNEXPECTED")
 if x["causal_operator_v1.json"].get("searcher_invoked"):contradictions.append("SEARCHER_UNEXPECTED")
 if x["failure_diagnosis_v2.json"]["next_action"]!="REFINE_RESEARCH_HYPOTHESIS":contradictions.append("DIAGNOSIS_CHAIN")
 if x["refined_hypothesis_v1.json"]["next_action"]!="DESIGN_BOUNDED_EXPERIMENT":contradictions.append("HYPOTHESIS_CHAIN")
 out={"schema_version":1,"kind":"JARVIS_METACOGNITION_V1","status":"PASS" if not contradictions else "FAIL","contradictions":contradictions,
 "assessment":"COHERENT_COGNITIVE_CHAIN" if not contradictions else "INCOHERENT_CHAIN","next_action":"OBSERVE_NEW_EVIDENCE",
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"metacognition_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"metacognition_v1.json")
 print(("ALL PASS" if not contradictions else "STOP|FAIL")+"|METACOGNITION_V1|"+out["assessment"])
if __name__=="__main__":main()
