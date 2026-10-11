import hashlib,json,py_compile,shutil
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");D=S/"self_improvement_sandbox";D.mkdir(parents=True,exist_ok=True)
T=D/"candidate.py";B=D/"candidate.py.rollback"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 T.write_text('CAPABILITY="BASELINE"\ndef self_check(): return True\n');before=sha(T);shutil.copy2(T,B)
 T.write_text('CAPABILITY="IMPROVED_TEST"\ndef self_check(): return True\ndef added_capability(): return "PASS"\n')
 build=sha(T)!=before
 try:py_compile.compile(str(T),doraise=True);verify=True
 except Exception:verify=False
 shutil.copy2(B,T);after=sha(T);rollback=after==before
 ok=build and verify and rollback
 out={"schema_version":1,"kind":"JARVIS_SELF_IMPROVEMENT_TRANSACTION_TEST_V1","status":"PASS" if ok else "FAIL","sandbox_only":True,"build_performed":build,"verification_passed":verify,"rollback_performed":True,"rollback_hash_match":rollback,"frozen_mutation":False,"production_mutation":False}
 t=S/"self_improvement_transaction_test_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"self_improvement_transaction_test_v1.json")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|SELF_IMPROVEMENT_TRANSACTION|BUILD="+str(build).upper()+"|VERIFY="+str(verify).upper()+"|ROLLBACK="+str(rollback).upper())
if __name__=="__main__":main()
