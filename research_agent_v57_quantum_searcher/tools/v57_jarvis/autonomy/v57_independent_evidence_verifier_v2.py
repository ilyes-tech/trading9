import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
ALLOW={"multimarket_evidence_registry_v3.json":"V57_MULTIMARKET_EVIDENCE_REGISTRY_V3"}
def verify(candidate):
 if not isinstance(candidate,dict):return "DENY_MALFORMED"
 if candidate.get("new_causal_evidence_verified") is True:return "DENY_SELF_ATTESTED"
 name=candidate.get("evidence_file")
 if not isinstance(name,str) or name not in ALLOW:return "DENY_UNTRUSTED_SOURCE"
 p=S/name
 if not p.is_file() or p.is_symlink():return "DENY_MISSING_OR_SYMLINK"
 expected=candidate.get("evidence_sha256")
 if not isinstance(expected,str) or len(expected)!=64:return "DENY_HASH"
 raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected:return "DENY_HASH"
 try:doc=json.loads(raw)
 except (ValueError,UnicodeError):return "DENY_INVALID_JSON"
 if doc.get("kind")!=ALLOW[name] or doc.get("status")!="PASS" or len(doc.get("markets",{}))!=7:return "DENY_SCHEMA"
 if any(doc.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE_SOURCE"
 return "INTEGRITY_AND_SCHEMA_VERIFIED_NOT_CAUSAL_NOVELTY"
def main():
 p=S/"multimarket_evidence_registry_v3.json";h=hashlib.sha256(p.read_bytes()).hexdigest()
 cases=[({"new_causal_evidence_verified":True},"DENY_SELF_ATTESTED"),({"evidence_file":"arbitrary_pass.json"},"DENY_UNTRUSTED_SOURCE"),({"evidence_file":p.name,"evidence_sha256":"0"*64},"DENY_HASH"),({"evidence_file":p.name,"evidence_sha256":h},"INTEGRITY_AND_SCHEMA_VERIFIED_NOT_CAUSAL_NOVELTY")]
 if any(verify(x)!=expected for x,expected in cases):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_INDEPENDENT_EVIDENCE_VERIFIER_V2","status":"PASS","tests":len(cases),"allowlisted_sources":list(ALLOW),"source_sha256":h,"source_schema_checked":True,"causal_novelty_proven":False,"new_research_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"independent_evidence_verifier_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"independent_evidence_verifier_v2.json")
 print("ALL PASS|INDEPENDENT_EVIDENCE_VERIFIER_V2|TESTS=4|ALLOWLIST=1|NOVELTY=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|INDEPENDENT_EVIDENCE_VERIFIER_V2|"+str(e));sys.exit(3)
