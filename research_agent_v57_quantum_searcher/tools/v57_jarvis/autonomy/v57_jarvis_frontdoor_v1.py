import json,subprocess,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');PY=R/'.venv-research/bin/python'
MC=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_mission_controller_v2.py'
def main():
 a=sys.argv[1:];q=' '.join(a).strip()
 if not q: print('STOP|FAIL|JARVIS_FRONTDOOR_V1|EMPTY');raise SystemExit(2)
 p=subprocess.run([str(PY),str(MC),*a],cwd=R)
 raise SystemExit(p.returncode)
if __name__=='__main__':main()
