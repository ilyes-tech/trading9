#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 i=load('action_intent_v2.json');reasons=[]
 if i.get('status')!='PROPOSED' or not i.get('intent_id'):reasons.append('INTENT_INVALID')
 expected=i.get('expected')
 if not isinstance(expected,dict) or not expected:reasons.append('EXPECTED_RESULT_MISSING')
 if i.get('action_class') not in ('OBSERVE','VERIFY','DESIGN','STATE_UPDATE'):reasons.append('ACTION_CLASS_NOT_ALLOWED')
 if any(i.get(k) is True for k in ('research_execution_allowed','orders_allowed','mt5_allowed','holdout_allowed','auto_promotion_allowed')):reasons.append('FORBIDDEN_CAPABILITY')
 before=i.get('before') or {}; aid=hashlib.sha256(canon({'intent_id':i.get('intent_id'),'action_class':i.get('action_class'),'expected':expected,'before':before}).encode()).hexdigest() if not reasons else None
 out={'schema_version':2,'kind':'JARVIS_ACTION_CONTRACT_V2','status':'SEALED' if not reasons else 'DENIED','action_id':aid,'intent_id':i.get('intent_id'),'action_class':i.get('action_class'),'expected':expected or {},'before':before,'reasons':reasons,'research_execution_allowed':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};t=S/'action_contract_v2.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'action_contract_v2.json');print(('ALL PASS' if not reasons else 'DENIED')+'|ACTION_CONTRACT_V2|'+out['status']);return 0 if not reasons else 3
if __name__=='__main__':sys.exit(main())
