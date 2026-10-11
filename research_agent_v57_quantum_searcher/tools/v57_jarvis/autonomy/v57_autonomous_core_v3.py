#!/usr/bin/env python3
import fcntl,json,os,subprocess,time
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab");A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";STATE=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");PY=ROOT/".venv-research/bin/python"
PIPE=("v57_learning_memory_v2.py","v57_reflection_engine_v2.py","v57_failure_diagnosis_v2.py","v57_hypothesis_refiner_v1.py","v57_experiment_designer_v1.py","v57_capability_audit_v1.py","v57_executive_v1.py","v57_capability_gap_planner_v1.py","v57_causal_operator_v1.py","v57_executive_v2.py","v57_metacognition_v1.py")
def call(p,timeout=120):
 q=subprocess.run([str(PY),str(p)],cwd=ROOT,text=True,capture_output=True,timeout=timeout)
 return {"name":Path(p).name,"ok":q.returncode==0,"out":q.stdout.strip()[-400:],"err":q.stderr.strip()[-400:]}
def atomic(p,x):
 t=Path(str(p)+".tmp");t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");os.replace(t,p)
def resources():
 m=next(int(x.split()[1])//1024 for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:"));la=os.getloadavg()[0];cp=os.cpu_count() or 1
 return {"available_memory_mb":m,"load1":la,"cpus":cp,"load_per_cpu":round(la/cp,3)}
def main():
 STATE.mkdir(parents=True,exist_ok=True);fd=os.open(STATE/"core_v3.lock",os.O_CREAT|os.O_RDWR,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print("ALL PASS|AUTONOMOUS_CORE_V3|ALREADY_RUNNING");return 0
 sup=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/jarvis_v438_supervisor_v1.py";checks=[call(sup,60)]
 safety=checks[0]["ok"] and "ALL PASS|" in checks[0]["out"]
 if safety:
  for s in PIPE:
   z=call(A/s);checks.append(z)
   if not z["ok"]:break
 r=resources();healthy=safety and all(x["ok"] for x in checks);compute="PASS" if r["available_memory_mb"]>=2048 and r["load_per_cpu"]<=0.75 else "WAIT"
 meta=json.loads((STATE/"metacognition_v1.json").read_text()) if (STATE/"metacognition_v1.json").exists() else {}
 rec={"schema_version":3,"kind":"JARVIS_AUTONOMOUS_CORE_V3","ts_ns":time.time_ns(),"status":"PASS" if healthy else "FAIL","phase":"AUTONOMOUS_COGNITIVE_LOOP" if healthy else "SAFE_STOP",
 "checks":checks,"resources":r,"compute_gate":compute,"metacognition":meta.get("assessment","UNKNOWN"),"next_action":meta.get("next_action","REPAIR"),
 "searcher_role":"OPTIONAL_TOOL","market_execution":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 atomic(STATE/"status_v3.json",rec)
 with (STATE/"journal_v3.jsonl").open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 print(("ALL PASS" if healthy else "STOP|FAIL")+"|AUTONOMOUS_CORE_V3|"+rec["phase"]+"|META="+rec["metacognition"]+"|COMPUTE="+compute)
 return 0 if healthy else 1
if __name__=="__main__":raise SystemExit(main())
