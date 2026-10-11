import hashlib,json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 e=json.loads((S/"executive_v1.json").read_text())
 gaps=[]
 if e.get("reason")=="NO_ALLOWLISTED_CAUSAL_OPERATOR": gaps.append("CAUSAL_EXPERIMENT_OPERATOR")
 proposal={"goal":"Implement a bounded research operator for a previously diagnosed failure.",
 "constraints":["NON_FROZEN_ONLY","ONE_DIMENSION_AT_A_TIME","MAX_8_CANDIDATES","CONCURRENCY_1","RESOURCE_GATE","DUPLICATE_GUARD","DEVELOPMENT_ONLY","VERIFY_RESULT"],
 "market_execution":False,"searcher_is_optional":True}
 pid=hashlib.sha256(json.dumps(proposal,sort_keys=True).encode()).hexdigest()
 out={"schema_version":1,"kind":"JARVIS_CAPABILITY_GAP_PLAN_V1","status":"GAP_FOUND" if gaps else "NO_GAP","gaps":gaps,
 "proposal_id":pid,"proposal":proposal if gaps else None,"next_action":"DESIGN_OPERATOR" if gaps else "OBSERVE",
 "build_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"capability_gap_plan_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"capability_gap_plan_v1.json")
 print("ALL PASS|CAPABILITY_GAP_PLANNER|GAPS="+str(len(gaps))+"|NEXT="+out["next_action"])
if __name__=="__main__":main()
