import json,hashlib
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 rows=[];total=0;passed=0
 for market in ("BTCUSD","ETHUSD","XAUUSD"):
  for tf in ("M5","M15","M30","H1"):
   for side in ("LONG","SHORT"):
    space=f"{market}_{tf}_{side}";p=R/"work/jarvis_v4_global"/(space+".json")
    x=json.loads(p.read_text());r=x.get("result",{})
    if x.get("kind")!="V57_JARVIS_V4_SPACE_EVIDENCE" or (x.get("market"),x.get("timeframe"),x.get("side"),x.get("space"))!=(market,tf,side,space):raise RuntimeError("IDENTITY:"+space)
    if any(x.get(k) is not False or r.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed")):raise RuntimeError("SAFETY:"+space)
    if x.get("status")!="SEARCH_BUDGET_EXHAUSTED" or r.get("status")!="SEARCH_BUDGET_EXHAUSTED":raise RuntimeError("STATUS:"+space)
    batches=r.get("batches")
    if not isinstance(batches,list) or not batches:raise RuntimeError("BATCHES:"+space)
    count=0;success=0
    for b in batches:
     n=b.get("total");e=b.get("exact_pass")
     if not isinstance(n,int) or not isinstance(e,int) or not 0<=e<=n:raise RuntimeError("COUNTS:"+space)
     count+=n;success+=e
    rows.append({"space":space,"candidates_checked":count,"exact_pass_reported":success,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    total+=count;passed+=success
 doc={"schema_version":1,"kind":"V57_CRYPTO_GOLD_EVIDENCE_AUDIT_V1","status":"PASS","source":"JARVIS_V4_GLOBAL_SPACE_EVIDENCE","spaces":rows,"spaces_checked":len(rows),"candidates_checked":total,"exact_pass_reported":passed,"scope_limit":"V4_BOUNDED_SEARCH_ONLY_NOT_ALL_POSSIBLE_STRATEGIES","new_evaluation_started":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"crypto_gold_evidence_audit_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"crypto_gold_evidence_audit_v1.json")
 print(f"ALL PASS|CRYPTO_GOLD_EVIDENCE_AUDIT_V1|SPACES={len(rows)}|CHECKED={total}|EXACT={passed}|EVALUATION=FALSE")
if __name__=="__main__":main()
