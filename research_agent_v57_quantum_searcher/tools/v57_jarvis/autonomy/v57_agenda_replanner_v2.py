import hashlib,json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 a=json.loads((S/"research_agenda_v3.json").read_text());d=json.loads((S/"failure_diagnosis_v2.json").read_text());term=json.loads((S/"agenda_terminal_v2.json").read_text())
 if a.get("active") is not None or term.get("status")!="AGENDA_EXHAUSTED":raise RuntimeError("REPLAN_PRECONDITION_FAILED")
 tested={x["objective"] for x in a.get("items",[])};failed={x["metric"] for x in d.get("failed_gates",[])}
 objective="IMPROVE_TEMPORAL_CONSISTENCY";novel=objective not in tested;justified=bool(failed & {"min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments"}) and novel
 if justified:
  oid=hashlib.sha256((d["space"]+"|"+objective).encode()).hexdigest();proposal={"id":oid,"space":d["space"],"objective":objective,"causal_dimension":"TIME_FILTER","justification_metrics":sorted(failed)};decision="PROPOSE_ONE_NEW_OBJECTIVE";nxt="ADD_BOUNDED_TIME_FILTER_BRANCH"
 else:proposal=None;decision="SAFE_STOP";nxt="NO_DISTINCT_EVIDENCE_BACKED_DIRECTION"
 out={"schema_version":2,"kind":"JARVIS_AGENDA_REPLANNER_V2","status":"REPLAN_READY","decision":decision,"proposal":proposal,"tested_objectives":sorted(tested),"failed_metrics":sorted(failed),"novel_time_filter":novel,"next_action":nxt,"max_new_objectives":1,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"agenda_replanner_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"agenda_replanner_v2.json")
 print("ALL PASS|AGENDA_REPLANNER_V2|DECISION="+decision+"|NOVEL_TIME_FILTER="+str(novel).upper()+"|NEXT="+nxt)
if __name__=="__main__":main()
