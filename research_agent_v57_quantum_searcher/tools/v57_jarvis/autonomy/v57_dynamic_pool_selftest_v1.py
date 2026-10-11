#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
import v57_dynamic_verified_pool_v1 as D
SID=json.loads(D.REG.read_text())['strategies'][0]['strategy_id']
def main():
 old=D.V.PROOFS
 with tempfile.TemporaryDirectory(prefix='v57_revoke_test_') as td:
  d=Path(td)
  for p in old.glob('*.json'): (d/p.name).write_bytes(p.read_bytes())
  (d/(SID+'.json')).unlink();D.V.PROOFS=d
  try:
   ok,reason=D.V.verify(SID)
  finally:D.V.PROOFS=old
 assert not ok and reason=='MISSING_OR_UNREADABLE'
 ok2,reason2=D.V.verify(SID);assert ok2 and reason2=='VERIFIED'
 print('PASS|DYNAMIC_POOL_SELFTEST|ISOLATED_REVOCATION=MISSING_OR_UNREADABLE|PRODUCTION_RESTORED=VERIFIED')
if __name__=='__main__':main()
