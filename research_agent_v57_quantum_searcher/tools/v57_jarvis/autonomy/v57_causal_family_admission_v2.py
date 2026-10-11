import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def check(x,exhausted):
 if not isinstance(x,dict):return "DENY_MALFORMED"
 family=x.get("native_family")
 if not isinstance(family,str) or not family.strip():return "DENY_MISSING_FAMILY"
 if family in exhausted:return "DENY_EXHAUSTED_FAMILY"
 if any(x.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE"
 if x.get("new_causal_evidence_verified") is True:return "DENY_UNTRUSTED_SELF_ATTESTATION"
 return "DENY_NO_INDEPENDENT_EVIDENCE_VERIFIER"
def main():
 p=S/"native_capability_coverage_v2.json";v=json.loads(p.read_text())
 if v.get("kind")!="V57_NATIVE_CAPABILITY_COVERAGE_V2" or v.get("status")!="PASS" or len(v.get("exhausted_families",[]))!=5:raise RuntimeError("COVERAGE")
 exhausted=set(v["exhausted_families"]);safe={k:False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")}
 cases=[({}, "DENY_MISSING_FAMILY"),({"native_family":"momentum",**safe},"DENY_EXHAUSTED_FAMILY"),({"native_family":"new_family","new_causal_evidence_verified":True,**safe},"DENY_UNTRUSTED_SELF_ATTESTATION"),({"native_family":"new_family",**safe},"DENY_NO_INDEPENDENT_EVIDENCE_VERIFIER"),({"native_family":"new_family","orders_allowed":True,**{k:v for k,v in safe.items() if k!="orders_allowed"}},"DENY_UNSAFE")]
 if any(check(x,exhausted)!=expected for x,expected in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_CAUSAL_FAMILY_ADMISSION_V2","status":"PASS","coverage_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"tests":len(cases),"independent_evidence_verifier":"NOT_IMPLEMENTED","self_attestation_accepted":False,"new_family_admitted":False,"research_execution_authorized":False,**safe}
 q=S/"causal_family_admission_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"causal_family_admission_v2.json")
 print("ALL PASS|CAUSAL_FAMILY_ADMISSION_V2|TESTS=5|SELF_ATTESTATION=DENIED|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|CAUSAL_FAMILY_ADMISSION_V2|"+str(e));sys.exit(3)
