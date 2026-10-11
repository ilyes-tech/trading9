import hashlib,json,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");J=S/"integrity_journal_v1.jsonl"
SOURCES=["status_v5.json","research_feedback_v1.json","goal_queue_v2.json","completion_audit_v5.json"]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prev="GENESIS";seq=1
 if J.exists() and J.stat().st_size:
  last=json.loads(J.read_text().splitlines()[-1]);prev=last["entry_hash"];seq=last["seq"]+1
 snap={n:digest(S/n) for n in SOURCES if (S/n).exists()}
 body={"seq":seq,"ts_ns":time.time_ns(),"prev_hash":prev,"artifacts":snap}
 eh=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest();rec={**body,"entry_hash":eh}
 with J.open("a") as f:f.write(json.dumps(rec,sort_keys=True)+"\n")
 rows=[json.loads(x) for x in J.read_text().splitlines() if x.strip()];valid=True;p="GENESIS"
 for i,r in enumerate(rows,1):
  b={k:r[k] for k in ("seq","ts_ns","prev_hash","artifacts")}
  h=hashlib.sha256(json.dumps(b,sort_keys=True,separators=(",",":")).encode()).hexdigest()
  if r["seq"]!=i or r["prev_hash"]!=p or r["entry_hash"]!=h:valid=False;break
  p=r["entry_hash"]
 out={"schema_version":1,"kind":"JARVIS_HASHCHAIN_JOURNAL_V1","status":"PASS" if valid else "FAIL","entries":len(rows),"head":p}
 t=S/"integrity_status_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"integrity_status_v1.json")
 print(("ALL PASS" if valid else "STOP|FAIL")+"|HASHCHAIN_JOURNAL|ENTRIES="+str(len(rows)))
if __name__=="__main__":main()
