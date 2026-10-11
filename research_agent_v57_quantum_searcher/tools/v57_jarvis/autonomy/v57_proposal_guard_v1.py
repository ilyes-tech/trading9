import json,re
from pathlib import Path
STATE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
ALLOWED_METRICS=("min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments","max_trade_profit_share","max_day_profit_share","worst_stress_avg_bps","min_stress_pf")
def main():
 d=json.loads((STATE/"critique_v2.json").read_text())
 p=d.get("proposal") or {}
 text=" ".join(str(v) for v in p.values()).lower()
 reasons=[]
 if re.search(r"fold\s*[123]|training fold|not used during training",text): reasons.append("UNVERIFIED_FOLD_SEMANTICS")
 if "sharpe" in text or "cumulative return" in text: reasons.append("UNSUPPORTED_METRIC")
 if not any(m.replace("_"," ") in text for m in ALLOWED_METRICS): reasons.append("NOT_TIED_TO_DEEP_GATE_METRICS")
 status="REJECTED" if reasons else "ACCEPTED_FOR_PLANNING"
 out={"schema_version":1,"kind":"JARVIS_PROPOSAL_GUARD_V1","status":status,"reasons":reasons,"source_status":d.get("status"),"execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=STATE/"proposal_guard_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(STATE/"proposal_guard_v1.json")
 print(("STOP|FAIL|PROPOSAL_GUARD|"+",".join(reasons)) if reasons else "ALL PASS|PROPOSAL_GUARD|ACCEPTED_FOR_PLANNING")
if __name__=="__main__": main()
