import sqlite3,subprocess
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');PY=R/'.venv-research/bin/python'
def run(n):
 q=subprocess.run([str(PY),str(A/n)],cwd=R,text=True,capture_output=True,timeout=120);o=q.stdout.strip().splitlines();print(o[-1] if o else n+'|NO_OUTPUT');return q.returncode==0 and not any(x.startswith('STOP|FAIL') for x in o)
def counts():
 c=sqlite3.connect(S/'research_agenda_v1.sqlite3');d=dict(c.execute('SELECT status,count(*) FROM agenda GROUP BY status').fetchall());c.close();return d
def main():
 print("STOP|FAIL|AGENDA_CYCLE|LEGACY_AGENDA_BLOCKED|REQUIRES_INDEPENDENT_ADMISSION")
 raise SystemExit(3)
 if not run('v57_agenda_replanner_v1.py'):print('STOP|FAIL|AGENDA_CYCLE|REPLANNER');return
 d=counts()
 if not d.get('ACTIVE') and not d.get('PENDING'):print('ALL PASS|AGENDA_CYCLE|IDLE|AGENDA_COMPLETE|ORDERS=BLOCKED|HOLDOUT=BLOCKED');return
 if not d.get('ACTIVE') and not run('v57_agenda_orchestrator_v1.py'):print('STOP|FAIL|AGENDA_CYCLE|ORCHESTRATOR');return
 if not run('v57_agenda_hypothesis_v1.py'):print('STOP|FAIL|AGENDA_CYCLE|HYPOTHESIS');return
 for n in ('v57_agenda_gate_audit_v1.py','v57_agenda_probe_executor_v1.py'):
  if not run(n):print('STOP|FAIL|AGENDA_CYCLE|'+n);return
 print('ALL PASS|AGENDA_CYCLE|SAFE_BOUNDED|ORDERS=BLOCKED|HOLDOUT=BLOCKED')
if __name__=='__main__':main()
