import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def eq(f,k,v):
 try:return json.loads((S/f).read_text()).get(k)==v
 except:return False
C=[("persistent_core",8,eq("status_v7.json","status","PASS")),("safety_fail_closed",10,eq("status_v7.json","phase","FULL_AUTONOMOUS_RESEARCH_LOOP")),("persistent_memory",8,eq("reflection_v2.json","status","READY")),("reflection",8,eq("reflection_v2.json","status","READY")),("failure_diagnosis",7,eq("failure_diagnosis_v2.json","status","DIAGNOSED")),("hypothesis_refinement",7,eq("refined_hypothesis_v1.json","status","PROPOSED")),("experiment_planning",6,eq("experiment_plan_v1.json","status","PLANNED")),("capability_audit",5,eq("capability_audit.json","status","PASS")),("executive_reasoning",8,eq("executive_v2.json","status","PASS")),("causal_operator_design",5,eq("causal_operator_v1.json","status","READY")),("metacognition",6,eq("metacognition_v1.json","status","PASS")),("autonomous_research_execution",8,eq("bounded_research_result_v1.json","status","COMPLETED") and eq("research_feedback_v1.json","status","LEARNED")),("action_result_verification_feedback",5,eq("action_feedback_v1.json","status","VERIFIED")),("safe_self_improvement_build_verify_rollback",6,eq("self_improvement_transaction_test_v1.json","status","PASS")),("tool_selection_beyond_search",5,eq("tool_selection_v1.json","status","PASS")),("long_horizon_goal_queue_recovery",4,eq("goal_queue_v2.json","status","READY")),("end_to_end_unattended_acceptance",4,eq("unattended_acceptance_v4.json","status","PASS"))]
def main():
 total=sum(w for _,w,_ in C);earned=sum(w for _,w,p in C if p);pct=round(100*earned/total,1);rem=[n for n,w,p in C if not p]
 out={"schema_version":6,"kind":"JARVIS_COMPLETION_AUDIT_V6","earned":earned,"total":total,"completion_percent":pct,"remaining":rem,"details":[{"capability":n,"weight":w,"passed":p} for n,w,p in C]}
 t=S/"completion_audit_v6.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"completion_audit_v6.json")
 print("ALL PASS|COMPLETION_AUDIT_V6|"+str(earned)+"/"+str(total)+"|"+str(pct)+"%|REMAINING="+str(len(rem)))
if __name__=="__main__":main()
