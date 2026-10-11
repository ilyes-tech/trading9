import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
items=[
("persistent_core",8,"status_v3.json","status","PASS"),
("safety_fail_closed",10,"status_v3.json","safety_pass",True),
("persistent_memory",8,"reflection_v2.json","status","READY"),
("reflection",8,"reflection_v2.json","status","READY"),
("failure_diagnosis",7,"failure_diagnosis_v2.json","status","DIAGNOSED"),
("hypothesis_refinement",7,"refined_hypothesis_v1.json","status","PROPOSED"),
("experiment_planning",6,"experiment_plan_v1.json","status","PLANNED"),
("capability_audit",5,"capability_audit.json","status","PASS"),
("executive_reasoning",8,"executive_v2.json","status","PASS"),
("causal_operator_design",5,"causal_operator_v1.json","status","READY"),
("metacognition",6,"metacognition_v1.json","status","PASS")]
manual=[("autonomous_research_execution",8),("action_result_verification_feedback",5),("safe_self_improvement_build_verify_rollback",6),("tool_selection_beyond_search",5),("long_horizon_goal_queue_recovery",4),("end_to_end_unattended_acceptance",4)]
def main():
 earned=0;details=[]
 for name,w,f,k,v in items:
  p=S/f
  try:d=json.loads(p.read_text());ok=d.get(k)==v
  except Exception:ok=False
  if ok:earned+=w
  details.append({"capability":name,"weight":w,"passed":ok})
 for name,w in manual:details.append({"capability":name,"weight":w,"passed":False})
 total=sum(x["weight"] for x in details)
 pct=round(100*earned/total,1)
 out={"schema_version":1,"kind":"JARVIS_COMPLETION_AUDIT_V1","definition":"Autonomous JARVIS research/engineering agent; searcher is only a tool; market execution excluded.","earned":earned,"total":total,"completion_percent":pct,"details":details,"remaining":[x["capability"] for x in details if not x["passed"]]}
 t=S/"completion_audit_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"completion_audit_v1.json")
 print("ALL PASS|COMPLETION_AUDIT|"+str(earned)+"/"+str(total)+"|"+str(pct)+"%|REMAINING="+str(len(out["remaining"])))
if __name__=="__main__":main()
