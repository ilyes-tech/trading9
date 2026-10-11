import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 rows=[json.loads(x) for x in (S/"journal_v15.jsonl").read_text().splitlines() if x.strip()];z=rows[-3:]
 forbidden={"v57_bounded_research_executor_v3.py","v57_research_feedback_v1.py","v57_hypothesis_refiner_v3.py"}
 good=len(z)==3 and all(r.get("status")=="PASS" and r.get("mode")=="SAFE_STOP_NO_NOVEL_DIRECTION" and r.get("phase")=="EVIDENCE_BOUNDED_SAFE_STOP" and not any(r.get(k) for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")) and not (forbidden & {c.get("name") for c in r.get("checks",[])}) for r in z)
 out={"schema_version":7,"kind":"JARVIS_UNATTENDED_ACCEPTANCE_V7","status":"PASS" if good else "PENDING","verified_consecutive_cycles":3 if good else 0,"required_cycles":3,"scope":"FULL_RESEARCH_AUTONOMY_EVIDENCE_BOUNDED_SAFE_STOP","terminal_no_executor":good,"terminal_no_refiner":good,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"unattended_acceptance_v7.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"unattended_acceptance_v7.json")
 print(("ALL PASS" if good else "STOP|PENDING")+"|UNATTENDED_ACCEPTANCE_V7|CYCLES="+str(out["verified_consecutive_cycles"])+"|STATUS="+out["status"])
if __name__=="__main__":main()
