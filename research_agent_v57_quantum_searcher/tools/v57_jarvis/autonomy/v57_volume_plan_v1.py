import hashlib,json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 r=json.loads((S/"capability_replan_v1.json").read_text());f=json.loads((S/"failure_diagnosis_v2.json").read_text());p=r["proposal"]
 if r.get("status")!="PROPOSED" or p.get("causal_dimension")!="VOLUME_CONFIRMATION" or p.get("native_family")!="volume":raise RuntimeError("BAD_VOLUME_REPLAN")
 hid=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
 plan={"hypothesis_id":hid,"agenda_id":p["id"],"agenda_objective":p["objective"],"space":p["space"],"parent_strategy_id":f["strategy_id"],"causal_dimension":"VOLUME_CONFIRMATION","target_metrics":p["target_metrics"],"preserve_metrics":p["preserve_metrics"],"max_candidates":4,"concurrency":1,"mode":"PLAN_ONLY"}
 out={"schema_version":1,"kind":"JARVIS_VOLUME_PLAN_V1","status":"PLANNED","plan":plan,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False};payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("volume_plan_v1.json","experiment_plan_v1.json"):
  q=S/(name+".tmp");q.write_text(payload);q.replace(S/name)
 print("ALL PASS|VOLUME_PLAN_V1|DIMENSION=VOLUME_CONFIRMATION|MAX=4|PLAN_ONLY")
if __name__=="__main__":main()
