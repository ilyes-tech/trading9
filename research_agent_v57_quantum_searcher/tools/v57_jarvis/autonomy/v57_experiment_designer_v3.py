import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
MAP={"IMPROVE_STABILITY":"ENTRY_STABILITY","PRESERVE_CONCENTRATION_GATES":"CONCENTRATION_CONTROL","EXPLORE_DISTINCT_CAUSAL_DIMENSION":"CONDITION_FAMILY","IMPROVE_TEMPORAL_CONSISTENCY":"TIME_FILTER"}
def main():
 h=json.loads((S/"refined_hypothesis_v1.json").read_text());o=h["objective"];ao=o.get("agenda_objective");dim=MAP.get(ao)
 if not dim:raise RuntimeError("UNMAPPED_AGENDA_OBJECTIVE")
 plan={"hypothesis_id":h["hypothesis_id"],"agenda_id":o["agenda_id"],"agenda_objective":ao,"space":o["space"],"parent_strategy_id":o["parent_strategy_id"],"method":"ONE_DIMENSION_AT_A_TIME","causal_dimension":dim,"target_metrics":o["improve"],"preserve_metrics":o["preserve"],"max_candidates":8,"max_concurrent_jobs":1,"requires_resource_gate":True,"requires_exact_replay":True,"requires_deep_validation":True,"forbid_identical_repeats":True,"execution_mode":"PLAN_ONLY"}
 out={"schema_version":3,"kind":"JARVIS_BOUNDED_EXPERIMENT_PLAN_V3","status":"PLANNED","plan":plan,"next_action":"AWAIT_ALLOWLISTED_EXPERIMENT_OPERATOR","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False};payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("experiment_plan_v3.json","experiment_plan_v1.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 print("ALL PASS|EXPERIMENT_DESIGNER_V3|AGENDA="+ao+"|DIMENSION="+dim+"|PLAN_ONLY")
if __name__=="__main__":main()
