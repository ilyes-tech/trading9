#!/usr/bin/env python3
import json,tempfile,sys
from pathlib import Path
A=Path(__file__).resolve().parent;sys.path.insert(0,str(A));import v57_strategy_decision_v1 as D
def main():
 prod=D.LOG.read_bytes();events=[x for x in D.LOG.read_text().splitlines() if x.strip()];assert events
 with tempfile.TemporaryDirectory(prefix='v57_crash_') as td:
  p=Path(td)/'audit.jsonl';p.write_text('\n'.join(events)+'\n{"ts":"PARTIAL"')
  assert D.verify_chain(p)[0] is False
  orig=D.LOG;D.LOG=p
  try:r,e=D.decide('XAUUSD',None,'SHORT')
  finally:D.LOG=orig
  assert r['status']=='DENIED' and r['reason']=='AUDIT_CHAIN_INVALID' and e is None
 assert D.LOG.read_bytes()==prod and D.verify_chain()[0] is True
 print('PASS|AUDIT_CRASH_SELFTEST|PARTIAL_LINE=DENIED|NO_AUTO_REPAIR=TRUE|PRODUCTION_UNCHANGED=TRUE')
if __name__=='__main__':main()
