import hashlib,json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 a=json.loads((S/"research_agenda_v2.json").read_text());d=json.loads((S/"failure_diagnosis_v2.json").read_text());term=json.loads((S/"agenda_terminal_v1.json").read_text())
 if a.get("active") is not None or term.get("status")!="AGENDA_EXHAUSTED":raise RuntimeError("REPLAN_PRECONDITION_FAILED")
 failed={x["metric"] for x in d.get("failed_gates",[])};tested={x["objective"] for x in a.get("items",[])}
 objective="IMPROVE_TEMPORAL_CONSISTENCY";justified=bool(failed & {"min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments"}) and objective not in tested
 if justified:
  oid=hashlib.sha256((d["space"]+"|"+objective).encode()).hexdigest();decision="PROPOSE_ONE_NEW_OBJECTIVE";next_action="ADD_BOUNDED_TIME_FILTER_BRANCH"
 else:oid=None;decision="SAFE_STOP";next_action="NO_DISTINCT_EVIDENCE_BACKED_DIRECTION"
 out={"schema_version":1,"kind":"JARVIS_AGENDA_REPLANNER_V1","status":"REPLAN_READY","decision":decision,"proposal":{"id":oid,"space":d["space"],"objective":objective,"causal_dimension":"TIME_FILTER","justification_metrics":sorted(failed)} if oid else None,"tested_objectives":sorted(tested),"next_action":next_action,"max_new_objectives":1,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"agenda_replanner_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"agenda_replanner_v1.json")
 print("ALL PASS|AGENDA_REPLANNER_V1|DECISION="+decision+"|NEXT="+next_action)
if __name__=="__main__":main()
