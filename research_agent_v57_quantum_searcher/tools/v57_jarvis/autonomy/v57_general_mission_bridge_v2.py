import json,subprocess,time,importlib.util
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');PY=R/'.venv-research/bin/python'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
PL=load('j57planner',A/'v57_mission_planner_v1.py')
TOOLS={'STATUS':('v57_autonomous_core_v6.py',),'AGENDA':('v57_agenda_cycle_v1.py',),'SAFETY':()}
def invoke(tool):
 if tool=='SAFETY':cmd=[str(PY),str(R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/kernel/v57_jarvis_safety_v1.py'),'--self-check']
 else:cmd=[str(PY),str(A/TOOLS[tool][0])]
 p=subprocess.run(cmd,cwd=R,text=True,capture_output=True,timeout=180);lines=p.stdout.strip().splitlines();return {'tool':tool,'rc':p.returncode,'output':lines[-1] if lines else ''}
def execute(q):
 plan=PL.plan(q);steps=[];status='COMPLETED'
 for tool in plan['steps']:
  r=invoke(tool);steps.append(r)
  if r['rc']!=0:status='FAILED';break
 out={'schema_version':2,'kind':'JARVIS_GENERAL_MISSION_BRIDGE_V2','mission_id':plan['mission_id'],'request':q,'route':'AUTONOMOUS_GENERAL','mission_kind':plan['mission_kind'],'plan':plan['steps'],'status':status,'steps':steps,'execution':True,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 t=S/'general_mission_last_v2.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'general_mission_last_v2.json');return out
def main():
 import sys
 q=' '.join(sys.argv[1:]).strip()
 if not q:print(json.dumps({'status':'FAILED','reason':'EMPTY_REQUEST'}));raise SystemExit(2)
 o=execute(q);print(json.dumps(o,ensure_ascii=False,sort_keys=True));raise SystemExit(0 if o['status']=='COMPLETED' else 1)
if __name__=='__main__':main()
