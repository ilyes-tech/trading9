import hashlib,json,sqlite3
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");DB=S/"causal_operator_v2.sqlite3"
ALLOWED={"ENTRY_STABILITY","CONCENTRATION_CONTROL","CONDITION_FAMILY","TIME_FILTER"}
def main():
 h=json.loads((S/"refined_hypothesis_v1.json").read_text());p=json.loads((S/"experiment_plan_v1.json").read_text())["plan"];dim=p.get("causal_dimension")
 if dim not in ALLOWED:status="DENIED";reason="UNKNOWN_CAUSAL_DIMENSION";design=None
 else:
  design={"hypothesis_id":h["hypothesis_id"],"agenda_id":p["agenda_id"],"agenda_objective":p["agenda_objective"],"space":p["space"],"parent_strategy_id":p["parent_strategy_id"],"allowed_dimensions":[dim],"selected_dimension":dim,"change_budget":1,"candidate_budget":min(8,int(p["max_candidates"])),"concurrency":1,"selection_rule":"CHANGE_EXACTLY_SELECTED_DIMENSION_AND_REQUIRE_TARGET_IMPROVEMENT_WITHOUT_BREAKING_PRESERVED_GATES","operator_mode":"DESIGN_ONLY"}
  status="READY";reason="AGENDA_BOUND_CAUSAL_DESIGN_VALID"
 c=sqlite3.connect(DB);c.execute("CREATE TABLE IF NOT EXISTS designs(design_id TEXT PRIMARY KEY,payload TEXT NOT NULL)");did=hashlib.sha256(json.dumps(design,sort_keys=True).encode()).hexdigest() if design else ""
 if design:c.execute("INSERT OR IGNORE INTO designs VALUES(?,?)",(did,json.dumps(design,sort_keys=True)));c.commit()
 c.close();out={"schema_version":2,"kind":"JARVIS_CAUSAL_OPERATOR_V2","status":status,"reason":reason,"design_id":did,"design":design,"searcher_invoked":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("causal_operator_v2.json","causal_operator_v1.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 print(("ALL PASS" if status=="READY" else "STOP|FAIL")+"|CAUSAL_OPERATOR_V2|"+status+"|DIMENSION="+str(dim)+"|SEARCHER=NOT_INVOKED")
if __name__=="__main__":main()
