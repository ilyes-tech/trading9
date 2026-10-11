import json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"executive_v2.sqlite3"
def main():
 core=json.loads((S/"status_v2.json").read_text());op=json.loads((S/"causal_operator_v1.json").read_text())
 key=op.get("design_id","");c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS decisions(k TEXT PRIMARY KEY,ts_ns INTEGER,decision TEXT,reason TEXT)")
 old=c.execute("SELECT decision,reason FROM decisions WHERE k=?",(key,)).fetchone() if key else None
 if old:decision,reason="SKIP_ALREADY_DECIDED",old[0]
 elif core.get("compute_gate")!="PASS":decision,reason="WAIT","RESOURCE_GATE"
 elif op.get("status")!="READY":decision,reason="DENY","OPERATOR_NOT_READY"
 else:decision,reason="AUTHORIZE_DESIGN","BOUNDED_CAUSAL_OPERATOR_READY";c.execute("INSERT OR IGNORE INTO decisions VALUES(?,?,?,?)",(key,time.time_ns(),decision,reason));c.commit()
 c.close()
 out={"schema_version":2,"kind":"JARVIS_EXECUTIVE_V2","status":"PASS","decision":decision,"reason":reason,
 "authorized_scope":"DESIGN_ONLY","research_execution_authorized":False,"searcher_invoked":False,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"executive_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"executive_v2.json")
 print("ALL PASS|EXECUTIVE_V2|"+decision+"|SCOPE=DESIGN_ONLY|SEARCHER=NOT_INVOKED")
if __name__=="__main__":main()
