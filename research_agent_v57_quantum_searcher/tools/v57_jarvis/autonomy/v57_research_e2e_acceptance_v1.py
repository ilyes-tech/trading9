import json,hashlib,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v57_autonomous_decision_policy_v1 import decide
def main():
 p=S/"multimarket_evidence_registry_v3.json";r=json.loads(p.read_text())
 if r.get("kind")!="V57_MULTIMARKET_EVIDENCE_REGISTRY_V3" or r.get("status")!="PASS":raise RuntimeError("REGISTRY")
 if set(r["markets"])!={"BTCUSD","ETHUSD","LTCUSD","EURUSD","GBPUSD","USDJPY","XAUUSD"}:raise RuntimeError("MARKET_COVERAGE")
 if r.get("deployable_strategy_proven") is not False or r.get("auto_promotion_allowed") is not False:raise RuntimeError("PROMOTION")
 if any(r.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed")):raise RuntimeError("SAFETY")
 checks=[]
 for market in sorted(r["markets"]):
  result=decide(market,r)
  if result!="SAFE_STOP_NO_NEW_HYPOTHESIS":raise RuntimeError("DECISION:"+market)
  checks.append({"market":market,"decision":result})
 if decide("INVALID",r)!="DENY_UNKNOWN_MARKET":raise RuntimeError("UNKNOWN_MARKET")
 if decide("XAUUSD",r,{"strategy_id":r["xau_initial_candidate"]["strategy_id"]})!="DENY_UNVERIFIED_HYPOTHESIS":raise RuntimeError("REJECTED_CANDIDATE")
 validshape={"market":"XAUUSD","hypothesis_id":"a"*64,"evidence_source_sha256":"b"*64,"novelty_evidence_sha256":"c"*64,"causal_dimension":"unverified","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 if decide("XAUUSD",r,validshape)!="REVIEW_REQUIRED_NOT_AUTHORIZED":raise RuntimeError("NO_AUTO_APPROVAL")
 unsafe=dict(validshape,orders_allowed=True)
 if decide("XAUUSD",r,unsafe)!="DENY_UNSAFE_PROPOSAL":raise RuntimeError("UNSAFE_GATE")
 doc={"schema_version":1,"kind":"V57_RESEARCH_E2E_ACCEPTANCE_V1","status":"PASS","registry_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"market_checks":checks,"negative_tests":["UNKNOWN_MARKET","REJECTED_CANDIDATE","UNVERIFIED_HYPOTHESIS_NO_AUTO_APPROVAL","UNSAFE_PROPOSAL"],"scope":"POLICY_LEVEL_ONLY_NO_EXECUTION_CONNECTOR_TESTED","execution_authorized":False,"auto_promotion_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"research_e2e_acceptance_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_e2e_acceptance_v1.json")
 print("ALL PASS|RESEARCH_E2E_ACCEPTANCE_V1|MARKETS=7|SAFE_STOP=7|NEGATIVE_TESTS=4|SCOPE=POLICY_ONLY")
if __name__=="__main__":main()
