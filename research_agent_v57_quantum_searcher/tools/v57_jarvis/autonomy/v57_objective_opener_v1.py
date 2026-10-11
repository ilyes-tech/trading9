#!/usr/bin/env python3
import json,pathlib,sys,time,hashlib
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
ALLOW={'REVIEW_CAPABILITY_GAP':'CAPABILITY_REVIEW','REFINE_RESEARCH_HYPOTHESIS':'HYPOTHESIS_REVIEW','REVALIDATE_POOL_INTEGRITY':'POOL_INTEGRITY_REVIEW','REVIEW_RESEARCH_FEEDBACK':'FEEDBACK_REVIEW'}
def main():
 try:r=json.loads((S/'event_router_v1.json').read_text())
 except Exception as e:print('STOP|FAIL|OBJECTIVE_OPENER|ROUTER_UNREADABLE');return 3
 action=r.get('action'); kind=ALLOW.get(action)
 if not kind:
  print('ALL PASS|OBJECTIVE_OPENER_V1|OPENED=NO|ACTION='+str(action));return 0
 seed=kind+'|'+str(r.get('reason'))+'|'+str(r.get('ts_ns')); oid=hashlib.sha256(seed.encode()).hexdigest()[:16]
 obj={'schema_version':1,'kind':'JARVIS_BOUNDED_OBJECTIVE_V1','objective_id':oid,'objective_type':kind,'source_action':action,'source_reason':r.get('reason'),'status':'OPEN_REVIEW_ONLY','max_steps':1,'search_execution_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'created_ns':time.time_ns()}
 p=S/'bounded_objective_v1.json';tmp=S/'bounded_objective_v1.tmp';tmp.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');tmp.replace(p)
 print('ALL PASS|OBJECTIVE_OPENER_V1|OPENED=YES|TYPE='+kind+'|ID='+oid);return 0
if __name__=='__main__':sys.exit(main())
