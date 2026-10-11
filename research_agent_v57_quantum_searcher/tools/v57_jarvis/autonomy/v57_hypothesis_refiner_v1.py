import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 p=S/"failure_diagnosis_v2.json"
 if not p.exists():print("ALL PASS|HYPOTHESIS_REFINER|NO_DIAGNOSIS");return
 d=json.loads(p.read_text());failed=d.get("failed_gates",[])
 names=[x["metric"] for x in failed]
 objective={"space":d["space"],"parent_strategy_id":d["strategy_id"],"problem":d["conclusion"],
 "improve":names,"preserve":[x["metric"] for x in d.get("passed_gates",[])],
 "constraint":"Use development evidence only; change one causal dimension at a time; reject repeats; require exact replay then DEEP validation.",
 "search_requested":False}
 hid=hashlib.sha256(json.dumps(objective,sort_keys=True).encode()).hexdigest()
 out={"schema_version":1,"kind":"JARVIS_REFINED_HYPOTHESIS_V1","status":"PROPOSED","hypothesis_id":hid,"objective":objective,
 "next_action":"DESIGN_BOUNDED_EXPERIMENT","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"refined_hypothesis_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"refined_hypothesis_v1.json")
 print("ALL PASS|HYPOTHESIS_REFINER|"+hid[:12]+"|NEXT=DESIGN_BOUNDED_EXPERIMENT|NO_SEARCH")
if __name__=="__main__":main()
