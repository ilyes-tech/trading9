#!/usr/bin/env python3
import hashlib,json,tempfile
from pathlib import Path
import v57_deployment_fidelity_verify_v1 as V
SID='002850644fdd4dcc9d8a5681ad7a0567c504074225b6f650d465dd651aff3101'
def main():
 ok,r=V.verify(SID); assert ok and r=='VERIFIED'
 src=V.PROOFS/(SID+'.json'); proof=json.loads(src.read_text())
 with tempfile.TemporaryDirectory(prefix='v57_fidelity_test_') as td:
  d=Path(td); fake=d/(SID+'.json'); fake.write_text(json.dumps(proof))
  old=V.PROOFS; V.PROOFS=d
  try:
   q=json.loads(fake.read_text()); q['promotion_allowed']=False; fake.write_text(json.dumps(q)); ok2,r2=V.verify(SID)
  finally: V.PROOFS=old
 assert not ok2 and r2=='PROOF_HASH_MISMATCH'
 print('PASS|FIDELITY_VERIFIER_SELFTEST|VALID=VERIFIED|TAMPER=PROOF_HASH_MISMATCH|PRODUCTION_UNCHANGED=TRUE')
if __name__=='__main__':main()
