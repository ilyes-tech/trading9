import json,importlib.util
from pathlib import Path
A=Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy');S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
PL=load('planner2',A/'v57_mission_planner_v2.py');RT=load('router1',A/'v57_capability_router_v1.py');SG=load('strategyguard1',A/'v57_strategy_reference_guard_v1.py');SD=load('strategydecision1',A/'v57_strategy_decision_v1.py')
def execute(q):
 gok,greason,gsid=SG.check(q)
 if not gok:return {'schema_version':3,'kind':'JARVIS_GENERAL_MISSION_BRIDGE_V3','request':q,'status':'FAILED','reason':'STRATEGY_REFERENCE_DENIED','strategy_id':gsid,'guard_reason':greason,'execution':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 decision=None
 if gsid is None and any(k in q.lower() for k in ('strategy','searcher','candidate')):
  sr,de=SD.decide();decision={'audit':de,'selection':sr}
  if sr.get('status')!='PASS':return {'schema_version':3,'kind':'JARVIS_GENERAL_MISSION_BRIDGE_V3','request':q,'status':'FAILED','reason':'AUTONOMOUS_STRATEGY_SELECTION_DENIED','decision':decision,'execution':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 p=PL.plan(q);steps=[];status='COMPLETED'
 for cap in p['steps']:
  if cap=='SAFETY':
   import subprocess;r=subprocess.run(['/home/trading/TradingAI-HF-Lab/.venv-research/bin/python',str(A.parent/'kernel/v57_jarvis_safety_v1.py'),'--self-check'],text=True,capture_output=True);z={'capability':'SAFETY','status':'PASS' if r.returncode==0 else 'FAIL','rc':r.returncode,'output':r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''}
  else:z=RT.run(cap)
  steps.append(z)
  if z['status']!='PASS':status='FAILED';break
 o={'schema_version':3,'kind':'JARVIS_GENERAL_MISSION_BRIDGE_V3','mission_id':p['mission_id'],'request':q,'mission_kind':p['mission_kind'],'plan':p['steps'],'steps':steps,'decision':decision,'status':status,'execution':True,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 S.mkdir(parents=True,exist_ok=True);t=S/'general_mission_last_v3.tmp';t.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');t.replace(S/'general_mission_last_v3.json');return o
def main():
 import sys;q=' '.join(sys.argv[1:]).strip()
 if not q:print(json.dumps({'status':'FAILED','reason':'EMPTY_REQUEST'}));raise SystemExit(2)
 o=execute(q);print(json.dumps(o,ensure_ascii=False,sort_keys=True));raise SystemExit(0 if o['status']=='COMPLETED' else 1)
if __name__=='__main__':main()
