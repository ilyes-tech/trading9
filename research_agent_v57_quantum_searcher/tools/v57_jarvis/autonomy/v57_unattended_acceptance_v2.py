import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");J=S/"journal_v4.jsonl"
def main():
 rows=[]
 if J.exists():
  for x in J.read_text().splitlines():
   try:rows.append(json.loads(x))
   except:pass
 good=[r for r in rows if r.get("status")=="PASS" and r.get("phase")=="AUTONOMOUS_COGNITIVE_LOOP" and r.get("searcher_role")=="OPTIONAL_TOOL" and not r.get("research_execution_authorized",False) and not r.get("orders_allowed",False) and not r.get("mt5_allowed",False) and not r.get("holdout_allowed",False)]
 consecutive=0
 for r in reversed(rows):
  if r in good:consecutive+=1
  else:break
 ok=consecutive>=3
 out={"schema_version":2,"kind":"JARVIS_UNATTENDED_ACCEPTANCE_V2","status":"PASS" if ok else "PENDING","verified_consecutive_cycles":consecutive,"required_cycles":3,"journal_rows":len(rows),"scope":"COGNITIVE_AUTONOMY_NO_MARKET_EXECUTION"}
 t=S/"unattended_acceptance_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"unattended_acceptance_v2.json")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|UNATTENDED_ACCEPTANCE_V2|CONSECUTIVE="+str(consecutive)+"|REQUIRED=3")
if __name__=="__main__":main()
