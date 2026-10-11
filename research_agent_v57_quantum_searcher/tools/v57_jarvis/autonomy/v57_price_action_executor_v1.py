import json,os,sys,sqlite3,time,hashlib
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
for p in [R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry",*[R/("research_agent_v57_quantum_searcher/src/v"+str(i)) for i in range(438,432,-1)],R/"research_agent_v57_quantum_searcher/src"]:sys.path.insert(0,str(p))
def main():
 pre_path=S/"price_action_preflight_v1.json";pre=json.loads(pre_path.read_text());ad=json.loads((S/"capability_admission_v1.json").read_text())
 if pre.get("status")!="PASS" or pre.get("evaluation_started") is not False or pre.get("families")!=["price_action"] or pre.get("candidate_count")!=4:raise RuntimeError("PREFLIGHT_DENIED")
 if ad.get("status")!="ADMIT" or ad.get("capability")!="price_action" or ad.get("execution_authorized") is not False:raise RuntimeError("ADMISSION_DENIED")
 import v57_scientist_v4 as SCI
 h=pre["hypothesis"];hid=h["hypothesis_id"];raw=h["hypothesis"];db=sqlite3.connect(S/"price_action_executor_v1.sqlite3")
 db.execute("CREATE TABLE IF NOT EXISTS runs(hid TEXT PRIMARY KEY,status TEXT,ts INTEGER)")
 try:db.execute("INSERT INTO runs VALUES(?,?,?)",(hid,"STARTED",time.time_ns()));db.commit()
 except sqlite3.IntegrityError:
  print("ALL PASS|PRICE_ACTION_EXECUTOR_V1|IDEMPOTENT_NO_REPEAT");return
 try:
  mem=next(int(x.split()[1])//1024 for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:"))
  if mem<2048 or os.getloadavg()[0]/max(1,os.cpu_count() or 1)>.75:raise RuntimeError("RESOURCE_GATE")
  seed=730000+int(hid[:8],16)%100000;res=SCI.experiment(raw,count=4,evaluate=True,seed=seed)
  if res["hypothesis"]["families"]!=["price_action"] or res["generated_count"]!=4 or not res["evaluated"]:raise RuntimeError("SCIENTIST_BINDING")
  records=res.get("records",[])
  if len(records)!=4 or any({c["family"] for c in x["meta"]["conditions"]}!={"price_action"} for x in records):raise RuntimeError("RECORD_BINDING")
  out={"kind":"PRICE_ACTION_EXECUTOR_V1","status":"COMPLETED","preflight_sha256":hashlib.sha256(pre_path.read_bytes()).hexdigest(),"hypothesis_id":hid,"seed":seed,"result":res,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
  q=S/"price_action_result_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"price_action_result_v1.json")
  db.execute("UPDATE runs SET status='COMPLETED' WHERE hid=?",(hid,));db.commit()
  print("ALL PASS|PRICE_ACTION_EXECUTOR_V1|COMPLETED|CANDIDATES=4|ORDERS=FALSE")
 except Exception:
  db.execute("UPDATE runs SET status='FAILED' WHERE hid=?",(hid,));db.commit();raise
 finally:db.close()
if __name__=="__main__":main()
