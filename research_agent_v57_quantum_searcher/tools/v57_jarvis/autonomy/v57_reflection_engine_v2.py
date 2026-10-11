import json,sqlite3
from collections import Counter
from pathlib import Path
DB=Path("/home/trading/.local/state/tradingai/jarvis-autonomous/learning_memory_v2.sqlite3")
OUT=Path("/home/trading/.local/state/tradingai/jarvis-autonomous/reflection_v2.json")
def main():
 c=sqlite3.connect(DB);rows=c.execute("SELECT space,status,decision,reason,strategy_id,evidence_path FROM observations ORDER BY id").fetchall();c.close()
 if not rows:raise RuntimeError("NO_MEMORY")
 decisions=Counter(r[2] for r in rows);deep=[r for r in rows if r[2]=="REJECTED_DEEP"]
 focus=[{"space":r[0],"reason":r[3],"strategy_id":r[4],"priority":"ANALYZE_DEEP_REJECTION"} for r in deep]
 x={"schema_version":2,"kind":"JARVIS_REFLECTION_V2","status":"READY","observations":len(rows),"decision_counts":dict(decisions),
 "interpretation":{"dominant_failure":"NO_EXACT_PASS" if decisions.get("NO_EXACT_PASS",0)>len(rows)/2 else "MIXED","deep_rejections":len(deep),
 "rule":"LEARN_BEFORE_COMPUTE; NEVER_REPEAT_IDENTICAL_FAILED_ACTION"},
 "focus":focus,"next_action":"ANALYZE_EXISTING_DEEP_EVIDENCE" if deep else "FORM_NEW_HYPOTHESIS",
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 OUT.parent.mkdir(parents=True,exist_ok=True);t=OUT.with_suffix(".tmp");t.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n");t.replace(OUT)
 print("ALL PASS|REFLECTION_V2|OBS="+str(len(rows))+"|NEXT="+x["next_action"])
if __name__=="__main__":main()
