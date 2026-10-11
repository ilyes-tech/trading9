import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def gate(proposal,registry):
 if not isinstance(proposal,dict):return "DENY_NO_PROPOSAL"
 if proposal.get("market") not in registry["markets"]:return "DENY_UNKNOWN_MARKET"
 if any(proposal.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):return "DENY_UNSAFE"
 for k in ("hypothesis_id","evidence_source_sha256","novelty_evidence_sha256"):
  v=proposal.get(k)
  if not isinstance(v,str) or len(v)!=64 or any(c not in "0123456789abcdef" for c in v):return "DENY_UNVERIFIED"
 if not isinstance(proposal.get("causal_dimension"),str) or not proposal["causal_dimension"].strip():return "DENY_UNVERIFIED"
 return "REVIEW_REQUIRED_NOT_AUTHORIZED"
def main():
 p=S/"multimarket_evidence_registry_v3.json";r=json.loads(p.read_text())
 if r.get("kind")!="V57_MULTIMARKET_EVIDENCE_REGISTRY_V3" or r.get("status")!="PASS" or len(r["markets"])!=7:raise RuntimeError("REGISTRY")
 z="a"*64
 cases=[(None,"DENY_NO_PROPOSAL"),({"market":"FAKE"},"DENY_UNKNOWN_MARKET"),({"market":"BTCUSD","orders_allowed":True},"DENY_UNSAFE"),({"market":"BTCUSD","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False},"DENY_UNVERIFIED"),({"market":"BTCUSD","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False,"hypothesis_id":z,"evidence_source_sha256":z,"novelty_evidence_sha256":z,"causal_dimension":"NEW_TESTABLE_CAUSE"},"REVIEW_REQUIRED_NOT_AUTHORIZED")]
 if any(gate(x,r)!=y for x,y in cases):raise RuntimeError("NEGATIVE_TESTS")
 doc={"schema_version":1,"kind":"V57_HYPOTHESIS_NOVELTY_GATE_V1","status":"PASS","registry_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"cases_checked":len(cases),"proposal_admitted":False,"novelty_proven":False,"execution_authorized":False,"next":"REQUIRE_EXTERNAL_VERIFIABLE_CAUSAL_EVIDENCE","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"hypothesis_novelty_gate_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"hypothesis_novelty_gate_v1.json")
 print("ALL PASS|HYPOTHESIS_NOVELTY_GATE_V1|TESTS=5|NOVELTY_PROVEN=NO|EXECUTION=DENIED")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|HYPOTHESIS_NOVELTY_GATE_V1|"+str(e));sys.exit(3)
