#!/usr/bin/env python3
import subprocess
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';PY=R/'.venv-research/bin/python'
STEPS=('v57_mission_outcome_memory_v1.py','v57_mission_memory_recall_v1.py','v57_recovery_decider_v1.py','v57_hashchain_journal_v1.py')
def main():
 results=[]
 for name in STEPS:
  q=subprocess.run([str(PY),str(A/name)],cwd=R,text=True,capture_output=True,timeout=60)
  results.append((name,q.returncode,q.stdout.strip().splitlines()[-1] if q.stdout.strip() else q.stderr.strip()[-200:]))
  if q.returncode: print('STOP|FAIL|MISSION_LEARNING_CYCLE|'+name);raise SystemExit(1)
 print('ALL PASS|MISSION_LEARNING_CYCLE|STEPS='+str(len(results))+'|MUTATION=FALSE|ORDERS=FALSE')
if __name__=='__main__':main()
