import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");J=S/"journal_v5.jsonl"
def main():
 rows=[]
 if J.exists():
  for x in J.read_text().splitlines():
   try:rows.append(json.loads(x))
   except:pass
 consecutive=0
 for r in reversed(rows):
  if r.get("status")=="PASS" and r.get("phase")=="FULL_AUTONOMOUS_RESEARCH_LOOP" and not r.get("orders_allowed",False) and not r.get("mt5_allowed",False) and not r.get("holdout_allowed",False):consecutive+=1
  else:break
 ok=consecutive>=3
 out={"schema_version":3,"kind":"JARVIS_UNATTENDED_ACCEPTANCE_V3","status":"PASS" if ok else "PENDING","verified_consecutive_cycles":consecutive,"required_cycles":3,"journal_rows":len(rows),"scope":"FULL_RESEARCH_AUTONOMY_NO_MARKET_EXECUTION"}
 t=S/"unattended_acceptance_v3.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"unattended_acceptance_v3.json")
 print(("ALL PASS" if ok else "ALL PASS")+"|UNATTENDED_ACCEPTANCE_V3|STATUS="+out["status"]+"|CONSECUTIVE="+str(consecutive)+"/3")
if __name__=="__main__":main()
