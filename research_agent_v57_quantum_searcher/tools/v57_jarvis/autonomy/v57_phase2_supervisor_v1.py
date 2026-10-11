#!/usr/bin/env python3
import json,pathlib,subprocess,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');A=pathlib.Path(__file__).resolve().parent;PY=sys.executable;VPY='/home/trading/TradingAI-HF-Lab/.venv-research/bin/python'
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def run(name,venv=False):
 p=subprocess.run([VPY if venv else PY,str(A/name)],capture_output=True,text=True);return p.returncode,(p.stdout+p.stderr).strip()
def stop(stage,detail,rc=3):
 out={'schema_version':1,'kind':'JARVIS_PHASE2_SUPERVISOR_V1','status':'STOPPED','stage':stage,'detail':detail,'search_started':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};(S/'phase2_supervisor_v1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('STOP|FAIL|PHASE2_SUPERVISOR|'+stage+'|'+detail);return rc
def main():
 # Supervisor never opens objectives or manufactures authorization. It only consumes a pre-authorized chain.
 for name,venv,stage in [('v57_phase2_research_contract_v1.py',False,'CONTRACT'),('v57_phase2_contract_execution_binding_v1.py',False,'BINDING')]:
  rc,msg=run(name,venv)
  if rc:return stop(stage,msg.splitlines()[-1] if msg else 'DENIED')
 b=load('phase2_contract_execution_binding_v1.json')
 if b.get('status')!='BOUND' or b.get('execution_verified') is not True:return stop('BINDING','NOT_BOUND')
 # Only now may the frozen guarded chain be invoked. Each frozen component remains independently fail-closed.
 steps=[('v57_guarded_bounded_research_v1.py',False,'GUARD'),('v57_phase2_scientific_executor_v1.py',True,'SCIENTIFIC'),('v57_phase2_result_triage_v1.py',False,'TRIAGE')]
 trace=[]
 for name,venv,stage in steps:
  rc,msg=run(name,venv);trace.append({'stage':stage,'rc':rc,'output':msg[-500:]})
  if rc:return stop(stage,msg.splitlines()[-1] if msg else 'DENIED')
 tri=load('phase2_result_triage_v1.json')
 if tri.get('decision')=='VALIDATION_REQUIRED':
  rc,msg=run('v57_phase2_deep_validation_v1.py',True);trace.append({'stage':'DEEP','rc':rc,'output':msg[-500:]})
  if rc:return stop('DEEP',msg.splitlines()[-1] if msg else 'DENIED')
 rc,msg=run('v57_phase2_promotion_decision_v1.py');trace.append({'stage':'PROMOTION_DECISION','rc':rc,'output':msg[-500:]})
 if rc:return stop('PROMOTION_DECISION',msg.splitlines()[-1] if msg else 'DENIED')
 out={'schema_version':1,'kind':'JARVIS_PHASE2_SUPERVISOR_V1','status':'COMPLETED','binding_id':b.get('binding_id'),'trace':trace,'search_started':True,'promotion':load('phase2_promotion_decision_v1.json'),'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()};(S/'phase2_supervisor_v1.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('ALL PASS|PHASE2_SUPERVISOR|COMPLETED|PROMOTION=NO|ORDERS=NO');return 0
if __name__=='__main__':sys.exit(main())
