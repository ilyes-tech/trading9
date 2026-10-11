import json
from pathlib import Path
OLD=Path("/home/trading/.local/state/tradingai/jarvis-v438/deep_evidence_v1.json")
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
TH={"min_boot_mean_positive_probability":(0.90,"MIN"),"min_boot_pf_ge1_probability":(0.80,"MIN"),"positive_half_segments":(4,"MIN"),"max_trade_profit_share":(0.35,"MAX"),"max_day_profit_share":(0.50,"MAX")}
def main():
 if not OLD.exists():print("ALL PASS|FAILURE_DIAGNOSIS_V2|NO_DEEP_EVIDENCE");return
 d=json.loads(OLD.read_text());x=d["deep"]["deep"];failed=[];passed=[]
 for k,(v,mode) in TH.items():
  a=x[k];ok=a>=v if mode=="MIN" else a<=v;(passed if ok else failed).append({"metric":k,"actual":a,"required":v,"mode":mode})
 out={"schema_version":2,"kind":"JARVIS_FAILURE_DIAGNOSIS_V2","status":"DIAGNOSED","space":d["space"],"strategy_id":d["strategy_id"],
 "failed_gates":failed,"passed_gates":passed,"conclusion":"ROBUSTNESS_INSUFFICIENT" if failed else "DEEP_PASS",
 "next_action":"REFINE_RESEARCH_HYPOTHESIS" if failed else "VERIFY_NEXT_GATE","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 S.mkdir(parents=True,exist_ok=True);t=S/"failure_diagnosis_v2.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"failure_diagnosis_v2.json")
 print("ALL PASS|FAILURE_DIAGNOSIS_V2|FAILED="+str(len(failed))+"|PASSED="+str(len(passed))+"|NEXT="+out["next_action"])
if __name__=="__main__":main()
