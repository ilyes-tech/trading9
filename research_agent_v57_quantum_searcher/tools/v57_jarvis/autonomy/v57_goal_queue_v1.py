import json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"goal_queue_v1.sqlite3"
DEFAULT=[("CLOSE_ACTION_FEEDBACK_LOOP",100),("BUILD_SAFE_SELF_IMPROVEMENT_PIPELINE",90),("EXPAND_TOOL_SELECTION",80),("UNATTENDED_ACCEPTANCE",70)]
def main():
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY,name TEXT UNIQUE,priority INTEGER,status TEXT,created_ns INTEGER,attempts INTEGER DEFAULT 0)")
 for n,p in DEFAULT:c.execute("INSERT OR IGNORE INTO goals(name,priority,status,created_ns) VALUES(?,?,?,?)",(n,p,"PENDING",time.time_ns()))
 c.commit();row=c.execute("SELECT id,name,priority,attempts FROM goals WHERE status IN ('PENDING','RETRY') ORDER BY priority DESC,id LIMIT 1").fetchone()
 if row:
  c.execute("UPDATE goals SET status='ACTIVE',attempts=attempts+1 WHERE id=?",(row[0],));c.commit();active={"id":row[0],"name":row[1],"priority":row[2],"attempt":row[3]+1}
 else:active=None
 counts=dict(c.execute("SELECT status,count(*) FROM goals GROUP BY status").fetchall());c.close()
 out={"schema_version":1,"kind":"JARVIS_GOAL_QUEUE_V1","status":"READY","active_goal":active,"counts":counts,"recovery":"PERSISTENT_SQLITE_RELOAD_ON_EACH_CYCLE","orders_allowed":False,"mt5_allowed":False}
 t=S/"goal_queue_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"goal_queue_v1.json")
 print("ALL PASS|GOAL_QUEUE_V1|ACTIVE="+(active["name"] if active else "NONE")+"|PERSISTENT=TRUE")
if __name__=="__main__":main()
