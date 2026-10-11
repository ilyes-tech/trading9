#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');A=pathlib.Path(__file__).resolve().parent;F=A/'PHASE2_RESEARCH_SAFETY_FREEZE_V1.json'
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 c=load('phase2_research_contract_v1.json');g=load('search_execution_gate_v1.json');o=load('bounded_objective_v1.json');reasons=[]
 try:fh=hashlib.sha256(F.read_bytes()).hexdigest()
 except Exception:fh='';reasons.append('FREEZE_UNREADABLE')
 b=c.get('binding') or {}
 if c.get('status')!='SEALED' or not c.get('contract_id'):reasons.append('CONTRACT_NOT_SEALED')
 if g.get('ready') is not True or not g.get('execution_token'):reasons.append('EXECUTION_GATE_NOT_READY')
 if b.get('objective_id')!=o.get('objective_id') or g.get('objective_id')!=b.get('objective_id'):reasons.append('OBJECTIVE_BINDING_INVALID')
 if g.get('budget_candidates')!=c.get('effective_candidates') or b.get('budget_candidates')!=c.get('effective_candidates'):reasons.append('BUDGET_BINDING_INVALID')
 if b.get('phase2_freeze_sha256')!=fh:reasons.append('FREEZE_BINDING_INVALID')
 # Recompute the contract ID from its immutable binding to detect post-seal mutation.
 expected=hashlib.sha256(canon(b).encode()).hexdigest()
 if c.get('contract_id')!=expected:reasons.append('CONTRACT_DIGEST_INVALID')
 payload={'contract_id':c.get('contract_id'),'execution_token':g.get('execution_token'),'objective_id':b.get('objective_id'),'hypothesis_id':b.get('hypothesis_id'),'diagnosis_sha256':b.get('diagnosis_sha256'),'space':b.get('space'),'budget_candidates':b.get('budget_candidates'),'phase2_freeze_sha256':fh};bid=hashlib.sha256(canon(payload).encode()).hexdigest() if not reasons else None
 out={'schema_version':1,'kind':'JARVIS_PHASE2_CONTRACT_EXECUTION_BINDING_V1','status':'BOUND' if not reasons else 'DENIED','binding_id':bid,'binding':payload,'reasons':reasons,'execution_verified':not reasons,'execution_started':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};q=S/'phase2_contract_execution_binding_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_contract_execution_binding_v1.json');print(('ALL PASS' if not reasons else 'DENIED')+'|PHASE2_CONTRACT_EXEC_BINDING|'+out['status']+'|EXECUTION_STARTED=NO');return 0 if not reasons else 3
if __name__=='__main__':sys.exit(main())
