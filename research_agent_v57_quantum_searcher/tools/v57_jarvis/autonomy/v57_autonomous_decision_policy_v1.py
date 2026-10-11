import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def decide(market,registry,proposal=None):
 if market not in registry["markets"]:return "DENY_UNKNOWN_MARKET"
 evidence=registry["markets"][market]
 if proposal is None:return "SAFE_STOP_NO_NEW_HYPOTHESIS"
 if not isinstance(proposal,dict):return "DENY_MALFORMED_HYPOTHESIS"
 required=("hypothesis_id","causal_dimension","evidence_source_sha256","novelty_evidence_sha256")
 if any(not isinstance(proposal.get(k),str) or len(proposal[k])!=64 or any(c not in "0123456789abcdef" for c in proposal[k]) for k in ("hypothesis_id","evidence_source_sha256","novelty_evidence_sha256")):return "DENY_UNVERIFIED_HYPOTHESIS"
 if not isinstance(proposal.get("causal_dimension"),str) or not proposal["causal_dimension"].strip():return "DENY_MALFORMED_HYPOTHESIS"
 if proposal.get("market")!=market:return "DENY_MARKET_MISMATCH"
 if proposal.get("orders_allowed") is not False or proposal.get("mt5_allowed") is not False or proposal.get("holdout_allowed") is not False:return "DENY_UNSAFE_PROPOSAL"
 return "REVIEW_REQUIRED_NOT_AUTHORIZED"
def main():
 p=S/"multimarket_evidence_registry_v2.json";r=json.loads(p.read_text())
 if r.get("kind")!="V57_MULTIMARKET_EVIDENCE_REGISTRY_V2" or r.get("status")!="PASS" or r.get("auto_promotion_allowed") is not False:raise RuntimeError("REGISTRY_GATE")
 results={m:decide(m,r) for m in r["markets"]}
 if len(results)!=7 or set(results.values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"}:raise RuntimeError("DECISION_GATE")
 if decide("UNKNOWN",r)!="DENY_UNKNOWN_MARKET" or decide("EURUSD",r,{})!="DENY_UNVERIFIED_HYPOTHESIS":raise RuntimeError("NEGATIVE_TEST_FAILED")
 doc={"schema_version":1,"kind":"V57_AUTONOMOUS_DECISION_POLICY_V1","status":"PASS","registry_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"market_decisions":results,"new_hypothesis_handling":"REVIEW_REQUIRED_NOT_AUTHORIZED","execution_authorized":False,"auto_promotion_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"autonomous_decision_policy_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"autonomous_decision_policy_v1.json")
 print("ALL PASS|AUTONOMOUS_DECISION_POLICY_V1|MARKETS=7|SAFE_STOP=7|NEGATIVE_TESTS=2|EXECUTION=DENIED")
if __name__=="__main__":main()
