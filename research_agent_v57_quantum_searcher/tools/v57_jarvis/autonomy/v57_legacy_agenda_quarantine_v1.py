import hashlib,json,sqlite3,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"research_agenda_v1.sqlite3"
def main():
 c=sqlite3.connect(str(DB),timeout=5)
 try:
  c.execute("BEGIN IMMEDIATE")
  rows=c.execute("SELECT id,space,objective,status FROM agenda ORDER BY id").fetchall()
  pending=[r for r in rows if r[3]=="PENDING"]
  if len(pending)!=15 or any(r[1]!="XAUUSD_M5_SHORT" for r in pending) or any(r[3]=="ACTIVE" for r in rows):raise RuntimeError("UNEXPECTED_AGENDA_STATE")
  digest=hashlib.sha256(json.dumps(pending,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
  c.executemany("UPDATE agenda SET status='QUARANTINED_UNVERIFIED' WHERE id=? AND status='PENDING'",[(r[0],) for r in pending])
  if c.execute("SELECT count(*) FROM agenda WHERE status='PENDING'").fetchone()[0]!=0 or c.execute("SELECT count(*) FROM agenda WHERE status='QUARANTINED_UNVERIFIED'").fetchone()[0]!=15:raise RuntimeError("QUARANTINE_FAILED")
  c.commit()
 finally:c.close()
 doc={"schema_version":1,"kind":"V57_LEGACY_AGENDA_QUARANTINE_V1","status":"PASS","quarantined":15,"original_pending_sha256":digest,"quarantine_reason":"UNVERIFIED_LEGACY_OBJECTIVES_NOT_ADMISSIBLE_FOR_AUTOMATIC_SELECTION","research_execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"legacy_agenda_quarantine_v1.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"legacy_agenda_quarantine_v1.json")
 print("ALL PASS|LEGACY_AGENDA_QUARANTINE_V1|QUARANTINED=15|PENDING=0|SEARCH=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|LEGACY_AGENDA_QUARANTINE_V1|"+str(e));sys.exit(3)
