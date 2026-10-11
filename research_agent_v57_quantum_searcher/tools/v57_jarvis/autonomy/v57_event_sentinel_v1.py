#!/usr/bin/env python3
import hashlib,json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
ROOT=pathlib.Path('/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher')
SNAP=S/'event_sentinel_v1.json'; POOL=ROOT/'work/v57_jarvis/dynamic_verified_pool_v1.json'
WATCH=[S/'research_feedback_v1.json',S/'capability_gap_plan_v1.json',S/'failure_diagnosis_v2.json',POOL]
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def main():
 current={str(p):digest(p) for p in WATCH}; previous={}
 if SNAP.is_file():
  try: previous=json.loads(SNAP.read_text()).get('observed',{})
  except Exception: previous={}
 changed=[p for p,h in current.items() if previous.get(p)!=h]
 reasons=[]
 # First run establishes baseline only: no synthetic work.
 if previous:
  for p in changed:
   name=pathlib.Path(p).name
   if name=='research_feedback_v1.json': reasons.append('NEW_RESEARCH_FEEDBACK')
   elif name=='capability_gap_plan_v1.json': reasons.append('CAPABILITY_GAP_STATE_CHANGED')
   elif name=='failure_diagnosis_v2.json': reasons.append('FAILURE_DIAGNOSIS_CHANGED')
   elif name=='dynamic_verified_pool_v1.json': reasons.append('VERIFIED_POOL_CHANGED')
 status='WAKE' if reasons else 'IDLE'
 out={'schema_version':1,'kind':'JARVIS_EVENT_SENTINEL_V1','status':status,'reasons':reasons,'changed':changed if previous else [],'observed':current,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()}
 tmp=S/'event_sentinel_v1.tmp';tmp.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');tmp.replace(SNAP)
 print(('ALL PASS' if status=='IDLE' else 'WAKE')+'|EVENT_SENTINEL_V1|STATUS='+status+'|REASONS='+(','.join(reasons) if reasons else 'NONE'))
 return 0
if __name__=='__main__':sys.exit(main())
