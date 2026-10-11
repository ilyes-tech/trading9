#!/usr/bin/env python3
import hashlib,json,pathlib,sys
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous');C=S/'checkpoints'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 try:return json.loads(p.read_text())
 except Exception:return {}
def main():
 ds=sorted([x for x in C.iterdir() if x.is_dir() and x.name.isdigit() and (x/'manifest.json').is_file()],key=lambda x:int(x.name)) if C.is_dir() else []
 if not ds:print('STOP|FAIL|RESUME_VALIDATOR|NO_CHECKPOINT');return 3
 d=ds[-1];m=load(d/'manifest.json');files=m.get('files',{})
 if not files or any(not (d/n).is_file() or sha(d/n)!=h for n,h in files.items()):print('STOP|FAIL|RESUME_VALIDATOR|CHECKPOINT_INVALID');return 3
 goal=load(S/'goal_queue_v2.json');active=goal.get('active_goal');drift=[n for n,h in files.items() if (S/n).is_file() and sha(S/n)!=h]
 if active:state='STOP_REVIEW' if drift else 'SAFE_RESUME';rc=3 if drift else 0
 else:state='IDLE';rc=0
 out={'schema_version':1,'kind':'JARVIS_RESUME_VALIDATOR_V1','status':'PASS' if rc==0 else 'REVIEW_REQUIRED','decision':state,'checkpoint':d.name,'checkpoint_files':len(files),'active_goal':active,'state_drift':drift,'automatic_restore_allowed':False,'research_execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False};t=S/'resume_validation_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'resume_validation_v1.json');print(('ALL PASS' if rc==0 else 'STOP|FAIL')+'|RESUME_VALIDATOR_V1|DECISION='+state+'|ACTIVE='+str(active or 'NONE')+'|DRIFT='+str(len(drift)));return rc
if __name__=='__main__':sys.exit(main())
