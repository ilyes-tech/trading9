import json,sqlite3,time
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def main():
 h=json.loads((S/'agenda_hypothesis_v1.json').read_text());d=json.loads((S/'agenda_probe_result_v1.json').read_text())
 if d.get('hypothesis_id')!=h.get('hypothesis_id') or d.get('agenda_id')!=h.get('agenda_id'):print('STOP|FAIL|AGENDA_DECIDER|EVIDENCE_MISMATCH');return
 records=d['result']['records'];pre=sum(r.get('status')=='PREFILTER_REJECT' for r in records);ev=sum(r.get('status')=='EVALUATED' for r in records);exact=sum(bool((r.get('result') or {}).get('exact_pass')) for r in records)
 decision='COMPLETED' if exact==0 else 'REQUIRES_DEEP_VALIDATION';lesson='BOUNDED_DISTINCT_PROBE_NO_EXACT_PASS' if exact==0 else 'EXACT_PASS_FOUND_NOT_PROMOTED'
 c=sqlite3.connect(S/'research_agenda_v1.sqlite3');c.execute("UPDATE agenda SET status=? WHERE id=? AND status='ACTIVE'",('COMPLETED' if exact==0 else 'REPLAN',h['agenda_id']));c.commit();c.close()
 out={'schema_version':1,'kind':'JARVIS_AGENDA_DECISION_V1','status':'DECIDED','agenda_id':h['agenda_id'],'hypothesis_id':h['hypothesis_id'],'decision':decision,'lesson':lesson,'candidates':len(records),'prefilter_reject':pre,'evaluated':ev,'exact_pass':exact,'next_action':'SELECT_NEXT_AGENDA_OBJECTIVE' if exact==0 else 'DEEP_VALIDATION_REQUIRED_BEFORE_ANY_FURTHER_ACTION','orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 t=S/'agenda_decision_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'agenda_decision_v1.json');
 with (S/'agenda_learning_v1.jsonl').open('a') as f:f.write(json.dumps({'ts_ns':time.time_ns(),**out},sort_keys=True)+'\n')
 print('ALL PASS|AGENDA_DECIDER|'+decision+'|EXACT_PASS='+str(exact)+'|AUTO_PROMOTION=FALSE')
if __name__=='__main__':main()
