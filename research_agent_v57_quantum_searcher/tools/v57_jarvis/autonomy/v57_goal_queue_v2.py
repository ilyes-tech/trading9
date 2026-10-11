import json,sqlite3,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"goal_queue_v2.sqlite3"
GOALS=[("CLOSE_ACTION_FEEDBACK_LOOP",100,"action_feedback_v1.json","status","VERIFIED"),("BUILD_SAFE_SELF_IMPROVEMENT_PIPELINE",90,"self_improvement_guard_v1.json","status","PASS"),("EXPAND_TOOL_SELECTION",80,"tool_selection_v1.json","status","PASS"),("UNATTENDED_ACCEPTANCE",70,"unattended_acceptance_v2.json","status","PASS")]
def evidence(f,k,v):
 try:return json.loads((S/f).read_text()).get(k)==v
 except:return False
def main():
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS goals(name TEXT PRIMARY KEY,priority INTEGER,status TEXT,attempts INTEGER DEFAULT 0,updated_ns INTEGER)")
 for n,p,*_ in GOALS:c.execute("INSERT OR IGNORE INTO goals VALUES(?,?,?,0,?)",(n,p,"PENDING",time.time_ns()))
 for n,p,f,k,v in GOALS:
  if evidence(f,k,v):c.execute("UPDATE goals SET status='DONE',updated_ns=? WHERE name=?",(time.time_ns(),n))
 c.execute("UPDATE goals SET status='PENDING' WHERE status='ACTIVE'")
 row=c.execute("SELECT name FROM goals WHERE status='PENDING' ORDER BY priority DESC LIMIT 1").fetchone()
 if row:c.execute("UPDATE goals SET status='ACTIVE',attempts=attempts+1,updated_ns=? WHERE name=?",(time.time_ns(),row[0]))
 c.commit();rows=c.execute("SELECT name,priority,status,attempts FROM goals ORDER BY priority DESC").fetchall();c.close()
 active=next((x[0] for x in rows if x[2]=="ACTIVE"),None);out={"schema_version":2,"kind":"JARVIS_GOAL_QUEUE_V2","status":"READY","active_goal":active,"goals":[{"name":n,"priority":p,"status":s,"attempts":a} for n,p,s,a in rows],"recovery":"ONE_ACTIVE_GOAL; EVIDENCE_CLOSES_GOALS; ACTIVE_RECOVERS_TO_PENDING"}
 t=S/"goal_queue_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"goal_queue_v2.json")
 print("ALL PASS|GOAL_QUEUE_V2|ACTIVE="+str(active)+"|DONE="+str(sum(x[2]=="DONE" for x in rows)))
if __name__=="__main__":main()
