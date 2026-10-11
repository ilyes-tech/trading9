import json,sqlite3,subprocess
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');PY=R/'.venv-research/bin/python'
def main():
 h=json.loads((S/'agenda_hypothesis_v1.json').read_text())
 if h.get('experiment_class')!='GATE_AUDIT': print('ALL PASS|AGENDA_GATE_AUDIT|SKIP|NOT_GATE_AUDIT'); return
 q=subprocess.run([str(PY),str(R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/kernel/v57_jarvis_safety_v1.py'),'--self-check'],cwd=R,text=True,capture_output=True,timeout=30)
 ok=q.returncode==0 and 'FAIL_CLOSED=PASS' in q.stdout and 'FROZEN_DRIFT=0' in q.stdout
 out={'schema_version':1,'kind':'JARVIS_AGENDA_GATE_AUDIT_V1','agenda_id':h['agenda_id'],'hypothesis_id':h['hypothesis_id'],'status':'PASS' if ok else 'FAIL','evidence':q.stdout.strip()[-2000:],'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
 t=S/'agenda_gate_audit_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'agenda_gate_audit_v1.json')
 if ok:
  c=sqlite3.connect(S/'research_agenda_v1.sqlite3');c.execute("UPDATE agenda SET status='COMPLETED' WHERE id=? AND status='ACTIVE'",(h['agenda_id'],));c.commit();c.close();print('ALL PASS|AGENDA_GATE_AUDIT|COMPLETED')
 else: print('STOP|FAIL|AGENDA_GATE_AUDIT|SAFETY_CHECK')
if __name__=='__main__': main()
