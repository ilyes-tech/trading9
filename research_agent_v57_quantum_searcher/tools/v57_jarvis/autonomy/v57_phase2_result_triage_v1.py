#!/usr/bin/env python3
import json,pathlib,sys,time
S=pathlib.Path('/home/trading/.local/state/tradingai/jarvis-autonomous')
def load(n):
 try:return json.loads((S/n).read_text())
 except Exception:return {}
def main():
 x=load('phase2_scientific_result_v1.json');reasons=[];decision='STOP_REVIEW'
 if x.get('status')!='COMPLETED_RESEARCH_ONLY' or x.get('independent_validation_required') is not True:reasons.append('RESULT_ENVELOPE_INVALID')
 r=x.get('result') or {}; recs=r.get('records') or []
 integ_ok=(r.get('holdout_allowed') is False and r.get('mt5_launch_allowed') is False and r.get('orders_allowed') is False and r.get('promotion_allowed') is False and x.get('pool_mutation_allowed') is False)
 for z in recs:
  ri=z.get('research_integrity') or {}; integ_ok &= ri.get('holdout_read') is False and ri.get('holdout_evaluated') is False and ri.get('real_orders_allowed') is False and ri.get('demo_orders_allowed') is False and ri.get('september_2026_data_accessed') is False
 if not integ_ok:reasons.append('RESEARCH_INTEGRITY_VIOLATION')
 if not reasons:
  sts=[z.get('status') for z in recs]
  if recs and all(s=='PREFILTER_REJECT' for s in sts):decision='TERMINAL_REJECT';reasons=['ALL_CANDIDATES_PREFILTER_REJECT']
  elif recs and any(z.get('result') is not None for z in recs):decision='VALIDATION_REQUIRED';reasons=['EVALUABLE_RESULT_PRESENT']
  else:decision='STOP_REVIEW';reasons=['UNCLASSIFIED_RESULT_SHAPE']
 out={'schema_version':1,'kind':'JARVIS_PHASE2_RESULT_TRIAGE_V1','decision':decision,'reasons':reasons,'execution_token':x.get('execution_token'),'records':len(recs),'deep_validation_allowed':decision=='VALIDATION_REQUIRED','pool_mutation_allowed':False,'orders_allowed':False,'mt5_allowed':False,'holdout_allowed':False,'auto_promotion_allowed':False,'ts_ns':time.time_ns()};q=S/'phase2_result_triage_v1.tmp';q.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');q.replace(S/'phase2_result_triage_v1.json');print(('ALL PASS' if decision!='STOP_REVIEW' else 'STOP|FAIL')+'|PHASE2_RESULT_TRIAGE|DECISION='+decision+'|RECORDS='+str(len(recs))+'|DEEP_VALIDATION='+str(out['deep_validation_allowed']).upper());return 0 if decision!='STOP_REVIEW' else 3
if __name__=='__main__':sys.exit(main())
