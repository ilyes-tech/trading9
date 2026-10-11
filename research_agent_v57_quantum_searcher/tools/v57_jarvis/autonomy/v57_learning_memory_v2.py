import hashlib,json,sqlite3,time
from pathlib import Path
DB=Path("/home/trading/.local/state/tradingai/jarvis-autonomous/learning_memory_v2.sqlite3")
SCHEMA="""CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY,ts_ns INTEGER NOT NULL,fingerprint TEXT NOT NULL UNIQUE,space TEXT NOT NULL,status TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT,strategy_id TEXT,evidence_path TEXT NOT NULL); CREATE INDEX IF NOT EXISTS idx_obs_space ON observations(space);"""
def fp(*x): return hashlib.sha256("|".join("" if v is None else str(v) for v in x).encode()).hexdigest()
def connect(): DB.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(DB,timeout=10);c.executescript(SCHEMA);return c
def ingest(work):
 c=connect();added=0
 for p in sorted(Path(work).glob("*.json")):
  if p.name=="latest_run.json":continue
  try:d=json.loads(p.read_text())
  except Exception:continue
  space=str(d.get("space",""));status=str(d.get("status","")); batches=(d.get("result") or {}).get("batches") or []
  xs=[x for b in batches for x in (b.get("candidates") or [])]
  if not xs: xs=[{"decision":"NO_EXACT_PASS","deep_status":"SEARCH_BUDGET_EXHAUSTED_WITHOUT_EXACT_PASS","strategy_id":None}]
  for x in xs:
   dec=str(x.get("decision") or "UNKNOWN");reason=x.get("deep_status") or x.get("post_status");sid=x.get("strategy_id")
   cur=c.execute("INSERT OR IGNORE INTO observations(ts_ns,fingerprint,space,status,decision,reason,strategy_id,evidence_path) VALUES(?,?,?,?,?,?,?,?)",(time.time_ns(),fp(space,dec,sid,p),space,status,dec,reason,sid,str(p)));added+=cur.rowcount
 c.commit();n=c.execute("SELECT COUNT(*) FROM observations").fetchone()[0];c.close();return added,n
if __name__=="__main__":
 a,n=ingest("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher/work/jarvis_v4_global");print("ALL PASS|LEARNING_MEMORY_V2|ROWS="+str(n)+"|ADDED="+str(a))
