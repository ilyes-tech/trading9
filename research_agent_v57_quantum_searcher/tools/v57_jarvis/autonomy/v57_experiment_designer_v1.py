import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 h=json.loads((S/"refined_hypothesis_v1.json").read_text());o=h["objective"]
 plan={"hypothesis_id":h["hypothesis_id"],"space":o["space"],"parent_strategy_id":o["parent_strategy_id"],
 "method":"ONE_DIMENSION_AT_A_TIME","target_metrics":o["improve"],"preserve_metrics":o["preserve"],
 "max_candidates":8,"max_concurrent_jobs":1,"requires_resource_gate":True,"requires_exact_replay":True,"requires_deep_validation":True,
 "forbid_identical_repeats":True,"execution_mode":"PLAN_ONLY"}
 out={"schema_version":1,"kind":"JARVIS_BOUNDED_EXPERIMENT_PLAN_V1","status":"PLANNED","plan":plan,
 "next_action":"AWAIT_ALLOWLISTED_EXPERIMENT_OPERATOR","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"experiment_plan_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"experiment_plan_v1.json")
 print("ALL PASS|EXPERIMENT_DESIGNER|MAX_CANDIDATES=8|CONCURRENCY=1|PLAN_ONLY")
if __name__=="__main__":main()
