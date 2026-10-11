import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-v438")
TH={"min_boot_mean_positive_probability":0.90,"min_boot_pf_ge1_probability":0.80,"positive_half_segments":4,"max_trade_profit_share":0.35,"max_day_profit_share":0.50}
def main():
 d=json.loads((S/"deep_evidence_v1.json").read_text()); x=d["deep"]["deep"]; failed=[]
 for k,v in TH.items():
  actual=x[k]; ok=(actual>=v) if k.startswith("min_") or k=="positive_half_segments" else (actual<=v)
  if not ok: failed.append({"metric":k,"actual":actual,"required":v})
 out={"schema_version":1,"kind":"JARVIS_FAILURE_DIAGNOSIS_V1","status":"DIAGNOSED","space":d["space"],
 "strategy_id":d["strategy_id"],"failed_gates":failed,"passed_gate_count":len(TH)-len(failed),
 "conclusion":"ROBUSTNESS_INSUFFICIENT" if failed else "NO_DEEP_FAILURE","next_action":"REFINE_HYPOTHESIS_FROM_FAILED_GATES",
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"failure_diagnosis_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"failure_diagnosis_v1.json")
 print("ALL PASS|FAILURE_DIAGNOSIS|FAILED_GATES="+str(len(failed))+"|NEXT="+out["next_action"])
if __name__=="__main__": main()
