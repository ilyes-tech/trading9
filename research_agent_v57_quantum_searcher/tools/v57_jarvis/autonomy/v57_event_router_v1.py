#!/usr/bin/env python3
import json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(name):
 p=S/name
 try:return json.loads(p.read_text())
 except Exception:return {}
def main():
 ev=load('event_sentinel_v1.json'); reasons=set(ev.get('reasons') or [])
 action='IDLE'; why='NO_NEW_EVENT'; research=False
 if ev.get('status')=='WAKE':
  if 'CAPABILITY_GAP_STATE_CHANGED' in reasons:
   gap=load('capability_gap_plan_v1.json')
   action='REVIEW_CAPABILITY_GAP' if gap.get('status')=='GAP_FOUND' else 'OBSERVE'
   why='CAPABILITY_GAP_EVENT'
  elif 'FAILURE_DIAGNOSIS_CHANGED' in reasons:
   action='REFINE_RESEARCH_HYPOTHESIS';why='FAILURE_DIAGNOSIS_EVENT'
  elif 'NEW_RESEARCH_FEEDBACK' in reasons:
   fb=load('research_feedback_v1.json')
   action='DO_NOT_REPEAT_IDENTICAL_PROBE' if fb.get('next_action')=='DO_NOT_REPEAT_IDENTICAL_PROBE' else 'REVIEW_RESEARCH_FEEDBACK'
   why='RESEARCH_FEEDBACK_EVENT'
  elif 'VERIFIED_POOL_CHANGED' in reasons:
   action='REVALIDATE_POOL_INTEGRITY';why='VERIFIED_POOL_EVENT'
 # Router never executes search; explicit downstream authorization is required.
 out={'schema_version':1,'kind':'JARVIS_EVENT_ROUTER_V1','status':'PASS','event_status':ev.get('status','UNKNOWN'),'action':action,'reason':why,'research_execution_allowed':research,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()}
 t=S/'event_router_v1.tmp';t.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');t.replace(S/'event_router_v1.json')
 print('ALL PASS|EVENT_ROUTER_V1|EVENT='+out['event_status']+'|ACTION='+action+'|RESEARCH=BLOCKED');return 0
if __name__=='__main__':sys.exit(main())
