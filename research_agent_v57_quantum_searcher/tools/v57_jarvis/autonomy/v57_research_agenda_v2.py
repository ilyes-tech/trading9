import hashlib,json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"research_agenda_v2.sqlite3"
OBJECTIVES=("IMPROVE_STABILITY","PRESERVE_CONCENTRATION_GATES","EXPLORE_DISTINCT_CAUSAL_DIMENSION")
def main():
 d=json.loads((S/"failure_diagnosis_v2.json").read_text()); term=json.loads((S/"branch_terminal_v2.json").read_text()) if (S/"branch_terminal_v2.json").exists() else {}
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS agenda_v2(id TEXT PRIMARY KEY,created_ns INTEGER,space TEXT,objective TEXT,status TEXT,attempts INTEGER DEFAULT 0,updated_ns INTEGER)" )
 for obj in OBJECTIVES:
  i=hashlib.sha256((d["space"]+"|"+obj).encode()).hexdigest();c.execute("INSERT OR IGNORE INTO agenda_v2 VALUES(?,?,?,?,?,0,?)",(i,time.time_ns(),d["space"],obj,"PENDING",time.time_ns()))
 if term.get("status")=="TERMINAL_VALID" and term.get("agenda_id"):
  c.execute("UPDATE agenda_v2 SET status='EXHAUSTED',updated_ns=? WHERE status='ACTIVE' AND id=?",(time.time_ns(),term["agenda_id"]))
 rows=c.execute("SELECT id,space,objective,status,attempts FROM agenda_v2 ORDER BY created_ns").fetchall()
 if not any(r[3]=="ACTIVE" for r in rows):
  nxt=next((r for r in rows if r[3]=="PENDING"),None)
  if nxt:c.execute("UPDATE agenda_v2 SET status='ACTIVE',attempts=attempts+1,updated_ns=? WHERE id=?",(time.time_ns(),nxt[0]))
 c.commit();rows=c.execute("SELECT id,space,objective,status,attempts FROM agenda_v2 ORDER BY created_ns").fetchall();c.close()
 active=next((r for r in rows if r[3]=="ACTIVE"),None)
 out={"schema_version":2,"kind":"JARVIS_RESEARCH_AGENDA_V2","status":"READY","active":{"id":active[0],"space":active[1],"objective":active[2],"attempts":active[4]} if active else None,"items":[{"id":i,"space":s,"objective":o,"status":st,"attempts":a} for i,s,o,st,a in rows],"rule":"ONE_ACTIVE; STABLE_IDS; EXHAUSTED_NEVER_REACTIVATED; NO_BLIND_SEARCH","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"research_agenda_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"research_agenda_v2.json")
 print("ALL PASS|RESEARCH_AGENDA_V2|ACTIVE="+(active[2] if active else "NONE")+"|EXHAUSTED="+str(sum(r[3]=="EXHAUSTED" for r in rows)))
if __name__=="__main__":main()
