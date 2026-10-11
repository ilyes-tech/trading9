#!/usr/bin/env python3
import hashlib,json,pathlib,subprocess,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');A=pathlib.Path(__file__).resolve().parent
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 d=load('autonomy_decision_v1.json');reasons=[]
 if d.get('status')!='READY' or not d.get('decision_id'):reasons.append('DECISION_INVALID')
 if d.get('action_class') not in ('OBSERVE','VERIFY','DESIGN','STATE_UPDATE'):reasons.append('ACTION_NOT_ALLOWLISTED')
 if not isinstance(d.get('expected'),dict) or not d.get('expected'):reasons.append('EXPECTED_MISSING')
 if any(d.get(k) is True for k in ('research_execution_allowed','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed')):reasons.append('FORBIDDEN_CAPABILITY')
 if reasons: print('STOP|FAIL|CAUSAL_AUTONOMY_BRIDGE|'+','.join(reasons));return 3
 old=load('causal_autonomy_bridge_v1.json')
 if old.get('decision_id')==d['decision_id'] and old.get('status')=='PASS' and old.get('feedback_status')=='VERIFIED' and old.get('next_decision')=='CLOSE_AND_ADVANCE':
  print('ALL PASS|CAUSAL_AUTONOMY_BRIDGE|IDEMPOTENT|NEXT=CLOSE_AND_ADVANCE');return 0
 intent={'schema_version':2,'status':'PROPOSED','intent_id':hashlib.sha256(canon({'decision_id':d['decision_id'],'action_class':d['action_class'],'expected':d['expected'],'before':d.get('before') or {}}).encode()).hexdigest(),'action_class':d['action_class'],'before':d.get('before') or {},'expected':d['expected'],'research_execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False};(S/'action_intent_v2.json').write_text(json.dumps(intent,indent=2,sort_keys=True)+'\n')
 if subprocess.run([sys.executable,str(A/'v57_action_contract_v2.py')]).returncode:return 3
 c=load('action_contract_v2.json');obs=d.get('observation')
 if not isinstance(obs,dict) or not obs: print('STOP|FAIL|CAUSAL_AUTONOMY_BRIDGE|OBSERVATION_REQUIRED');return 3
 (S/'action_observation_v2.json').write_text(json.dumps({'schema_version':2,'status':'OBSERVED','action_id':c['action_id'],'observed':obs},indent=2,sort_keys=True)+'\n')
 if subprocess.run([sys.executable,str(A/'v57_action_receipt_v2.py')]).returncode:return 3
 subprocess.run([sys.executable,str(A/'v57_action_feedback_v2.py')]);f=load('action_feedback_v2.json');next_decision='CLOSE_AND_ADVANCE' if f.get('status')=='VERIFIED' else ('REVISE' if f.get('status')=='FAILED' else 'STOP')
 out={'schema_version':1,'kind':'JARVIS_CAUSAL_AUTONOMY_BRIDGE_V1','status':'PASS' if f.get('status')=='VERIFIED' else 'STOPPED','decision_id':d['decision_id'],'action_id':c.get('action_id'),'feedback_id':f.get('feedback_id'),'feedback_status':f.get('status'),'next_decision':next_decision,'research_execution_allowed':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};(S/'causal_autonomy_bridge_v1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(('ALL PASS' if out['status']=='PASS' else 'STOP|FAIL')+'|CAUSAL_AUTONOMY_BRIDGE|'+out['status']+'|NEXT='+next_decision);return 0 if out['status']=='PASS' else (2 if f.get('status')=='FAILED' else 3)
if __name__=='__main__':sys.exit(main())
