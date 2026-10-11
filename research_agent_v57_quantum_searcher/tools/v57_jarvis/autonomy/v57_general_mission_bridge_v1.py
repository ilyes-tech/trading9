import json,subprocess,time,hashlib
from pathlib import Path
R=Path('/home/trading/TradingAI-HF-Lab');A=R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy';S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous');PY=R/'.venv-research/bin/python'
SAFE={'STATUS':('v57_autonomous_core_v6.py',),'AGENDA':('v57_agenda_cycle_v1.py',),'SAFETY':()}
def classify(q):
 x=q.lower()
 if any(k in x for k in ('sécur','secur','safety','interdit','holdout','ordre','mt5')): return 'SAFETY'
 if any(k in x for k in ('agenda','objectif','plan','continue','autonom')): return 'AGENDA'
 return 'STATUS'
def run_script(n):
 p=subprocess.run([str(PY),str(A/n)],cwd=R,text=True,capture_output=True,timeout=180);lines=p.stdout.strip().splitlines();return p.returncode,(lines[-1] if lines else '')
def execute(q):
 kind=classify(q);steps=[]
 for n in SAFE[kind]:
  rc,out=run_script(n);steps.append({'tool':n,'rc':rc,'output':out})
  if rc: return result(q,kind,'FAILED',steps)
 if kind=='SAFETY':
  p=subprocess.run([str(PY),str(R/'research_agent_v57_quantum_searcher/tools/v57_jarvis/kernel/v57_jarvis_safety_v1.py'),'--self-check'],cwd=R,text=True,capture_output=True,timeout=60);steps.append({'tool':'SAFETY_SELF_CHECK','rc':p.returncode,'output':p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ''})
  if p.returncode:return result(q,kind,'FAILED',steps)
 return result(q,kind,'COMPLETED',steps)
def result(q,kind,status,steps):
 mid=hashlib.sha256((q+str(time.time_ns())).encode()).hexdigest()[:16]
 out={'schema_version':1,'kind':'JARVIS_GENERAL_MISSION_BRIDGE_V1','mission_id':mid,'request':q,'route':'AUTONOMOUS_GENERAL','mission_kind':kind,'status':status,'steps':steps,'execution':True,'allowlist':list(SAFE),'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False}
 S.mkdir(parents=True,exist_ok=True);t=S/'general_mission_last.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'general_mission_last.json');return out
def main():
 import sys
 q=' '.join(sys.argv[1:]).strip()
 if not q: print(json.dumps({'status':'FAILED','reason':'EMPTY_REQUEST'}));return
 print(json.dumps(execute(q),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
