import json,hashlib,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def check(x,covered):
 if not isinstance(x,dict):return "DENY_MALFORMED"
 if x.get("native_family") in covered:return "DENY_EXHAUSTED_NATIVE_FAMILY"
 if not isinstance(x.get("native_family"),str) or not x["native_family"].strip():return "DENY_MISSING_FAMILY"
 if x.get("new_causal_evidence_verified") is not True:return "DENY_UNVERIFIED_CAUSAL_EVIDENCE"
 if any(x.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE"
 return "REVIEW_REQUIRED_NOT_AUTHORIZED"
def main():
 p=S/"native_capability_coverage_v2.json";a=json.loads(p.read_text())
 if a.get("status")!="PASS" or a.get("kind")!="V57_NATIVE_CAPABILITY_COVERAGE_V2" or a.get("uncovered_native_families")!=[]:raise RuntimeError("COVERAGE")
 covered=set(a["exhausted_families"])
 if len(covered)!=5:raise RuntimeError("FAMILIES")
 safe={"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 cases=[({"native_family":"momentum","new_causal_evidence_verified":True,**safe},"DENY_EXHAUSTED_NATIVE_FAMILY"),({"native_family":"price_action","new_causal_evidence_verified":False,**safe},"DENY_UNVERIFIED_CAUSAL_EVIDENCE"),({"native_family":"new_testable_family","new_causal_evidence_verified":True,"orders_allowed":True,**{k:v for k,v in safe.items() if k!="orders_allowed"}},"DENY_UNSAFE"),({"native_family":"new_testable_family","new_causal_evidence_verified":True,**safe},"REVIEW_REQUIRED_NOT_AUTHORIZED"),({},"DENY_MISSING_FAMILY")]
 if any(check(x,covered)!=expected for x,expected in cases):raise RuntimeError("TEST")
 doc={"schema_version":1,"kind":"V57_CAUSAL_FAMILY_ADMISSION_V1","status":"PASS","coverage_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"tested":len(cases),"exhausted_families":sorted(covered),"new_family_admitted":False,"evidence_verified":False,"execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"causal_family_admission_v1.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"causal_family_admission_v1.json")
 print("ALL PASS|CAUSAL_FAMILY_ADMISSION_V1|TESTS=5|EXHAUSTED=5|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|CAUSAL_FAMILY_ADMISSION_V1|"+str(e));sys.exit(3)
