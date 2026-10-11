import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 d=json.loads((S/"failure_diagnosis_v2.json").read_text());a=json.loads((S/"research_agenda_v2.json").read_text());active=a.get("active")
 if not active:raise RuntimeError("NO_ACTIVE_RESEARCH_OBJECTIVE")
 failed=[x["metric"] for x in d.get("failed_gates",[])];passed=[x["metric"] for x in d.get("passed_gates",[])]
 objective={"agenda_id":active["id"],"agenda_objective":active["objective"],"space":d["space"],"parent_strategy_id":d["strategy_id"],"problem":d["conclusion"],"improve":failed,"preserve":passed,"constraint":"Development evidence only; one bounded causal dimension; exact replay then DEEP validation.","search_requested":False}
 hid=hashlib.sha256(json.dumps(objective,sort_keys=True).encode()).hexdigest();seen=set();p=S/"research_learning_v1.jsonl"
 if p.exists():
  for line in p.read_text().splitlines():
   try:
    x=json.loads(line)
    if x.get("next_action")=="DO_NOT_REPEAT_IDENTICAL_PROBE":seen.add(x.get("hypothesis_id"))
   except:pass
 status="EXHAUSTED" if hid in seen else "PROPOSED"
 out={"schema_version":3,"kind":"JARVIS_REFINED_HYPOTHESIS_V3","status":status,"hypothesis_id":hid,"objective":objective,"next_action":"ESCALATE_OR_STOP" if status=="EXHAUSTED" else "DESIGN_BOUNDED_EXPERIMENT","execution_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("refined_hypothesis_v3.json","refined_hypothesis_v1.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 print("ALL PASS|HYPOTHESIS_REFINER_V3|AGENDA="+active["objective"]+"|"+hid[:12]+"|"+status)
if __name__=="__main__":main()
