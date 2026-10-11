#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 c=load('action_contract_v2.json');o=load('action_observation_v2.json');reasons=[]
 if c.get('status')!='SEALED' or not c.get('action_id'):reasons.append('CONTRACT_INVALID')
 if o.get('status')!='OBSERVED' or o.get('action_id')!=c.get('action_id'):reasons.append('OBSERVATION_INVALID')
 observed=o.get('observed')
 if not isinstance(observed,dict) or not observed:reasons.append('OBSERVED_RESULT_MISSING')
 oh=hashlib.sha256(canon(o).encode()).hexdigest() if o else None
 out={'schema_version':2,'kind':'JARVIS_ACTION_RECEIPT_V2','status':'OBSERVED' if not reasons else 'DENIED','action_id':c.get('action_id'),'observation_sha256':oh,'observed':observed or {},'reasons':reasons,'research_execution_allowed':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};t=S/'action_receipt_v2.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'action_receipt_v2.json');print(('ALL PASS' if not reasons else 'DENIED')+'|ACTION_RECEIPT_V2|'+out['status']);return 0 if not reasons else 3
if __name__=='__main__':sys.exit(main())
