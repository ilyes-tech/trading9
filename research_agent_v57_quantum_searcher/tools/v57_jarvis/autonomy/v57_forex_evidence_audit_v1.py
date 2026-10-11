import json,hashlib
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 root=R/"work/jarvis_v4_global";records=[];tot=0;exact=0
 for market in ("EURUSD","GBPUSD","USDJPY"):
  for tf in ("M5","M15","M30","H1"):
   for side in ("LONG","SHORT"):
    name=f"{market}_{tf}_{side}";path=root/(name+".json")
    if not path.is_file():raise RuntimeError("MISSING:"+name)
    x=json.loads(path.read_text());r=x.get("result",{})
    if x.get("kind")!="V57_JARVIS_V4_SPACE_EVIDENCE" or x.get("market")!=market or x.get("timeframe")!=tf or x.get("side")!=side or x.get("space")!=name:raise RuntimeError("IDENTITY:"+name)
    if x.get("orders_allowed") is not False or x.get("mt5_allowed") is not False or x.get("holdout_allowed") is not False:raise RuntimeError("UNSAFE:"+name)
    if r.get("status")!="SEARCH_BUDGET_EXHAUSTED" or x.get("status")!="SEARCH_BUDGET_EXHAUSTED":raise RuntimeError("NOT_TERMINAL:"+name)
    batches=r.get("batches",[])
    if len(batches)!=1 or not isinstance(batches[0].get("candidates"),list):raise RuntimeError("BATCH_FORMAT:"+name)
    n=batches[0].get("total");passed=batches[0].get("exact_pass")
    if not isinstance(n,int) or not isinstance(passed,int) or n<0 or passed<0 or passed>n:raise RuntimeError("COUNT:"+name)
    tot+=n;exact+=passed
    records.append({"space":name,"candidates_checked":n,"exact_pass":passed,"returned_candidates":len(batches[0]["candidates"]),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
 doc={"schema_version":1,"kind":"V57_FOREX_EVIDENCE_AUDIT_V1","status":"PASS","source":"JARVIS_V4_GLOBAL_SPACE_EVIDENCE","spaces":records,"spaces_checked":len(records),"candidates_checked":tot,"exact_pass_reported":exact,"scope_limit":"SEARCH_BUDGET_EXHAUSTED_DOES_NOT_PROVE_ALL_FOREX_STRATEGIES_EXHAUSTED","new_evaluation_started":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"forex_evidence_audit_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"forex_evidence_audit_v1.json")
 print(f"ALL PASS|FOREX_EVIDENCE_AUDIT_V1|SPACES={len(records)}|CHECKED={tot}|EXACT={exact}|NEW_EVALUATION=FALSE")
if __name__=="__main__":main()
