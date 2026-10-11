import json,time,hashlib
from pathlib import Path
S=Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
PLANS={'SAFETY':['SAFETY'],'STATUS':['STATUS'],'AGENDA':['AGENDA','STATUS'],'CONTINUE':['AGENDA','STATUS']}
def classify(q):
 x=q.lower()
 if any(k in x for k in ('sécur','secur','safety','holdout','mt5','ordre')):return 'SAFETY'
 if any(k in x for k in ('continue','poursui','avance')):return 'CONTINUE'
 if any(k in x for k in ('agenda','objectif','plan','autonom')):return 'AGENDA'
 return 'STATUS'
def plan(q):
 k=classify(q);mid=hashlib.sha256((q+str(time.time_ns())).encode()).hexdigest()[:16]
 return {'schema_version':1,'kind':'JARVIS_MISSION_PLAN_V1','mission_id':mid,'request':q,'mission_kind':k,'steps':PLANS[k],'policy':'ALLOWLIST_ONLY;FAIL_CLOSED;MINIMUM_SUFFICIENT_ACTION','orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False}
def main():
 import sys;q=' '.join(sys.argv[1:]).strip();o=plan(q);S.mkdir(parents=True,exist_ok=True);(S/'mission_plan_v1.json').write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(json.dumps(o,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
