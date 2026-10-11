import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
def get(p,kind):
 x=json.loads(p.read_text())
 if x.get("kind")!=kind:raise RuntimeError("KIND:"+p.name)
 return x,hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old,oh=get(S/"multimarket_evidence_registry_v2.json","V57_MULTIMARKET_EVIDENCE_REGISTRY_V2")
 audit,ah=get(S/"crypto_gold_evidence_audit_v1.json","V57_CRYPTO_GOLD_EVIDENCE_AUDIT_V1")
 candidate,sh=get(R/"work/jarvis_v4_global/XAUUSD_M5_SHORT.json","V57_JARVIS_V4_SPACE_EVIDENCE")
 b=candidate["result"]["batches"][0];matches=b["candidates"]
 if audit["spaces_checked"]!=24 or audit["candidates_checked"]!=768 or audit["exact_pass_reported"]!=1:raise RuntimeError("AUDIT")
 if b["exact_pass"]!=1 or len(matches)!=1 or matches[0]["decision"]!="REJECTED_DEEP" or matches[0]["deep_status"]!="DEEP_REJECT":raise RuntimeError("CANDIDATE_GATE")
 markets=json.loads(json.dumps(old["markets"]))
 for m in ("BTCUSD","ETHUSD","XAUUSD"):
  rr=[r for r in audit["spaces"] if r["space"].startswith(m+"_")]
  n=sum(r["candidates_checked"] for r in rr);passed=sum(r["exact_pass_reported"] for r in rr)
  if len(rr)!=8 or n!=256 or passed!=(1 if m=="XAUUSD" else 0):raise RuntimeError("MARKET_COUNTS:"+m)
  markets[m].update({"market_specific_outcome":"HISTORICAL_V4_DEEP_REJECT" if m=="XAUUSD" else "HISTORICAL_V4_NO_EXACT_PASS","spaces_checked":8,"candidates_checked":n,"initial_exact_pass":passed,"admitted":0,"source_sha256":ah})
 doc={"schema_version":3,"kind":"V57_MULTIMARKET_EVIDENCE_REGISTRY_V3","status":"PASS","markets":markets,"branches":old["branches"],"source_registry_v2_sha256":oh,"source_crypto_gold_audit_sha256":ah,"xau_initial_candidate":{"strategy_id":matches[0]["strategy_id"],"decision":"REJECTED_DEEP","source_sha256":sh},"all_seven_markets_have_historical_evidence":True,"deployable_strategy_proven":False,"auto_promotion_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"next_gate":"END_TO_END_RESEARCH_ONLY_ACCEPTANCE"}
 q=S/"multimarket_evidence_registry_v3.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"multimarket_evidence_registry_v3.json")
 print("ALL PASS|MULTIMARKET_EVIDENCE_REGISTRY_V3|MARKETS=7/7|XAU_INITIAL=1|XAU_DEEP=REJECT|DEPLOYABLE=0")
if __name__=="__main__":main()
