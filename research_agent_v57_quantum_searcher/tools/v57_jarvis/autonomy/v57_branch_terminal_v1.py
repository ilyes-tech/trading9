#!/usr/bin/env python3
import json,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
h=json.loads((S/"refined_hypothesis_v1.json").read_text())
assert h.get("status")=="EXHAUSTED" and h.get("next_action")=="ESCALATE_OR_STOP"
out={"schema_version":1,"kind":"JARVIS_BRANCH_TERMINAL_V1","status":"TERMINAL_VALID","reason":"HYPOTHESIS_BRANCH_EXHAUSTED","hypothesis_id":h["hypothesis_id"],"next_action":"RETURN_TO_AGENDA_REPLAN","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False,"ts_ns":time.time_ns()}
t=S/"branch_terminal_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"branch_terminal_v1.json")
print("ALL PASS|BRANCH_TERMINAL|EXHAUSTED|RETURN_TO_AGENDA_REPLAN")
