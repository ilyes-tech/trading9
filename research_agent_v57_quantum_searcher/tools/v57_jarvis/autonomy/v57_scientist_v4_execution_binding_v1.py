#!/usr/bin/env python3
"""Single-use, research-only binding from authorized objective to Scientist V4."""
import hashlib,json,sys,time
from pathlib import Path
A=Path(__file__).resolve().parent
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
REG=A.parent/"v3/registry"
def read(name):
 p=S/name
 if not p.is_file() or p.is_symlink():raise RuntimeError("MISSING_OR_SYMLINK:"+name)
 return json.loads(p.read_text())
def main():
 auth=read("search_authorization_v1.json")
 gate=read("search_execution_gate_v1.json")
 obj=read("bounded_objective_v1.json")
 if auth.get("authorized") is not True or auth.get("status")!="AUTHORIZED":raise RuntimeError("NOT_AUTHORIZED")
 if gate.get("ready") is not True or gate.get("status")!="READY":raise RuntimeError("EXECUTION_GATE_DENIED")
 budget=gate.get("budget_candidates")
 if type(budget)!=int or not 1<=budget<=4 or budget!=auth.get("max_candidates"):raise RuntimeError("BUDGET")
 if obj.get("objective_id")!=gate.get("objective_id") or obj.get("status")!="OPEN_REVIEW_ONLY":raise RuntimeError("OBJECTIVE_MISMATCH")
 if obj.get("objective_type") not in ("HYPOTHESIS_REVIEW","FEEDBACK_REVIEW"):raise RuntimeError("OBJECTIVE_TYPE")
 if any(obj.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):raise RuntimeError("OBJECTIVE_UNSAFE")
 token=gate.get("execution_token")
 expected=hashlib.sha256((obj["objective_id"]+"|"+str(budget)).encode()).hexdigest()
 if token!=expected:raise RuntimeError("TOKEN_MISMATCH")
 ledger=read("search_execution_ledger_v1.json")
 if token in (ledger.get("consumed_tokens") or []):raise RuntimeError("TOKEN_USED")
 proposal=read("approved_scientist_hypothesis_v1.json")
 if proposal.get("objective_id")!=obj["objective_id"] or proposal.get("status")!="APPROVED_RESEARCH_ONLY":raise RuntimeError("HYPOTHESIS_NOT_APPROVED")
 if any(proposal.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):raise RuntimeError("HYPOTHESIS_UNSAFE")
 hypothesis=proposal.get("hypothesis")
 if not isinstance(hypothesis,str) or not 8<=len(hypothesis)<=500:raise RuntimeError("HYPOTHESIS_INVALID")
 sys.path.insert(0,str(REG))
 import v57_scientist_v4 as scientist
 spec=scientist.H.parse(hypothesis)
 if spec.get("market") not in scientist.SUPPORTED_MARKETS or spec.get("timeframe") not in scientist.SUPPORTED_TIMEFRAMES or spec.get("side") not in ("LONG","SHORT"):raise RuntimeError("HYPOTHESIS_UNSUPPORTED")
 if spec["hypothesis_id"]!=proposal.get("hypothesis_id"):raise RuntimeError("HYPOTHESIS_HASH")
 # Persist token before evaluation: crash means no duplicate execution.
 ledger["consumed_tokens"]=list(ledger.get("consumed_tokens") or [])+[token]
 tmp=S/"search_execution_ledger_v1.tmp";tmp.write_text(json.dumps(ledger,indent=2,sort_keys=True)+"\n");tmp.replace(S/"search_execution_ledger_v1.json")
 result=scientist.experiment(hypothesis,start=0,count=budget,evaluate=True)
 if result.get("evaluated") is not True or result.get("generated_count")!=budget:raise RuntimeError("SCIENTIST_RESULT_INVALID")
 output={"kind":"JARVIS_SCIENTIST_V4_EXECUTION_BINDING_V1","objective_id":obj["objective_id"],"execution_token":token,"finished_at_ns":time.time_ns(),"research_only":True,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False,"result":result}
 target=S/("scientist_v4_run_"+token[:16]+".json");tmp=S/("scientist_v4_run_"+token[:16]+".tmp");tmp.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n");tmp.replace(target)
 print("ALL PASS|SCIENTIST_V4_BINDING|EVALUATED="+str(budget)+"|ORDERS=NO|FILE="+target.name)
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|SCIENTIST_V4_BINDING|"+type(e).__name__+":"+str(e));sys.exit(3)
