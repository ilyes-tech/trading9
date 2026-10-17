#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 a=load('search_authorization_v1.json');o=load('bounded_objective_v1.json'); reasons=[]
 if a.get('authorized') is not True: reasons.append('AUTHORIZATION_DENIED')
 if a.get('status') != 'AUTHORIZED' or a.get('reasons') != []:
  reasons.append('UNTRUSTED_AUTHORIZATION_DOCUMENT')
 # A JSON authorization flag is not independent scientific authority.
 # Keep this secondary gate closed until a separately approved, verified
 # signature-bound BTC/ETH experiment permission has been implemented.
 reasons.append('INDEPENDENT_SCIENTIFIC_EXECUTION_AUTHORITY_NOT_PROVISIONED')
 if a.get('execution_started') is not False: reasons.append('AUTHORIZATION_ALREADY_CONSUMED')
 budget=a.get('max_candidates',0)
 if type(budget) is not int or budget != 1: reasons.append('ONE_CANDIDATE_EXPERIMENT_BUDGET_REQUIRED')
 oid=o.get('objective_id')
 if not oid: reasons.append('OBJECTIVE_ID_MISSING')
 token=hashlib.sha256((str(oid)+'|'+str(budget)).encode()).hexdigest() if oid else None
 ledger=load('search_execution_ledger_v1.json'); used=set(ledger.get('consumed_tokens') or [])
 if token in used: reasons.append('TOKEN_ALREADY_CONSUMED')
 allowed=not reasons
 out={'schema_version':1,'kind':'JARVIS_SEARCH_EXECUTION_GATE_V1','status':'READY' if allowed else 'DENIED','ready':allowed,'objective_id':oid,'budget_candidates':budget if allowed else 0,'execution_token':token if allowed else None,'reasons':reasons,'search_process_started':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()}
 p=S/'search_execution_gate_v1.json';q=S/'search_execution_gate_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(p)
 print(('ALL PASS' if allowed else 'DENIED')+'|SEARCH_EXEC_GATE_V1|READY='+str(allowed).upper()+'|BUDGET='+str(out['budget_candidates'])+'|PROCESS=NO|REASONS='+(','.join(reasons) if reasons else 'NONE'));return 0 if allowed else 3
if __name__=='__main__':sys.exit(main())
