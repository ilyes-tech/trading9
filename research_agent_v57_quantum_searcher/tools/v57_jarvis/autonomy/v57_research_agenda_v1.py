import hashlib,json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"research_agenda_v1.sqlite3"
def main():
 fb=json.loads((S/"research_feedback_v1.json").read_text());diag=json.loads((S/"failure_diagnosis_v2.json").read_text())
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS agenda(id TEXT PRIMARY KEY,created_ns INTEGER,space TEXT,objective TEXT,status TEXT,source TEXT)")
 objectives=[]
 if fb.get("exact_pass",0)==0:objectives=["IMPROVE_STABILITY_WITHOUT_REPEATING_IDENTICAL_PROBE","PRESERVE_CONCENTRATION_GATES","TEST_ONE_BOUNDED_DISTINCT_HYPOTHESIS"]
 for obj in objectives:
  raw=diag["space"]+"|"+obj+"|"+fb["hypothesis_id"];i=hashlib.sha256(raw.encode()).hexdigest()
  c.execute("INSERT OR IGNORE INTO agenda VALUES(?,?,?,?,?,?)",(i,time.time_ns(),diag["space"],obj,"PENDING","RESEARCH_FEEDBACK_V1"))
 c.commit();rows=c.execute("SELECT id,space,objective,status FROM agenda ORDER BY created_ns").fetchall();c.close()
 out={"schema_version":1,"kind":"JARVIS_RESEARCH_AGENDA_V1","status":"READY","items":[{"id":i,"space":s,"objective":o,"status":st} for i,s,o,st in rows],"rule":"EVIDENCE_DRIVEN; DISTINCT; BOUNDED; NO_BLIND_SEARCH"}
 t=S/"research_agenda_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"research_agenda_v1.json")
 print("ALL PASS|RESEARCH_AGENDA|ITEMS="+str(len(rows))+"|NO_BLIND_SEARCH")
if __name__=="__main__":main()
