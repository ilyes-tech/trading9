import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 a=json.loads((S/"research_agenda_v2.json").read_text());active=a.get("active");items=a.get("items",[])
 if active:raise RuntimeError("AGENDA_STILL_ACTIVE")
 if not items or any(x.get("status")!="EXHAUSTED" for x in items):raise RuntimeError("AGENDA_NOT_FULLY_EXHAUSTED")
 out={"schema_version":1,"kind":"JARVIS_AGENDA_TERMINAL_V1","status":"AGENDA_EXHAUSTED","exhausted_count":len(items),"space":items[0].get("space"),"reason":"ALL_BOUNDED_AGENDA_BRANCHES_EXHAUSTED","next_action":"REPLAN_WITH_NEW_EVIDENCE_OR_SAFE_STOP","research_execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"agenda_terminal_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"agenda_terminal_v1.json")
 print("ALL PASS|AGENDA_TERMINAL_V1|EXHAUSTED="+str(len(items))+"|NEXT=REPLAN_WITH_NEW_EVIDENCE_OR_SAFE_STOP")
if __name__=="__main__":main()
