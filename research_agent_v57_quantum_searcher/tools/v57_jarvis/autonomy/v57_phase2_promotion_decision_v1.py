#!/usr/bin/env python3
import json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 d=load('phase2_deep_validation_v1.json');reasons=[]
 if d.get('status')!='COMPLETED':reasons.append('DEEP_VALIDATION_NOT_COMPLETED')
 deep=d.get('deep') or {}
 if deep.get('status')!='DEEP_PASS':reasons.append('DEEP_PASS_REQUIRED')
 if d.get('independent_replay_exact_pass') is not True:reasons.append('INDEPENDENT_REPLAY_REQUIRED')
 # A DEEP_PASS may become review-eligible only. This component never promotes or mutates pools.
 eligible=not reasons
 out={'schema_version':1,'kind':'JARVIS_PHASE2_PROMOTION_DECISION_V1','decision':'REVIEW_ELIGIBLE' if eligible else 'NOT_ELIGIBLE','reasons':reasons or ['DEEP_PASS_REQUIRES_EXPLICIT_REVIEW'],'execution_token':d.get('execution_token'),'strategy_id':d.get('strategy_id'),'review_required':True,'promotion_executed':False,'pool_mutation_allowed':False,'auto_promotion_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'ts_ns':time.time_ns()}
 q=S/'phase2_promotion_decision_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_promotion_decision_v1.json')
 print('ALL PASS|PHASE2_PROMOTION_DECISION|'+out['decision']+'|REVIEW_REQUIRED=YES|PROMOTION=NO|POOL_MUTATION=NO');return 0
if __name__=='__main__':sys.exit(main())
