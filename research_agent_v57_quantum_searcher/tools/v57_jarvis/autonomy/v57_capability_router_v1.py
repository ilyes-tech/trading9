import json,subprocess
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');PY=R/'.venv-research/bin/python'
CAPS={'HEALTH':'v57_autonomous_core_v6.py','AGENDA':'v57_agenda_cycle_v1.py','GOALS':'v57_goal_queue_v2.py','TOOLS':'v57_tool_selector_v1.py','CAPABILITY_GAPS':'v57_capability_gap_planner_v1.py','REFLECTION':'v57_reflection_engine_v2.py','STRATEGY_POOL':'v57_dynamic_verified_pool_v1.py'}
def run(cap):
 if cap not in CAPS:return {'capability':cap,'status':'DENIED','reason':'NOT_ALLOWLISTED'}
 p=subprocess.run([str(PY),str(A/CAPS[cap])],cwd=R,text=True,capture_output=True,timeout=180);lines=p.stdout.strip().splitlines()
 return {'capability':cap,'status':'PASS' if p.returncode==0 else 'FAIL','rc':p.returncode,'output':lines[-1] if lines else ''}
def main():
 import sys;cap=(sys.argv[1] if len(sys.argv)>1 else '').upper();o=run(cap);print(json.dumps(o,sort_keys=True));raise SystemExit(0 if o['status']=='PASS' else 1)
if __name__=='__main__':main()
