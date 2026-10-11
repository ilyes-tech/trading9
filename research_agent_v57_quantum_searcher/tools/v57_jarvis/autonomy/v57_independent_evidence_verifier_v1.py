import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def verify(candidate):
 if not isinstance(candidate,dict):return "DENY_MALFORMED"
 if candidate.get("new_causal_evidence_verified") is True:return "DENY_SELF_ATTESTED"
 name=candidate.get("evidence_file")
 if not isinstance(name,str) or not name.endswith(".json") or Path(name).name!=name:return "DENY_UNTRUSTED_PATH"
 p=S/name
 if not p.is_file():return "DENY_MISSING_EVIDENCE"
 h=candidate.get("evidence_sha256")
 if not isinstance(h,str) or len(h)!=64 or hashlib.sha256(p.read_bytes()).hexdigest()!=h:return "DENY_HASH_MISMATCH"
 try:doc=json.loads(p.read_text())
 except (ValueError,UnicodeError):return "DENY_INVALID_EVIDENCE"
 if doc.get("status") not in ("PASS","COMPLETED"):return "DENY_FAILED_EVIDENCE"
 return "INTEGRITY_VERIFIED_CAUSAL_NOVELTY_NOT_PROVEN"
def main():
 p=S/"multimarket_evidence_registry_v3.json";h=hashlib.sha256(p.read_bytes()).hexdigest()
 cases=[({"new_causal_evidence_verified":True},"DENY_SELF_ATTESTED"),({"evidence_file":"../outside.json"},"DENY_UNTRUSTED_PATH"),({"evidence_file":"missing.json"},"DENY_MISSING_EVIDENCE"),({"evidence_file":p.name,"evidence_sha256":"0"*64},"DENY_HASH_MISMATCH"),({"evidence_file":p.name,"evidence_sha256":h},"INTEGRITY_VERIFIED_CAUSAL_NOVELTY_NOT_PROVEN")]
 if any(verify(x)!=y for x,y in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_INDEPENDENT_EVIDENCE_VERIFIER_V1","status":"PASS","tests":len(cases),"verified_reference_sha256":h,"evidence_integrity_supported":True,"causal_novelty_proven":False,"new_research_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"independent_evidence_verifier_v1.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"independent_evidence_verifier_v1.json")
 print("ALL PASS|INDEPENDENT_EVIDENCE_VERIFIER_V1|TESTS=5|INTEGRITY=YES|CAUSAL_NOVELTY=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|INDEPENDENT_EVIDENCE_VERIFIER_V1|"+str(e));sys.exit(3)
