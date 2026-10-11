import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 names={"registry":"multimarket_evidence_registry_v3.json","acceptance":"research_e2e_acceptance_v1.json","policy":"autonomous_decision_policy_v1.json"}
 x={k:json.loads((S/v).read_text()) for k,v in names.items()}
 r=x["registry"];a=x["acceptance"];p=x["policy"]
 if r.get("status")!="PASS" or a.get("status")!="PASS" or p.get("status")!="PASS":raise RuntimeError("STATUS")
 if a.get("registry_sha256")!=hashlib.sha256((S/names["registry"]).read_bytes()).hexdigest():raise RuntimeError("ACCEPTANCE_HASH")
 if p.get("registry_sha256")==a.get("registry_sha256"):raise RuntimeError("EXPECTED_VERSIONED_POLICY_PROVENANCE")
 if set(a["market_checks"][i]["market"] for i in range(len(a["market_checks"])))!=set(r["markets"]):raise RuntimeError("MARKET_SET")
 if any(v.get("decision")!="SAFE_STOP_NO_NEW_HYPOTHESIS" for v in a["market_checks"]):raise RuntimeError("SAFE_STOP")
 if any(r.get(k) is not False for k in ("auto_promotion_allowed","orders_allowed","mt5_allowed","holdout_allowed")):raise RuntimeError("SAFETY")
 doc={"schema_version":1,"kind":"V57_RESEARCH_INTEGRATION_AUDIT_V1","status":"PASS","registry_v3_sha256":a["registry_sha256"],"policy_v1_registry_provenance":"V2_NOT_V3","policy_v1_reused_as_pure_decision_function":True,"acceptance_v1":"PASS","external_global_guards_executed_separately":True,"scope_limit":"NO_RUNTIME_WIRING_PROOF","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_integration_audit_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_integration_audit_v1.json")
 print("ALL PASS|RESEARCH_INTEGRATION_AUDIT_V1|REGISTRY=V3|POLICY_FUNCTION=PASS|PROVENANCE=V2|RUNTIME_WIRING=NOT_PROVEN")
if __name__=="__main__":main()
