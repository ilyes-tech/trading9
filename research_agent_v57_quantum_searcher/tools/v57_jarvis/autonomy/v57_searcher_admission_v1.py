#!/usr/bin/env python3
import hashlib,importlib.util,json,re,sys
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher')
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
V=R/'tools/v57_jarvis/v3/registry/v57_deployment_fidelity_verify_v1.py'
PROOFS=R/'work/deployment_fidelity_v1/proofs'
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def load():
 spec=importlib.util.spec_from_file_location('fv',V);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify_record_proof(record):
 try:
  if not isinstance(record,dict) or record.get('status')!='EVALUATED':return False,'INVALID_RECORD'
  strategy=record['strategy'];sid=strategy['strategy_id'];result=record['result'];fidelity=record['post_search_fidelity']
  if not isinstance(sid,str) or re.fullmatch(r'[0-9a-f]{64}',sid) is None:return False,'INVALID_STRATEGY_ID'
  if result.get('exact_pass') is not True:return False,'SEARCH_FAILED'
  if fidelity.get('strategy_id')!=sid or fidelity.get('deployment_exact_pass') is not True:return False,'FIDELITY_FAILED'
  proof=json.loads((PROOFS/(sid+'.json')).read_text())
  body={k:v for k,v in proof.items() if k!='proof_sha256'}
  if hashlib.sha256(canon(body).encode()).hexdigest()!=proof.get('proof_sha256'):return False,'PROOF_HASH_MISMATCH'
  if hashlib.sha256(canon(strategy).encode()).hexdigest()!=proof.get('strategy_sha256'):return False,'STRATEGY_HASH_MISMATCH'
  verdict=proof['verdict'];ri=verdict['research_integrity']
  if proof.get('kind')!='V57_DEPLOYMENT_FIDELITY_PROOF_V1' or proof.get('strategy_id')!=sid or verdict.get('strategy_id')!=sid:return False,'IDENTITY_MISMATCH'
  if fidelity.get('proof_sha256')!=proof.get('proof_sha256') or fidelity.get('strategy_sha256')!=proof.get('strategy_sha256'):return False,'FIDELITY_HASH_MISMATCH'
  if verdict.get('conclusion')!='DEPLOYMENT_VERIFIED' or verdict.get('fixed_exact_pass') is not True or verdict.get('search_exact_pass') is not True:return False,'FIXED_REPLAY_FAILED'
  if verdict.get('promotion_allowed') is not True or proof.get('promotion_allowed') is not True:return False,'NOT_PROMOTABLE'
  if any(proof.get(k) is not False or ri.get(k) is not False for k in ('holdout_read','september_2026_data_accessed','orders_allowed')):return False,'RESEARCH_INTEGRITY_FAILED'
  return True,'RECORD_PROOF_VERIFIED'
 except (OSError,ValueError,TypeError,KeyError,AttributeError):return False,'MISSING_OR_INVALID_PROOF'
def price_action_rejection(sid):
 try:
  source=json.loads((S/'price_action_result_v1.json').read_text())
  rows=[r for r in source['result']['records'] if r.get('strategy',{}).get('strategy_id')==sid]
  if len(rows)!=1:return None
  strategy=rows[0]['strategy'];result=rows[0].get('result')
  if not isinstance(result,dict) or result.get('exact_pass') is not True:return None
  p=json.loads((PROOFS/(sid+'.json')).read_text());body={k:v for k,v in p.items() if k!='proof_sha256'}
  if hashlib.sha256(canon(body).encode()).hexdigest()!=p.get('proof_sha256'):return None
  if hashlib.sha256(canon(strategy).encode()).hexdigest()!=p.get('strategy_sha256'):return None
  if p.get('strategy_id')!=sid or p.get('kind')!='V57_DEPLOYMENT_FIDELITY_PROOF_V1':return None
  v=p.get('verdict',{});ri=v.get('research_integrity',{})
  if any(p.get(k) is not False or ri.get(k) is not False for k in ('holdout_read','september_2026_data_accessed','orders_allowed')):return None
  if v.get('strategy_id')!=sid:return None
  if v.get('conclusion')=='DEPLOYMENT_REJECTED' and v.get('fixed_exact_pass') is False and v.get('promotion_allowed') is False and p.get('promotion_allowed') is False:return 'VERIFIED_FIXED_REPLAY_REJECTION'
 except (OSError,ValueError,TypeError,KeyError,AttributeError):pass
 return None
def admit(sid):
 ok,reason=load().verify(str(sid)) if sid else (False,'EMPTY_STRATEGY_ID')
 if not ok and sid:
  rejection=price_action_rejection(str(sid))
  if rejection:reason=rejection
 return {'kind':'JARVIS_SEARCHER_ADMISSION_V1','strategy_id':str(sid or ''),'status':'PASS' if ok else 'DENIED','reason':reason,'admitted':ok,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
def admit_record(record):
 sid=str(record.get('strategy',{}).get('strategy_id','')) if isinstance(record,dict) else ''
 ok,reason=verify_record_proof(record)
 return {'kind':'JARVIS_SEARCHER_ADMISSION_V1','strategy_id':sid,'status':'PASS' if ok else 'DENIED','reason':reason,'admitted':ok,'execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
def main():
 sid=sys.argv[1] if len(sys.argv)>1 else ''
 out=admit(sid);print(json.dumps(out,sort_keys=True));raise SystemExit(0 if out['admitted'] else 3)
if __name__=='__main__':main()
