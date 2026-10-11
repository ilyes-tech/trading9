import json
from pathlib import Path
STATE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
def main():
 ref=json.loads((STATE/"reflection_v1.json").read_text()); guard=json.loads((STATE/"proposal_guard_v1.json").read_text())
 focus=ref["focus"][0]
 if guard.get("status")=="REJECTED":
  plan={"action":"RECONSTRUCT_EXISTING_DEEP_EVIDENCE","space":focus["space"],"strategy_id":focus["strategy_id"],
   "purpose":"Measure the failed candidate only with the exact metrics already enforced by DEEP validation.",
   "required_metrics":["min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments","max_trade_profit_share","max_day_profit_share"],
   "compute_budget":"ONE_CANDIDATE_REPLAY","research_execution_allowed":True}
 else:
  plan={"action":"REVIEW_ACCEPTED_CRITIQUE","space":focus["space"],"strategy_id":focus["strategy_id"],"research_execution_allowed":False}
 out={"schema_version":1,"kind":"JARVIS_EVIDENCE_PLANNER_V1","status":"PLANNED","plan":plan,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=STATE/"evidence_plan_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(STATE/"evidence_plan_v1.json")
 print("ALL PASS|EVIDENCE_PLANNER|"+plan["action"]+"|BUDGET="+plan.get("compute_budget","NONE"))
if __name__=="__main__": main()
