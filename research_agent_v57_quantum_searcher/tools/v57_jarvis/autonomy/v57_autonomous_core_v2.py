#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab");A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
STATE=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");PY=ROOT/".venv-research/bin/python"
LOCK=STATE/"core_v2.lock";JOURNAL=STATE/"journal_v2.jsonl";SNAP=STATE/"status_v2.json"
def atomic(p,x):p.parent.mkdir(parents=True,exist_ok=True);t=Path(str(p)+".tmp");t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");os.replace(t,p)
def call(p,timeout=120):
 q=subprocess.run([str(PY),str(p)],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
 return {"name":Path(p).name,"ok":q.returncode==0,"out":q.stdout.strip()[-500:],"err":q.stderr.strip()[-500:]}
def resources():
 m=0
 for line in Path("/proc/meminfo").read_text().splitlines():
  if line.startswith("MemAvailable:"):m=int(line.split()[1])//1024
 la=os.getloadavg()[0];cp=os.cpu_count() or 1
 return {"load1":la,"cpus":cp,"load_per_cpu":round(la/cp,3),"available_memory_mb":m}
def run():
 STATE.mkdir(parents=True,exist_ok=True);fd=os.open(LOCK,os.O_CREAT|os.O_RDWR,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALL PASS|AUTONOMOUS_CORE_V2|ALREADY_RUNNING");return 0
 checks=[];sup=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/jarvis_v438_supervisor_v1.py"
 q=call(sup,60);checks.append(q);safety=q["ok"] and "ALL PASS|" in q["out"]
 if safety:
  for s in ("v57_learning_memory_v2.py","v57_reflection_engine_v2.py","v57_failure_diagnosis_v2.py","v57_hypothesis_refiner_v1.py","v57_experiment_designer_v1.py","v57_capability_audit_v1.py"):checks.append(call(A/s))
 r=resources();healthy=safety and all(x["ok"] for x in checks)
 compute_ok=r["available_memory_mb"]>=2048 and r["load_per_cpu"]<=0.75
 phase="COGNITIVE_IDLE" if healthy else "SAFE_STOP"
 rec={"schema_version":2,"kind":"JARVIS_AUTONOMOUS_CORE_V2","ts_ns":time.time_ns(),"status":"PASS" if healthy else "FAIL",
 "phase":phase,"next_action":"OBSERVE_LEARN_REFLECT_PLAN_VERIFY","safety_pass":safety,"checks":checks,"resources":r,
 "compute_gate":"PASS" if compute_ok else "WAIT","autonomous_research_launch":False,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 atomic(SNAP,rec)
 with JOURNAL.open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 print(("ALL PASS" if healthy else "STOP|FAIL")+"|AUTONOMOUS_CORE_V2|"+phase+"|COMPUTE="+rec["compute_gate"]+"|NO_SEARCH_LAUNCHED")
 return 0 if healthy else 1
if __name__=="__main__":raise SystemExit(run())
