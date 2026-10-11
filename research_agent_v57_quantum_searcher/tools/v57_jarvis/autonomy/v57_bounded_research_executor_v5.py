import json,os,sqlite3,sys,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");os.chdir(R);S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
for p in [R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry",R/"research_agent_v57_quantum_searcher/src/v438",R/"research_agent_v57_quantum_searcher/src/v437",R/"research_agent_v57_quantum_searcher/src/v436",R/"research_agent_v57_quantum_searcher/src/v435",R/"research_agent_v57_quantum_searcher/src/v434",R/"research_agent_v57_quantum_searcher/src/v433",R/"research_agent_v57_quantum_searcher/src"]:sys.path.insert(0,str(p))
DB=S/"bounded_research_v5_native.sqlite3"
def main():
 pre=json.loads((S/"bounded_research_preflight_v4.json").read_text());plan=json.loads((S/"experiment_plan_v1.json").read_text())["plan"];op=json.loads((S/"causal_operator_v1.json").read_text());hid=plan["hypothesis_id"]
 if pre.get("status")!="PREFLIGHT_PASS" or pre.get("execution_started") is not False:raise RuntimeError("PREFLIGHT_NOT_CLEAN")
 if plan.get("causal_dimension")!="VOLUME_CONFIRMATION" or pre.get("native_family")!="volume" or pre.get("parsed_families")!=["volume"]:raise RuntimeError("VOLUME_BINDING_FAILED")
 d=op.get("design") or {}
 if op.get("status")!="READY" or d.get("selected_dimension")!="VOLUME_CONFIRMATION" or d.get("allowed_dimensions")!=["VOLUME_CONFIRMATION"]:raise RuntimeError("OPERATOR_BINDING_FAILED")
 market,tf,side=plan["space"].split("_");hypothesis=f"{market} {tf} {side} volume researchonly probeid={hid}";seed=720000+(int(hid[:8],16)%100000);cap=min(4,int(plan.get("max_candidates",4)))
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS runs(hypothesis_id TEXT PRIMARY KEY,ts_ns INTEGER,status TEXT,result_path TEXT)")
 old=c.execute("SELECT status,result_path FROM runs WHERE hypothesis_id=?",(hid,)).fetchone()
 if old:print("ALL PASS|BOUNDED_RESEARCH_V5|IDEMPOTENT|"+old[0]);c.close();return
 mem=next(int(x.split()[1])//1024 for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:"));load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
 if mem<2048 or load>0.75:raise RuntimeError("RESOURCE_GATE")
 import v57_scientist_v3_4 as SCI
 res=SCI.experiment(hypothesis,start=0,count=cap,evaluate=True,seed=seed);families=res.get("hypothesis",{}).get("families",[])
 if families!=["volume"]:raise RuntimeError("NATIVE_FAMILY_BINDING_FAILED:"+repr(families))
 out={"schema_version":5,"kind":"JARVIS_BOUNDED_RESEARCH_RESULT_V5","status":"COMPLETED","hypothesis_id":hid,"agenda_id":plan["agenda_id"],"agenda_objective":plan["agenda_objective"],"causal_dimension":"VOLUME_CONFIRMATION","native_family":"volume","hypothesis":hypothesis,"seed":seed,"candidate_count":cap,"result":res,"purpose":"bounded development-only native-volume evidence probe; not causal proof","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"bounded_research_result_v5.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"bounded_research_result_v5.json");c.execute("INSERT INTO runs VALUES(?,?,?,?)",(hid,time.time_ns(),"COMPLETED",str(S/"bounded_research_result_v5.json")));c.commit();c.close()
 print("ALL PASS|BOUNDED_RESEARCH_V5|COMPLETED|CANDIDATES="+str(cap)+"|DIMENSION=VOLUME_CONFIRMATION|FAMILY=volume|SEARCHER_DAEMON=NOT_USED")
if __name__=="__main__":main()
