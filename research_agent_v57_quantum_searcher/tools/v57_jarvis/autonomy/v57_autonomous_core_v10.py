#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");A=R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");PY=R/".venv-research/bin/python"
PRE=("v57_research_agenda_v1.py","v57_learning_memory_v2.py","v57_reflection_engine_v2.py","v57_failure_diagnosis_v2.py","v57_hypothesis_refiner_v2.py"); NORMAL=("v57_experiment_designer_v1.py","v57_tool_selector_v1.py","v57_executive_v1.py","v57_capability_gap_planner_v1.py","v57_causal_operator_v1.py","v57_executive_v2.py","v57_bounded_research_executor_v2.py","v57_research_feedback_v1.py","v57_action_feedback_v1.py","v57_goal_queue_v2.py","v57_self_improvement_guard_v1.py","v57_metacognition_v1.py","v57_hashchain_journal_v1.py","v57_recovery_checkpoint_v1.py")
def call(p):
 q=subprocess.run([str(PY),str(p)],cwd=R,text=True,capture_output=True,timeout=120);return {"name":Path(p).name,"ok":q.returncode==0,"out":q.stdout.strip()[-300:],"err":q.stderr.strip()[-300:]}
def main():
 S.mkdir(parents=True,exist_ok=True);fd=os.open(S/"core_v7.lock",os.O_CREAT|os.O_RDWR,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALL PASS|AUTONOMOUS_CORE_V10|ALREADY_RUNNING");return
 guard=A/"v57_core_freeze_guard_v1.py";sup=A/"v57_project_inspect_v1.py";checks=[call(guard)]
 if checks[0]["ok"]:checks.append(call(sup))
 if all(x["ok"] for x in checks):
  for n in PRE:
   z=call(A/n);checks.append(z)
   if not z["ok"]:break
  if all(x["ok"] for x in checks):
   h=json.loads((S/"refined_hypothesis_v1.json").read_text())
   seq=("v57_branch_terminal_v1.py","v57_goal_queue_v2.py","v57_metacognition_v1.py","v57_recovery_checkpoint_v1.py") if h.get("status")=="EXHAUSTED" else NORMAL
   for n in seq:
    z=call(A/n);checks.append(z)
    if not z["ok"]:break
 ok=all(x["ok"] for x in checks);rec={"schema_version":10,"kind":"JARVIS_AUTONOMOUS_CORE_V10","ts_ns":time.time_ns(),"status":"PASS" if ok else "FAIL","checks":checks,"phase":"FULL_AUTONOMOUS_RESEARCH_LOOP" if ok else "SAFE_STOP","searcher_role":"OPTIONAL_TOOL","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"status_v10.tmp";t.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");t.replace(S/"status_v10.json")
 with (S/"journal_v10.jsonl").open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 acc=call(A/"v57_unattended_acceptance_v5.py");aud=call(A/"v57_completion_audit_v7.py")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|AUTONOMOUS_CORE_V10|CHECKS="+str(len(checks))+"|"+acc["out"].splitlines()[-1]+"|"+aud["out"].splitlines()[-1])
if __name__=="__main__":main()
