import hashlib,json,sqlite3
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"causal_operator_v1.sqlite3"
ALLOWED={"min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments","max_trade_profit_share","max_day_profit_share"}
def main():
 h=json.loads((S/"refined_hypothesis_v1.json").read_text());p=json.loads((S/"experiment_plan_v1.json").read_text())["plan"]
 metrics=set(p["target_metrics"]); bad=sorted(metrics-ALLOWED)
 if bad: status="DENIED";reason="UNKNOWN_METRIC";design=None
 else:
  dims=[]
  if metrics & {"min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments"}:
   dims=["ENTRY_STABILITY","CONDITION_FAMILY","TIME_FILTER"]
  if metrics & {"max_trade_profit_share","max_day_profit_share"}: dims+=["CONCENTRATION_CONTROL"]
  design={"hypothesis_id":h["hypothesis_id"],"space":p["space"],"parent_strategy_id":p["parent_strategy_id"],
   "allowed_dimensions":dims,"change_budget":1,"candidate_budget":min(8,int(p["max_candidates"])),"concurrency":1,
   "selection_rule":"CHANGE_ONE_DIMENSION_AND_REQUIRE_IMPROVEMENT_IN_TARGET_WITHOUT_BREAKING_PRESERVED_GATES",
   "operator_mode":"DESIGN_ONLY"}
  status="READY";reason="CAUSAL_DESIGN_VALID"
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS designs(design_id TEXT PRIMARY KEY,payload TEXT NOT NULL)")
 did=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest() if design else ""
 if design:c.execute("INSERT OR IGNORE INTO designs VALUES(?,?)",(did,json.dumps(design,sort_keys=True)));c.commit()
 c.close()
 out={"schema_version":1,"kind":"JARVIS_CAUSAL_OPERATOR_V1","status":status,"reason":reason,"design_id":did,"design":design,
 "searcher_invoked":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"causal_operator_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"causal_operator_v1.json")
 print(("ALL PASS" if status=="READY" else "STOP|FAIL")+"|CAUSAL_OPERATOR_V1|"+status+"|DESIGN_ONLY|SEARCHER=NOT_INVOKED")
if __name__=="__main__":main()
