import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def read(name,kind):
 p=S/name;x=json.loads(p.read_text())
 if x.get("kind")!=kind:raise RuntimeError("SOURCE_KIND:"+name)
 return x,hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 old,oh=read("multimarket_evidence_registry_v1.json","V57_MULTIMARKET_EVIDENCE_REGISTRY_V1")
 fx,fh=read("forex_evidence_audit_v1.json","V57_FOREX_EVIDENCE_AUDIT_V1")
 if old.get("status")!="PASS" or fx.get("status")!="PASS" or fx.get("spaces_checked")!=24 or fx.get("candidates_checked")!=768 or fx.get("exact_pass_reported")!=0:raise RuntimeError("EVIDENCE_GATE")
 markets=json.loads(json.dumps(old["markets"]))
 for market in ("EURUSD","GBPUSD","USDJPY"):
  rows=[r for r in fx["spaces"] if r["space"].startswith(market+"_")]
  if len(rows)!=8 or sum(r["candidates_checked"] for r in rows)!=256 or sum(r["exact_pass"] for r in rows)!=0:raise RuntimeError("FOREX_MARKET_MISMATCH:"+market)
  markets[market].update({"market_specific_outcome":"HISTORICAL_V4_PROBE_NO_EXACT_PASS","spaces_checked":8,"candidates_checked":256,"exact_pass":0,"source_sha256":fh})
 doc={"schema_version":2,"kind":"V57_MULTIMARKET_EVIDENCE_REGISTRY_V2","status":"PASS","markets":markets,"branches":old["branches"],"source_registry_v1_sha256":oh,"source_forex_audit_v1_sha256":fh,"research_decision":"SAFE_STOP_UNLESS_DISTINCT_EVIDENCE_BACKED_HYPOTHESIS","market_specific_unknowns":["BTCUSD","ETHUSD","XAUUSD"],"auto_promotion_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"next_gate":"AUTONOMOUS_DECISION_POLICY"}
 q=S/"multimarket_evidence_registry_v2.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"multimarket_evidence_registry_v2.json")
 print("ALL PASS|MULTIMARKET_EVIDENCE_REGISTRY_V2|MARKETS=7|FOREX=3/3|FOREX_EXACT=0|UNAUDITED=3|PROMOTION=DENIED")
if __name__=="__main__":main()
