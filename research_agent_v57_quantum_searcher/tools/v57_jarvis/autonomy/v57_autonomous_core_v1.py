#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab")
A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
STATE=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
SAFE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
PY=ROOT/".venv-research/bin/python"
LOCK=STATE/"core.lock"; JOURNAL=STATE/"journal.jsonl"; SNAP=STATE/"status.json"
SCRIPTS=("v57_learning_memory_v1.py","v57_reflection_engine_v1.py","v57_failure_diagnosis_v1.py")
def atomic(p,x):
 p.parent.mkdir(parents=True,exist_ok=True); t=Path(str(p)+".tmp"); t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n"); os.replace(t,p)
def call(name,timeout=120):
 q=subprocess.run([str(PY),str(A/name)],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
 return {"name":name,"ok":q.returncode==0,"out":q.stdout.strip()[-1000:],"err":q.stderr.strip()[-1000:]}
def resources():
 la=os.getloadavg()[0]; cp=os.cpu_count() or 1; av=os.sysconf("SC_AVPHYS_PAGES")*os.sysconf("SC_PAGE_SIZE")
 return {"load1":la,"cpus":cp,"load_per_cpu":la/cp,"available_memory_mb":round(av/1048576)}
def run():
 STATE.mkdir(parents=True,exist_ok=True)
 fd=os.open(LOCK,os.O_CREAT|os.O_RDWR,0o600)
 try: fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError: print("ALL PASS|AUTONOMOUS_CORE|ALREADY_RUNNING"); return 0
 checks=[]
 sup=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/jarvis_v438_supervisor_v1.py"
 q=subprocess.run([str(PY),str(sup)],cwd=ROOT,text=True,capture_output=True,timeout=60)
 safety=q.returncode==0 and "ALL PASS|" in q.stdout
 if safety:
  for s in SCRIPTS:
   if s=="v57_failure_diagnosis_v1.py" and not (SAFE/"deep_evidence_v1.json").exists(): continue
   checks.append(call(s))
 r=resources(); healthy=safety and all(x["ok"] for x in checks)
 phase="LEARN_REFLECT_PLAN" if healthy else "SAFE_STOP"
 next_action="MAINTAIN_COGNITIVE_LOOP" if healthy else "REPAIR_FAILED_CHECK"
 rec={"schema_version":1,"kind":"JARVIS_AUTONOMOUS_CORE_V1","ts_ns":time.time_ns(),"status":"PASS" if healthy else "FAIL",
 "phase":phase,"next_action":next_action,"safety_pass":safety,"checks":checks,"resources":r,
 "heavy_research_launched":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 atomic(SNAP,rec)
 with JOURNAL.open("a") as f: f.write(json.dumps(rec,sort_keys=True)+"\n")
 print(("ALL PASS" if healthy else "STOP|FAIL")+"|JARVIS_AUTONOMOUS_CORE|"+phase+"|"+next_action)
 return 0 if healthy else 1
if __name__=="__main__": raise SystemExit(run())
