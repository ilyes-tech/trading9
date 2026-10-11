#!/usr/bin/env python3
import hashlib,json,os,pathlib,sys,time
R=pathlib.Path('/home/trading/TradingAI-HF-Lab');S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');os.chdir(R)
for p in [R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry',R/'research_agent_v57_quantum_searcher/src/v438',R/'research_agent_v57_quantum_searcher/src/v437',R/'research_agent_v57_quantum_searcher/src/v436',R/'research_agent_v57_quantum_searcher/src/v435',R/'research_agent_v57_quantum_searcher/src/v434',R/'research_agent_v57_quantum_searcher/src/v433',R/'research_agent_v57_quantum_searcher/src']:sys.path.insert(0,str(p))
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 g=load('guarded_bounded_research_v1.json');gate=load('search_execution_gate_v1.json');led=load('search_execution_ledger_v1.json');d=load('failure_diagnosis_v2.json');reasons=[]
 tok=g.get('execution_token');budget=g.get('budget_candidates')
 if g.get('status')!='DRY_RUN_PASS' or g.get('scientific_execution_enabled') is not False:reasons.append('GUARD_INVALID')
 if gate.get('ready') is not True or gate.get('execution_token')!=tok or gate.get('budget_candidates')!=budget:reasons.append('GATE_BINDING_INVALID')
 if not tok or (led.get('consumed_tokens') or []).count(tok)!=1:reasons.append('TOKEN_NOT_EXACTLY_ONCE_CONSUMED')
 if not isinstance(budget,int) or not 1<=budget<=4:reasons.append('INVALID_BUDGET')
 if not d.get('space'):reasons.append('DIAGNOSIS_MISSING')
 if reasons:print('STOP|FAIL|PHASE2_SCI_EXEC|'+','.join(reasons));return 3
 done=set(load('phase2_scientific_execution_ledger_v1.json').get('completed_tokens') or [])
 if tok in done:print('STOP|FAIL|PHASE2_SCI_EXEC|TOKEN_ALREADY_EXECUTED');return 3
 market,tf,side=d['space'].split('_');hyp=f'{market} {tf} {side} development-only Phase2 bounded robustness probe';hid=hashlib.sha256(hyp.encode()).hexdigest();seed=800000+(int(hid[:8],16)%100000)
 mem=next(int(x.split()[1])//1024 for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'));loadavg=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
 if mem<2048 or loadavg>0.75:print('STOP|FAIL|PHASE2_SCI_EXEC|RESOURCE_GATE');return 3
 import v57_scientist_v3_4 as SCI
 res=SCI.experiment(hyp,start=0,count=budget,evaluate=True,seed=seed)
 out={'schema_version':1,'kind':'JARVIS_PHASE2_SCIENTIFIC_RESULT_V1','status':'COMPLETED_RESEARCH_ONLY','execution_token':tok,'hypothesis_id':hid,'hypothesis':hyp,'seed':seed,'candidate_count':budget,'result':res,'independent_validation_required':True,'pool_mutation_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()};q=S/'phase2_scientific_result_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_scientific_result_v1.json');done.add(tok);q=S/'phase2_scientific_execution_ledger_v1.tmp';q.write_text(json.dumps({'schema_version':1,'completed_tokens':sorted(done)},indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_scientific_execution_ledger_v1.json');print('ALL PASS|PHASE2_SCI_EXEC|COMPLETED|CANDIDATES='+str(budget)+'|POOL_MUTATION=NO|VALIDATION_REQUIRED=YES');return 0
if __name__=='__main__':sys.exit(main())
