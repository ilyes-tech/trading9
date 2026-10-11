import hashlib,json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
DB=S/"research_agenda_v1.sqlite3"
PRIORITY=("PRESERVE_CONCENTRATION_GATES","TEST_ONE_BOUNDED_DISTINCT_HYPOTHESIS","IMPROVE_STABILITY_WITHOUT_REPEATING_IDENTICAL_PROBE")
def main():
 c=sqlite3.connect(DB); c.execute("BEGIN IMMEDIATE")
 rows=c.execute("SELECT id,space,objective,status FROM agenda WHERE status='PENDING'").fetchall()
 if not rows:
  c.commit();c.close();print("ALL PASS|AGENDA_ORCHESTRATOR|IDLE|NO_PENDING");return
 rank={x:i for i,x in enumerate(PRIORITY)}; row=min(rows,key=lambda r:(rank.get(r[2],99),r[0])); aid,space,obj,_=row
 active=c.execute("SELECT count(*) FROM agenda WHERE status='ACTIVE'").fetchone()[0]
 if active: c.commit();c.close();print("STOP|FAIL|AGENDA_ORCHESTRATOR|ACTIVE_EXISTS");return
 c.execute("UPDATE agenda SET status='ACTIVE' WHERE id=? AND status='PENDING'",(aid,));c.commit();c.close()
 token=hashlib.sha256((aid+'|'+obj).encode()).hexdigest()
 out={"schema_version":1,"kind":"JARVIS_AGENDA_SELECTION_V1","status":"ACTIVE","agenda_id":aid,"space":space,"objective":obj,"selection_token":token,"rule":"ONE_ACTIVE; DETERMINISTIC; SAFETY_FIRST; NO_BLIND_SEARCH","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"agenda_selection_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"agenda_selection_v1.json")
 print("ALL PASS|AGENDA_ORCHESTRATOR|ACTIVE="+obj+"|SEARCHER=NOT_INVOKED")
if __name__=="__main__":main()
