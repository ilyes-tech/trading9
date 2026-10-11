import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 p=S/"failure_diagnosis_v2.json"
 if not p.exists():print("ALL PASS|HYPOTHESIS_REFINER_V2|NO_DIAGNOSIS");return
 d=json.loads(p.read_text());failed=d.get("failed_gates",[])
 names=[x["metric"] for x in failed]
 objective={"space":d["space"],"parent_strategy_id":d["strategy_id"],"problem":d["conclusion"],
 "improve":names,"preserve":[x["metric"] for x in d.get("passed_gates",[])],
 "constraint":"Use development evidence only; change one causal dimension at a time; reject repeats; require exact replay then DEEP validation.",
 "search_requested":False}
 base=hashlib.sha256(json.dumps(objective,sort_keys=True).encode()).hexdigest(); seen=[]; lp=S/"research_learning_v1.jsonl"
 if lp.exists():
  for line in lp.read_text().splitlines():
   try:
    x=json.loads(line)
    if x.get("next_action")=="DO_NOT_REPEAT_IDENTICAL_PROBE" and x.get("hypothesis_id"): seen.append(x["hypothesis_id"])
   except: pass
 generation=0; hid=base
 while hid in set(seen) and generation<4:
  generation+=1; objective["refinement_generation"]=generation; objective["prior_failed_hypothesis_id"]=hid; objective["causal_focus"]=names[(generation-1)%len(names)] if names else "NO_FAILED_METRIC"; hid=hashlib.sha256(json.dumps(objective,sort_keys=True).encode()).hexdigest()
 exhausted=hid in set(seen)
 out={"schema_version":2,"kind":"JARVIS_REFINED_HYPOTHESIS_V2","status":"EXHAUSTED" if exhausted else "PROPOSED","hypothesis_id":hid,"objective":objective,
 "next_action":"ESCALATE_OR_STOP" if exhausted else "DESIGN_BOUNDED_EXPERIMENT","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"refined_hypothesis_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"refined_hypothesis_v1.json")
 print("ALL PASS|HYPOTHESIS_REFINER_V2|"+hid[:12]+"|NEXT=DESIGN_BOUNDED_EXPERIMENT|NO_SEARCH")
if __name__=="__main__":main()
