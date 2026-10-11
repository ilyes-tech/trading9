import json,sqlite3,time
from pathlib import Path
DB=Path("/home/trading/.local/state/tradingai/jarvis-v438/learning_memory_v1.sqlite3")
SCHEMA="""CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY,ts_ns INTEGER NOT NULL,space TEXT NOT NULL,status TEXT NOT NULL,decision TEXT,reason TEXT,strategy_id TEXT,evidence_path TEXT NOT NULL,UNIQUE(evidence_path,strategy_id,decision)); CREATE INDEX IF NOT EXISTS idx_obs_space ON observations(space);"""
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(DB,timeout=10); c.executescript(SCHEMA); return c
def ingest(work):
 c=connect(); added=0
 for p in sorted(Path(work).glob("*.json")):
  if p.name=="latest_run.json": continue
  try: d=json.loads(p.read_text())
  except Exception: continue
  space=str(d.get("space","")); status=str(d.get("status",""))
  batches=(d.get("result") or {}).get("batches") or []
  candidates=[x for b in batches for x in (b.get("candidates") or [])]
  if not candidates:
   cur=c.execute("INSERT OR IGNORE INTO observations(ts_ns,space,status,decision,reason,strategy_id,evidence_path) VALUES(?,?,?,?,?,?,?)",(time.time_ns(),space,status,"NO_EXACT_PASS","SEARCH_BUDGET_EXHAUSTED_WITHOUT_EXACT_PASS",None,str(p)))
   added+=cur.rowcount
  for x in candidates:
   cur=c.execute("INSERT OR IGNORE INTO observations(ts_ns,space,status,decision,reason,strategy_id,evidence_path) VALUES(?,?,?,?,?,?,?)",(time.time_ns(),space,status,x.get("decision"),x.get("deep_status") or x.get("post_status"),x.get("strategy_id"),str(p)))
   added+=cur.rowcount
 c.commit(); c.close(); return added
def summary():
 c=connect()
 rows=c.execute("SELECT space,status,COALESCE(decision,'NO_CANDIDATE'),COUNT(*) FROM observations GROUP BY space,status,COALESCE(decision,'NO_CANDIDATE') ORDER BY space").fetchall()
 total=c.execute("SELECT COUNT(*) FROM observations").fetchone()[0]; c.close()
 return {"rows":total,"by_space":[{"space":a,"status":b,"decision":d,"count":n} for a,b,d,n in rows]}
if __name__=="__main__":
 a=ingest("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/work/jarvis_v4_global"); print(json.dumps({"status":"PASS","added":a,"summary":summary()},sort_keys=True))
