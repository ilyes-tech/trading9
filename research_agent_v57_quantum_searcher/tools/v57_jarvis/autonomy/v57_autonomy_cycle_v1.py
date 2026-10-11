import json,os,subprocess,sys
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab")
A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy"
STATE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
SUP=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/jarvis_v438_supervisor_v1.py"
PYTHON=ROOT/".venv-research/bin/python"
def run(script):
 p=subprocess.run([str(PYTHON),str(script)],cwd=ROOT,text=True,capture_output=True,timeout=120)
 if p.returncode: raise RuntimeError(script.name+":"+p.stderr[-1000:])
 return p.stdout.strip()
def main():
 safety=run(SUP)
 if not safety.startswith("ALL PASS|"): raise RuntimeError("SAFETY_NOT_PASS")
 mem=run(A/"v57_learning_memory_v1.py")
 ref=run(A/"v57_reflection_engine_v1.py")
 d=json.loads((STATE/"reflection_v1.json").read_text())
 # V1 is intentionally observation/reflection only. Heavy search remains externally gated.
 if d.get("next_action")=="CRITIQUE_DEEP_REJECTION":
  decision="AWAIT_CRITIQUE_EXECUTOR_V2"
 else: decision="AWAIT_HYPOTHESIS_PLANNER_V2"
 out={"schema_version":1,"kind":"JARVIS_AUTONOMY_CYCLE_V1","status":"PASS","safety":safety,"memory":json.loads(mem),"reflection":d,"decision":decision,"research_execution":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=STATE/"autonomy_cycle_v1.tmp"; t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); t.replace(STATE/"autonomy_cycle_v1.json")
 print("ALL PASS|AUTONOMY_CYCLE_V1|"+decision+"|NO_ORDERS|NO_MT5|NO_HOLDOUT")
if __name__=="__main__": main()
