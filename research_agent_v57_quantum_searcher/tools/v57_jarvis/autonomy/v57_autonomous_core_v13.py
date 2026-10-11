#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");A=R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");PY=R/".venv-research/bin/python"
PRE=("v57_learning_memory_v2.py","v57_reflection_engine_v2.py","v57_failure_diagnosis_v2.py","v57_research_agenda_v2.py","v57_hypothesis_refiner_v3.py")
NORMAL=("v57_experiment_designer_v2.py","v57_tool_selector_v1.py","v57_executive_v1.py","v57_capability_gap_planner_v1.py","v57_causal_operator_v2.py","v57_executive_v2.py","v57_bounded_research_executor_v3.py","v57_research_feedback_v1.py","v57_action_feedback_v3.py","v57_goal_queue_v2.py","v57_self_improvement_guard_v1.py","v57_metacognition_v2.py","v57_hashchain_journal_v1.py","v57_recovery_checkpoint_v1.py")
TERMINAL=("v57_branch_terminal_v2.py","v57_research_agenda_v2.py","v57_goal_queue_v2.py","v57_metacognition_v2.py","v57_action_feedback_v3.py","v57_recovery_checkpoint_v1.py")
def call(p):
 q=subprocess.run([str(PY),str(p)],cwd=R,text=True,capture_output=True,timeout=120);return {"name":Path(p).name,"ok":q.returncode==0,"out":q.stdout.strip()[-300:],"err":q.stderr.strip()[-300:]}
def main():
 S.mkdir(parents=True,exist_ok=True);fd=os.open(S/"core_v13.lock",os.O_CREAT|os.O_RDWR,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALL PASS|AUTONOMOUS_CORE_V13|ALREADY_RUNNING");return
 checks=[call(A/"v57_core_freeze_guard_v1.py")]
 if checks[0]["ok"]:checks.append(call(A/"v57_project_inspect_v1.py"))
 if all(x["ok"] for x in checks):
  for n in PRE:
   z=call(A/n);checks.append(z)
   if not z["ok"]:break
 if all(x["ok"] for x in checks):
  h=json.loads((S/"refined_hypothesis_v1.json").read_text());seq=TERMINAL if h.get("status")=="EXHAUSTED" else NORMAL
  for n in seq:
   z=call(A/n);checks.append(z)
   if not z["ok"]:break
 ok=all(x["ok"] for x in checks);rec={"schema_version":13,"kind":"JARVIS_AUTONOMOUS_CORE_V13","ts_ns":time.time_ns(),"status":"PASS" if ok else "FAIL","checks":checks,"phase":"AGENDA_CAUSAL_AUTONOMOUS_RESEARCH" if ok else "SAFE_STOP","searcher_role":"OPTIONAL_TOOL","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"status_v13.tmp";t.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");t.replace(S/"status_v13.json")
 with (S/"journal_v13.jsonl").open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|AUTONOMOUS_CORE_V13|CHECKS="+str(len(checks))+"|PHASE="+rec["phase"])
 if not ok:
  bad=next(x for x in checks if not x["ok"]);print("FAIL_AT="+bad["name"]+"|ERR="+bad["err"][-180:]+"|OUT="+bad["out"][-180:])
if __name__=="__main__":main()
