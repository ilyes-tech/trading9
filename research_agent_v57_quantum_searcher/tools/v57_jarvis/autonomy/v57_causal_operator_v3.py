import hashlib,json,sqlite3
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"causal_operator_v3.sqlite3"
ALLOWED={"ENTRY_STABILITY","CONCENTRATION_CONTROL","CONDITION_FAMILY","TIME_FILTER","VOLUME_CONFIRMATION"}
def main():
 p=json.loads((S/"experiment_plan_v1.json").read_text())["plan"];dim=p.get("causal_dimension")
 if dim not in ALLOWED: raise RuntimeError("UNKNOWN_CAUSAL_DIMENSION")
 design={"hypothesis_id":p["hypothesis_id"],"agenda_id":p["agenda_id"],"agenda_objective":p["agenda_objective"],"space":p["space"],"parent_strategy_id":p["parent_strategy_id"],"allowed_dimensions":[dim],"selected_dimension":dim,"change_budget":1,"candidate_budget":min(8,int(p["max_candidates"])),"concurrency":1,"selection_rule":"CHANGE_EXACTLY_SELECTED_DIMENSION_AND_REQUIRE_TARGET_IMPROVEMENT_WITHOUT_BREAKING_PRESERVED_GATES","operator_mode":"DESIGN_ONLY"}
 did=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest();c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS designs(design_id TEXT PRIMARY KEY,payload TEXT NOT NULL)");c.execute("INSERT OR IGNORE INTO designs VALUES(?,?)",(did,json.dumps(design,sort_keys=True)));c.commit();c.close()
 out={"schema_version":3,"kind":"JARVIS_CAUSAL_OPERATOR_V3","status":"READY","reason":"AGENDA_BOUND_CAUSAL_DESIGN_VALID","design_id":did,"design":design,"searcher_invoked":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False};payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("causal_operator_v3.json","causal_operator_v1.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 print("ALL PASS|CAUSAL_OPERATOR_V3|READY|DIMENSION="+dim+"|SEARCHER=NOT_INVOKED")
if __name__=="__main__": main()
