import json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"research_agenda_v3.sqlite3"
def main():
 old=json.loads((S/"research_agenda_v2.json").read_text());rp=json.loads((S/"agenda_replanner_v1.json").read_text());term=json.loads((S/"branch_terminal_v2.json").read_text()) if (S/"branch_terminal_v2.json").exists() else {}
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS agenda_v3(id TEXT PRIMARY KEY,created_ns INTEGER,space TEXT,objective TEXT,status TEXT,attempts INTEGER DEFAULT 0,source TEXT,updated_ns INTEGER)")
 for x in old.get("items",[]):c.execute("INSERT OR IGNORE INTO agenda_v3 VALUES(?,?,?,?,?,?,?,?)",(x["id"],time.time_ns(),x["space"],x["objective"],x["status"],x.get("attempts",0),"AGENDA_V2_IMPORT",time.time_ns()))
 p=rp.get("proposal")
 if rp.get("decision")=="PROPOSE_ONE_NEW_OBJECTIVE" and p:
  if p.get("causal_dimension")!="TIME_FILTER":raise RuntimeError("REPLAN_DIMENSION_NOT_TIME_FILTER")
  c.execute("INSERT OR IGNORE INTO agenda_v3 VALUES(?,?,?,?,?,?,?,?)",(p["id"],time.time_ns(),p["space"],p["objective"],"PENDING",0,"REPLANNER_V1",time.time_ns()))
 if term.get("status")=="TERMINAL_VALID" and term.get("agenda_id"):c.execute("UPDATE agenda_v3 SET status='EXHAUSTED',updated_ns=? WHERE status='ACTIVE' AND id=?",(time.time_ns(),term["agenda_id"]))
 rows=c.execute("SELECT id,space,objective,status,attempts,source FROM agenda_v3 ORDER BY created_ns").fetchall()
 if not any(r[3]=="ACTIVE" for r in rows):
  nxt=next((r for r in rows if r[3]=="PENDING"),None)
  if nxt:c.execute("UPDATE agenda_v3 SET status='ACTIVE',attempts=attempts+1,updated_ns=? WHERE id=?",(time.time_ns(),nxt[0]))
 c.commit();rows=c.execute("SELECT id,space,objective,status,attempts,source FROM agenda_v3 ORDER BY created_ns").fetchall();c.close();active=next((r for r in rows if r[3]=="ACTIVE"),None)
 out={"schema_version":3,"kind":"JARVIS_RESEARCH_AGENDA_V3","status":"READY","active":{"id":active[0],"space":active[1],"objective":active[2],"attempts":active[4],"source":active[5]} if active else None,"items":[{"id":i,"space":s,"objective":o,"status":st,"attempts":a,"source":src} for i,s,o,st,a,src in rows],"rule":"IMPORT_HISTORY; ONE_REPLANNER_PROPOSAL; ONE_ACTIVE; EXHAUSTED_NEVER_REACTIVATED","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("research_agenda_v3.json","research_agenda_v2.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 print("ALL PASS|RESEARCH_AGENDA_V3|ACTIVE="+(active[2] if active else "NONE")+"|ITEMS="+str(len(rows)))
if __name__=="__main__":main()
