import hashlib,json,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");A=R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
C=("v57_autonomous_core_v15.py","v57_research_agenda_v3.py","v57_agenda_terminal_v2.py","v57_agenda_replanner_v2.py","v57_experiment_designer_v3.py","v57_hypothesis_refiner_v3.py","v57_causal_operator_v2.py","v57_bounded_research_executor_v3.py","v57_research_feedback_v1.py","v57_branch_terminal_v2.py","v57_action_feedback_v3.py","v57_unattended_acceptance_v7.py","v57_completion_audit_v9.py")
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 u=json.loads((S/"unattended_acceptance_v7.json").read_text());a=json.loads((S/"completion_audit_v9.json").read_text());st=json.loads((S/"status_v15.json").read_text())
 if u.get("status")!="PASS" or a.get("status")!="PASS" or a.get("completion_percent")!=100.0 or st.get("mode")!="SAFE_STOP_NO_NOVEL_DIRECTION":raise RuntimeError("FREEZE_PRECONDITION_FAILED")
 out={"schema_version":1,"kind":"JARVIS_AUTONOMOUS_CORE_V15_FINAL_FREEZE","status":"FROZEN_FINAL","created_ns":time.time_ns(),"scope":"FULL_RESEARCH_AUTONOMY_EVIDENCE_BOUNDED_SAFE_STOP","components":{n:h(A/n) for n in C},"evidence":{"unattended_acceptance_v7.json":h(S/"unattended_acceptance_v7.json"),"completion_audit_v9.json":h(S/"completion_audit_v9.json"),"status_v15.json":h(S/"status_v15.json"),"research_agenda_v3.json":h(S/"research_agenda_v3.json"),"agenda_replanner_v2.json":h(S/"agenda_replanner_v2.json")},"verified_consecutive_cycles":u["verified_consecutive_cycles"],"completion_percent":a["completion_percent"],"invariants":{"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False,"terminal_no_executor":True,"terminal_no_refiner":True,"agenda_active":None,"agenda_exhausted_count":4,"replan_decision":"SAFE_STOP"}}
 payload=json.dumps(out,sort_keys=True,separators=(",",":")).encode();out["manifest_payload_sha256"]=hashlib.sha256(payload).hexdigest();p=S/"JARVIS_AUTONOMOUS_CORE_V15_FINAL_FREEZE.json";p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print("ALL PASS|V15_FINAL_FREEZE|MANIFEST="+out["manifest_payload_sha256"]+"|COMPONENTS="+str(len(C)))
if __name__=="__main__":main()
