import json,os,sqlite3,sys,time
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");os.chdir(R);S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
for p in [R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry",R/"research_agent_v57_quantum_searcher/src/v438",R/"research_agent_v57_quantum_searcher/src/v437",R/"research_agent_v57_quantum_searcher/src/v436",R/"research_agent_v57_quantum_searcher/src/v435",R/"research_agent_v57_quantum_searcher/src/v434",R/"research_agent_v57_quantum_searcher/src/v433",R/"research_agent_v57_quantum_searcher/src"]:sys.path.insert(0,str(p))
DB=S/"bounded_research_v4_native.sqlite3";FAMILY_MAP={"ENTRY_STABILITY":"momentum","CONCENTRATION_CONTROL":"volatility","CONDITION_FAMILY":"trend","TIME_FILTER":"time","VOLUME_CONFIRMATION":"volume"}
def main():
 plan=json.loads((S/"experiment_plan_v1.json").read_text())["plan"];op=json.loads((S/"causal_operator_v1.json").read_text());design=op.get("design") or {};hid=plan["hypothesis_id"];dim=plan.get("causal_dimension")
 if op.get("status")!="READY" or design.get("selected_dimension")!=dim or design.get("allowed_dimensions")!=[dim]:raise RuntimeError("CAUSAL_DIMENSION_NOT_BOUND")
 family=FAMILY_MAP.get(dim)
 if not family:raise RuntimeError("UNMAPPED_NATIVE_FAMILY")
 space=plan["space"];market,tf,side=space.split("_");hypothesis=f"{market} {tf} {side} {family} researchonly probeid={hid}";seed=710000+(int(hid[:8],16)%100000);cap=min(4,int(plan.get("max_candidates",4)))
 import v57_hypothesis_generator_v3 as H
 parsed=H.parse(hypothesis)
 if parsed.get("families")!=[family]:raise RuntimeError("STATIC_NATIVE_FAMILY_BINDING_FAILED:"+repr(parsed.get("families")))
 out={"schema_version":4,"kind":"JARVIS_BOUNDED_RESEARCH_PREFLIGHT_V4","status":"PREFLIGHT_PASS","hypothesis_id":hid,"causal_dimension":dim,"native_family":family,"parsed_families":parsed["families"],"candidate_cap":cap,"execution_started":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"bounded_research_preflight_v4.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"bounded_research_preflight_v4.json")
 print("ALL PASS|BOUNDED_RESEARCH_V4_PREFLIGHT|DIMENSION="+dim+"|FAMILY="+family+"|PARSED="+",".join(parsed["families"])+"|EXECUTION=NOT_STARTED")
if __name__=="__main__":main()
