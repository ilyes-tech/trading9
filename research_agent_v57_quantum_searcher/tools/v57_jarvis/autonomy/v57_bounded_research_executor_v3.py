import json,os,sqlite3,sys,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");os.chdir(R);S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
for p in [R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry",R/"research_agent_v57_quantum_searcher/src/v438",R/"research_agent_v57_quantum_searcher/src/v437",R/"research_agent_v57_quantum_searcher/src/v436",R/"research_agent_v57_quantum_searcher/src/v435",R/"research_agent_v57_quantum_searcher/src/v434",R/"research_agent_v57_quantum_searcher/src/v433",R/"research_agent_v57_quantum_searcher/src"]:sys.path.insert(0,str(p))
DB=S/"bounded_research_v3_native.sqlite3";FAMILY_MAP={"ENTRY_STABILITY":"momentum","CONCENTRATION_CONTROL":"volatility","CONDITION_FAMILY":"trend","TIME_FILTER":"time"}
def main():
 plan=json.loads((S/"experiment_plan_v1.json").read_text())["plan"];op=json.loads((S/"causal_operator_v1.json").read_text());design=op.get("design") or {};hid=plan["hypothesis_id"];dim=plan.get("causal_dimension")
 if op.get("status")!="READY" or not dim or design.get("selected_dimension")!=dim or design.get("allowed_dimensions")!=[dim]:raise RuntimeError("CAUSAL_DIMENSION_NOT_BOUND")
 family=FAMILY_MAP.get(dim)
 if not family:raise RuntimeError("UNMAPPED_NATIVE_FAMILY")
 space=plan["space"];market,tf,side=space.split("_");hypothesis=f"{market} {tf} {side} {family} researchonly probeid={hid}";seed=700000+(int(hid[:8],16)%100000);cap=min(4,int(plan.get("max_candidates",4)))
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS runs(hypothesis_id TEXT PRIMARY KEY,ts_ns INTEGER,status TEXT,result_path TEXT,causal_dimension TEXT,native_family TEXT)")
 old=c.execute("SELECT status,result_path,causal_dimension,native_family FROM runs WHERE hypothesis_id=?",(hid,)).fetchone()
 if old:print("ALL PASS|BOUNDED_RESEARCH_V3|IDEMPOTENT|"+old[0]+"|DIMENSION="+str(old[2])+"|FAMILY="+str(old[3]));c.close();return
 mem=next(int(x.split()[1])//1024 for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:"));load=os.getloadavg()[0]/max(1,os.cpu_count() or 1)
 if mem<2048 or load>0.75:print("STOP|FAIL|BOUNDED_RESEARCH_V3|RESOURCE_GATE");c.close();return
 import v57_scientist_v3_4 as SCI
 res=SCI.experiment(hypothesis,start=0,count=cap,evaluate=True,seed=seed)
 parsed=res.get("hypothesis",{});families=parsed.get("families",[])
 if families!=[family]:raise RuntimeError("NATIVE_FAMILY_BINDING_FAILED:"+repr(families))
 out={"schema_version":3,"kind":"JARVIS_BOUNDED_RESEARCH_RESULT_V3","status":"COMPLETED","hypothesis_id":hid,"agenda_id":plan.get("agenda_id"),"agenda_objective":plan.get("agenda_objective"),"causal_dimension":dim,"native_family":family,"hypothesis":hypothesis,"seed":seed,"candidate_count":cap,"result":res,"purpose":"bounded agenda-bound development-only evidence probe; not causal proof","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("bounded_research_result_v3.json","bounded_research_result_v1.json"):
  q=S/name;t=S/(name+".tmp");t.write_text(payload);t.replace(q)
 c.execute("INSERT INTO runs VALUES(?,?,?,?,?,?)",(hid,time.time_ns(),"COMPLETED",str(S/"bounded_research_result_v3.json"),dim,family));c.commit();c.close()
 print("ALL PASS|BOUNDED_RESEARCH_V3|COMPLETED|CANDIDATES="+str(cap)+"|DIMENSION="+dim+"|FAMILY="+family+"|SEARCHER_DAEMON=NOT_USED")
if __name__=="__main__":main()
