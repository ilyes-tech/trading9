#!/usr/bin/env python3
import json
CONTROLLED={'NOT_ALLOWLISTED','EMPTY_REQUEST','POLICY_DENIED','SAFETY_DENIED'}
def classify(result):
 status=result.get('status');reason=str(result.get('reason','')).upper()
 if status in {'DENIED','REJECTED'} and reason in CONTROLLED:return 'CONTROLLED_REJECTION'
 if status in {'FAIL','FAILED','ERROR'}:return 'MISSION_FAILURE'
 if status in {'PASS','COMPLETED','SUCCESS'}:return 'SUCCESS'
 return 'UNKNOWN'
def main():
 import sys
 try:r=json.loads(sys.argv[1]) if len(sys.argv)>1 else {}
 except Exception:print('STOP|FAIL|FAILURE_CLASSIFIER|BAD_JSON');raise SystemExit(2)
 c=classify(r);print(json.dumps({'kind':'JARVIS_FAILURE_CLASSIFIER_V1','status':'PASS','classification':c,'memory_failure_eligible':c=='MISSION_FAILURE','orders_allowed':False,'mutation_allowed':False},sort_keys=True))
if __name__=='__main__':main()
