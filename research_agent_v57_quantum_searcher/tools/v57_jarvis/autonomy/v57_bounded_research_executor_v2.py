import hashlib,json,os,sqlite3,sys,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");os.chdir(R);S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
for p in [R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry",R/"research_agent_v57_quantum_searcher/src/v438",R/"research_agent_v57_quantum_searcher/src/v437",R/"research_agent_v57_quantum_searcher/src/v436",R/"research_agent_v57_quantum_searcher/src/v435",R/"research_agent_v57_quantum_searcher/src/v434",R/"research_agent_v57_quantum_searcher/src/v433",R/"research_agent_v57_quantum_searcher/src"]:
 sys.path.insert(0,str(p))
DB=S/"bounded_research_v1.sqlite3"
def main():
 plan_doc=json.loads((S/"experiment_plan_v1.json").read_text());plan=plan_doc["plan"];hid=plan["hypothesis_id"];space=plan["space"];market,tf,side=space.split("_");hypothesis=f"{market} {tf} {side} development-only ONE_DIMENSION_AT_A_TIME hypothesis={hid} parent={plan.get('parent_strategy_id')} targets={','.join(plan.get('target_metrics',[]))}";seed=700000+(int(hid[:8],16)%100000);cap=min(4,int(plan.get("max_candidates",4)))
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS runs(hypothesis_id TEXT PRIMARY KEY,ts_ns INTEGER,status TEXT,result_path TEXT)")
 old=c.execute("SELECT status,result_path FROM runs WHERE hypothesis_id=?",(hid,)).fetchone()
 if old:print("ALL PASS|BOUNDED_RESEARCH_V1|IDEMPOTENT|"+old[0]);c.close();return
 mem=next(int(x.split()[1])//1024 for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:"));load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
 if mem<2048 or load>0.75:print("STOP|FAIL|BOUNDED_RESEARCH_V1|RESOURCE_GATE");c.close();return
 import v57_scientist_v3_4 as SCI
 res=SCI.experiment(hypothesis,start=0,count=cap,evaluate=True,seed=seed)
 out={"schema_version":1,"kind":"JARVIS_BOUNDED_RESEARCH_RESULT_V1","status":"COMPLETED","hypothesis_id":hid,"hypothesis":hypothesis,"seed":seed,"candidate_count":cap,"result":res,
 "purpose":"bounded development-only evidence probe; not causal proof","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 p=S/"bounded_research_result_v1.json";t=S/"bounded_research_result_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(p)
 c.execute("INSERT INTO runs VALUES(?,?,?,?)",(hid,time.time_ns(),"COMPLETED",str(p)));c.commit();c.close()
 print("ALL PASS|BOUNDED_RESEARCH_V1|COMPLETED|CANDIDATES="+str(cap)+"|SEARCHER_DAEMON=NOT_USED")
if __name__=="__main__":main()
