import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 h=json.loads((S/"refined_hypothesis_v3.json").read_text())
 if h.get("status")!="EXHAUSTED" or h.get("next_action")!="ESCALATE_OR_STOP":raise RuntimeError("BRANCH_NOT_EXHAUSTED")
 aid=h.get("objective",{}).get("agenda_id")
 if not aid:raise RuntimeError("MISSING_AGENDA_ID")
 out={"schema_version":2,"kind":"JARVIS_BRANCH_TERMINAL_V2","status":"TERMINAL_VALID","reason":"HYPOTHESIS_BRANCH_EXHAUSTED","hypothesis_id":h["hypothesis_id"],"agenda_id":aid,"next_action":"RETURN_TO_AGENDA_REPLAN","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"branch_terminal_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"branch_terminal_v2.json")
 print("ALL PASS|BRANCH_TERMINAL_V2|AGENDA="+aid[:12]+"|RETURN_TO_AGENDA_REPLAN")
if __name__=="__main__":main()
