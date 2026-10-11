import hashlib,json,sqlite3
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous'); DB=S/'research_agenda_v1.sqlite3'
TEMPLATES={'PRESERVE_CONCENTRATION_GATES':'Verify concentration gates remain invariant before any distinct development probe','TEST_ONE_BOUNDED_DISTINCT_HYPOTHESIS':'Evaluate one distinct bounded development hypothesis derived from current failure evidence','IMPROVE_STABILITY_WITHOUT_REPEATING_IDENTICAL_PROBE':'Evaluate a stability-oriented development hypothesis distinct from all completed probes'}
def main():
 c=sqlite3.connect(DB); rows=c.execute("SELECT id,space,objective FROM agenda WHERE status='ACTIVE'").fetchall(); c.close()
 if len(rows)!=1: print('STOP|FAIL|AGENDA_HYPOTHESIS|ACTIVE_COUNT='+str(len(rows))); return
 aid,space,obj=rows[0]; statement=TEMPLATES.get(obj)
 if not statement: print('STOP|FAIL|AGENDA_HYPOTHESIS|UNKNOWN_OBJECTIVE'); return
 hid=hashlib.sha256((aid+'|'+space+'|'+statement).encode()).hexdigest()
 out={'schema_version':1,'kind':'JARVIS_AGENDA_HYPOTHESIS_V1','status':'READY','agenda_id':aid,'space':space,'objective':obj,'hypothesis_id':hid,'hypothesis':statement,'experiment_class':'GATE_AUDIT' if obj=='PRESERVE_CONCENTRATION_GATES' else 'BOUNDED_DEVELOPMENT_PROBE','candidate_cap':0 if obj=='PRESERVE_CONCENTRATION_GATES' else 4,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'rule':'DISTINCT; BOUNDED; FAIL_CLOSED'}
 t=S/'agenda_hypothesis_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'agenda_hypothesis_v1.json')
 print('ALL PASS|AGENDA_HYPOTHESIS|'+obj+'|CLASS='+out['experiment_class'])
if __name__=='__main__': main()
