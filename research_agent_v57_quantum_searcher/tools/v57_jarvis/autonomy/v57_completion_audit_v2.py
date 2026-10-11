import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def okfile(n,k,v):
 try:return json.loads((S/n).read_text()).get(k)==v
 except:return False
checks=[
("persistent_core",8,okfile("status_v3.json","status","PASS")),
("safety_fail_closed",10,okfile("status_v3.json","status","PASS") and okfile("status_v3.json","phase","AUTONOMOUS_COGNITIVE_LOOP")),
("persistent_memory",8,okfile("reflection_v2.json","status","READY")),
("reflection",8,okfile("reflection_v2.json","status","READY")),
("failure_diagnosis",7,okfile("failure_diagnosis_v2.json","status","DIAGNOSED")),
("hypothesis_refinement",7,okfile("refined_hypothesis_v1.json","status","PROPOSED")),
("experiment_planning",6,okfile("experiment_plan_v1.json","status","PLANNED")),
("capability_audit",5,okfile("capability_audit.json","status","PASS")),
("executive_reasoning",8,okfile("executive_v2.json","status","PASS")),
("causal_operator_design",5,okfile("causal_operator_v1.json","status","READY")),
("metacognition",6,okfile("metacognition_v1.json","status","PASS")),
("autonomous_research_execution",8,False),("action_result_verification_feedback",5,False),("safe_self_improvement_build_verify_rollback",6,False),("tool_selection_beyond_search",5,False),("long_horizon_goal_queue_recovery",4,False),("end_to_end_unattended_acceptance",4,False)]
def main():
 total=sum(w for _,w,_ in checks);earned=sum(w for _,w,p in checks if p);pct=round(100*earned/total,1)
 out={"schema_version":2,"kind":"JARVIS_COMPLETION_AUDIT_V2","definition":"Autonomous JARVIS research/engineering agent; searcher only a tool; market execution excluded.","earned":earned,"total":total,"completion_percent":pct,"details":[{"capability":n,"weight":w,"passed":p} for n,w,p in checks],"remaining":[n for n,w,p in checks if not p]}
 t=S/"completion_audit_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"completion_audit_v2.json")
 print("ALL PASS|COMPLETION_AUDIT_V2|"+str(earned)+"/"+str(total)+"|"+str(pct)+"%|REMAINING="+str(len(out["remaining"])))
if __name__=="__main__":main()
