import json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
DB=S/"executive_v1.sqlite3"
def main():
 plan=json.loads((S/"experiment_plan_v1.json").read_text())["plan"]; status=json.loads((S/"status_v2.json").read_text())
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY,ts_ns INTEGER,action_key TEXT UNIQUE,status TEXT,reason TEXT)")
 key=plan["hypothesis_id"]+":BOUNDED_EXPERIMENT"
 old=c.execute("SELECT status FROM actions WHERE action_key=?",(key,)).fetchone()
 if old: decision="SKIP_ALREADY_DECIDED";reason=old[0]
 elif status.get("compute_gate")!="PASS":decision="WAIT";reason="RESOURCE_GATE"
 elif plan.get("execution_mode")!="PLAN_ONLY":decision="DENY";reason="UNEXPECTED_MODE"
 else:
  decision="DEFER";reason="NO_ALLOWLISTED_CAUSAL_OPERATOR"
  c.execute("INSERT OR IGNORE INTO actions(ts_ns,action_key,status,reason) VALUES(?,?,?,?)",(time.time_ns(),key,decision,reason));c.commit()
 c.close()
 out={"schema_version":1,"kind":"JARVIS_EXECUTIVE_V1","status":"PASS","decision":decision,"reason":reason,
 "principle":"EXECUTE_ONLY_WHEN_ACTION_IS_ALLOWLISTED_AND_CAUSALLY_JUSTIFIED","searcher_invoked":False,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"executive_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"executive_v1.json")
 print("ALL PASS|EXECUTIVE_V1|DECISION="+decision+"|REASON="+reason+"|SEARCHER=NOT_INVOKED")
if __name__=="__main__":main()
