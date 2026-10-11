import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
REQ=[("status_v3.json","status","PASS"),("reflection_v2.json","status","READY"),("failure_diagnosis_v2.json","status","DIAGNOSED"),("refined_hypothesis_v1.json","status","PROPOSED"),("experiment_plan_v1.json","status","PLANNED"),("executive_v2.json","status","PASS"),("metacognition_v1.json","status","PASS"),("action_feedback_v1.json","status","VERIFIED"),("goal_queue_v1.json","status","READY"),("tool_selection_v1.json","status","PASS"),("self_improvement_guard_v1.json","status","PASS")]
def main():
 checks=[]
 for f,k,v in REQ:
  try:d=json.loads((S/f).read_text());ok=d.get(k)==v
  except Exception:ok=False
  checks.append({"artifact":f,"passed":ok})
 ok=all(x["passed"] for x in checks)
 out={"schema_version":1,"kind":"JARVIS_UNATTENDED_ACCEPTANCE_V1","status":"PASS" if ok else "FAIL","checks":checks,
 "scope":"COGNITIVE_AUTONOMY_NO_MARKET_EXECUTION","cycles_required":3,"current_verified_cycle":1,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"unattended_acceptance_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"unattended_acceptance_v1.json")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|UNATTENDED_ACCEPTANCE_V1|ARTIFACTS="+str(len(checks))+"|CYCLE=1/3")
if __name__=="__main__":main()
