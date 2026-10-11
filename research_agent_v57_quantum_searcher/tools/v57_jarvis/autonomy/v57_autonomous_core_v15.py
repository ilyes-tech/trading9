#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");A=R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");PY=R/".venv-research/bin/python"
PRE=("v57_learning_memory_v2.py","v57_reflection_engine_v2.py","v57_failure_diagnosis_v2.py","v57_research_agenda_v3.py")
ACTIVE=("v57_hypothesis_refiner_v3.py","v57_experiment_designer_v3.py","v57_tool_selector_v1.py","v57_executive_v1.py","v57_capability_gap_planner_v1.py","v57_causal_operator_v2.py","v57_executive_v2.py","v57_bounded_research_executor_v3.py","v57_research_feedback_v1.py","v57_action_feedback_v3.py","v57_goal_queue_v2.py","v57_self_improvement_guard_v1.py","v57_metacognition_v2.py","v57_hashchain_journal_v1.py","v57_recovery_checkpoint_v1.py")
BRANCH_TERM=("v57_branch_terminal_v2.py","v57_research_agenda_v3.py","v57_action_feedback_v3.py","v57_recovery_checkpoint_v1.py")
def call(n):
 q=subprocess.run([str(PY),str(A/n)],cwd=R,text=True,capture_output=True,timeout=120);return {"name":n,"ok":q.returncode==0,"out":q.stdout.strip()[-300:],"err":q.stderr.strip()[-300:]}
def seq(ch,names):
 for n in names:
  z=call(n);ch.append(z)
  if not z["ok"]:break
def main():
 S.mkdir(parents=True,exist_ok=True);fd=os.open(S/"core_v15.lock",os.O_CREAT|os.O_RDWR,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALL PASS|AUTONOMOUS_CORE_V15|ALREADY_RUNNING");return
 ch=[call("v57_core_freeze_guard_v1.py")]
 if ch[0]["ok"]:ch.append(call("v57_project_inspect_v1.py"))
 if all(x["ok"] for x in ch):seq(ch,PRE)
 mode="SAFE_STOP"
 if all(x["ok"] for x in ch):
  agenda=json.loads((S/"research_agenda_v3.json").read_text())
  if agenda.get("active") is None:
   seq(ch,("v57_agenda_terminal_v2.py","v57_agenda_replanner_v2.py"))
   if all(x["ok"] for x in ch):
    rp=json.loads((S/"agenda_replanner_v2.json").read_text())
    mode="SAFE_STOP_NO_NOVEL_DIRECTION" if rp.get("decision")=="SAFE_STOP" else "REPLAN_PROPOSED"
  else:
   z=call("v57_hypothesis_refiner_v3.py");ch.append(z)
   if z["ok"]:
    h=json.loads((S/"refined_hypothesis_v1.json").read_text())
    if h.get("status")=="EXHAUSTED":mode="BRANCH_EXHAUSTED";seq(ch,BRANCH_TERM)
    else:mode="ACTIVE_RESEARCH";seq(ch,ACTIVE[1:])
 ok=all(x["ok"] for x in ch)
 if ok and mode=="SAFE_STOP_NO_NOVEL_DIRECTION":phase="EVIDENCE_BOUNDED_SAFE_STOP"
 elif ok and mode=="REPLAN_PROPOSED":phase="REPLAN_PENDING_ADMISSION"
 elif ok:phase="AGENDA_CAUSAL_AUTONOMOUS_RESEARCH"
 else:phase="SAFE_STOP"
 rec={"schema_version":15,"kind":"JARVIS_AUTONOMOUS_CORE_V15","ts_ns":time.time_ns(),"status":"PASS" if ok else "FAIL","mode":mode,"checks":ch,"phase":phase,"searcher_role":"OPTIONAL_TOOL","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"status_v15.tmp";t.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");t.replace(S/"status_v15.json")
 with (S/"journal_v15.jsonl").open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|AUTONOMOUS_CORE_V15|MODE="+mode+"|CHECKS="+str(len(ch))+"|PHASE="+phase)
 if not ok:
  bad=next(x for x in ch if not x["ok"]);print("FAIL_AT="+bad["name"]+"|ERR="+bad["err"][-180:]+"|OUT="+bad["out"][-180:])
if __name__=="__main__":main()
