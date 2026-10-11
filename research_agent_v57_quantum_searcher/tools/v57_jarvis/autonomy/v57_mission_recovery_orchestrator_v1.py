#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';PY=R/'.venv-research/bin/python'
def main():
 kind=(sys.argv[1] if len(sys.argv)>1 else 'STATUS').upper()
 d=subprocess.run([str(PY),str(A/'v57_recovery_decider_v1.py'),kind],cwd=R,text=True,capture_output=True,timeout=60)
 if d.returncode: print('STOP|FAIL|RECOVERY_ORCHESTRATOR|DECIDER');raise SystemExit(1)
 state=json.loads((Path('/home/trading/.local/state/tradingai/jarvis-autonomous')/'recovery_decision_v1.json').read_text())
 if state['decision']=='DIAGNOSE_BEFORE_RETRY':
  q=subprocess.run([str(PY),str(A/'v57_failure_diagnosis_v2.py')],cwd=R,text=True,capture_output=True,timeout=120)
  if q.returncode: print('STOP|FAIL|RECOVERY_ORCHESTRATOR|DIAGNOSIS');raise SystemExit(1)
  action='DIAGNOSED_RETRY_BLOCKED'
 else: action=state['decision']
 print(json.dumps({'status':'PASS','kind':'JARVIS_MISSION_RECOVERY_ORCHESTRATOR_V1','mission_kind':kind,'action':action,'retry_allowed':state['retry_allowed'],'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'mutation_allowed':False},sort_keys=True))
if __name__=='__main__':main()
