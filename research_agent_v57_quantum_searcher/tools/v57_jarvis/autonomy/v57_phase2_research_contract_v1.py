#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');A=pathlib.Path(__file__).resolve().parent
FREEZE=A/'PHASE2_RESEARCH_SAFETY_FREEZE_V1.json'
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def main():
 o=load('bounded_objective_v1.json');d=load('failure_diagnosis_v2.json');h=load('refined_hypothesis_v1.json');p=load('experiment_plan_v1.json');reasons=[]
 try:f=json.loads(FREEZE.read_text());fh=hashlib.sha256(FREEZE.read_bytes()).hexdigest()
 except Exception:f={};fh='';reasons.append('PHASE2_FREEZE_UNREADABLE')
 if f.get('status')!='FROZEN':reasons.append('PHASE2_NOT_FROZEN')
 if o.get('status')!='OPEN_REVIEW_ONLY' or not o.get('objective_id'):reasons.append('OBJECTIVE_INVALID')
 if d.get('status')!='DIAGNOSED' or not d.get('space'):reasons.append('DIAGNOSIS_INVALID')
 if h.get('status')!='PROPOSED' or not h.get('hypothesis_id'):reasons.append('HYPOTHESIS_INVALID')
 plan=p.get('plan') or {};space=d.get('space')
 if (h.get('objective') or {}).get('space')!=space or plan.get('space')!=space:reasons.append('SPACE_BINDING_INVALID')
 if plan.get('hypothesis_id')!=h.get('hypothesis_id'):reasons.append('HYPOTHESIS_BINDING_INVALID')
 requested=plan.get('max_candidates');cap=(f.get('invariants') or {}).get('bounded_candidate_budget_max')
 if not isinstance(requested,int) or requested<1 or cap!=4:reasons.append('BUDGET_SOURCE_INVALID')
 budget=min(requested,cap) if isinstance(requested,int) and isinstance(cap,int) else 0
 diag_fp=hashlib.sha256(canon(d).encode()).hexdigest();payload={'objective_id':o.get('objective_id'),'hypothesis_id':h.get('hypothesis_id'),'diagnosis_sha256':diag_fp,'space':space,'budget_candidates':budget,'phase2_freeze_sha256':fh};cid=hashlib.sha256(canon(payload).encode()).hexdigest()
 out={'schema_version':1,'kind':'JARVIS_PHASE2_RESEARCH_CONTRACT_V1','status':'SEALED' if not reasons else 'DENIED','contract_id':cid if not reasons else None,'binding':payload,'requested_candidates':requested,'effective_candidates':budget if not reasons else 0,'reasons':reasons,'execution_allowed':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};q=S/'phase2_research_contract_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_research_contract_v1.json');print(('ALL PASS' if not reasons else 'DENIED')+'|PHASE2_RESEARCH_CONTRACT|'+out['status']+'|BUDGET='+str(out['effective_candidates'])+'|EXECUTION=NO');return 0 if not reasons else 3
if __name__=='__main__':sys.exit(main())
