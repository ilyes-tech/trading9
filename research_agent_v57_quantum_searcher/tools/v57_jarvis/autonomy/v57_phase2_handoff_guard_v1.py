#!/usr/bin/env python3
"""Fail-closed Phase 2 handoff observer. Does not launch validation or trades."""
import json, sys, time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def read(name):
 p=S/name
 if not p.is_file() or p.is_symlink():return None
 return json.loads(p.read_text())
def main():
 src=read("phase2_scientific_result_v1.json")
 gate=read("search_execution_gate_v1.json")
 ledger=read("search_execution_ledger_v1.json")
 reasons=[]
 if src is None:reasons.append("NO_PHASE2_RESULT")
 else:
  token=src.get("execution_token")
  if src.get("status")!="COMPLETED_RESEARCH_ONLY":reasons.append("RESULT_NOT_COMPLETED")
  if not isinstance(token,str) or len(token)!=64:reasons.append("TOKEN_INVALID")
  if gate is None or gate.get("execution_token")!=token or gate.get("ready") is not True:reasons.append("EXECUTION_GATE_NOT_MATCHED")
  if ledger is None or (ledger.get("consumed_tokens") or []).count(token)!=1:reasons.append("TOKEN_NOT_EXACTLY_ONCE_CONSUMED")
  scientific_ledger=read("phase2_scientific_execution_ledger_v1.json")
  if scientific_ledger is None or (scientific_ledger.get("completed_tokens") or []).count(token)!=1:reasons.append("SCIENTIFIC_EXECUTION_NOT_RECORDED")
  if src.get("independent_validation_required") is not True:reasons.append("INDEPENDENT_VALIDATION_NOT_REQUIRED")
  if src.get("pool_mutation_allowed") is not False:reasons.append("POOL_SAFETY_NOT_PROVEN")
  if any(src.get(k) is not False for k in ("holdout_allowed","mt5_allowed","orders_allowed","auto_promotion_allowed")):reasons.append("RESULT_SAFETY_NOT_PROVEN")
 status="ELIGIBLE_FOR_TRIAGE" if not reasons else "BLOCKED"
 out={"kind":"JARVIS_PHASE2_HANDOFF_GUARD_V1","status":status,"reasons":reasons,"execution_token":src.get("execution_token") if src else None,"checked_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"triage_executed":False,"deep_validation_executed":False,"orders_allowed":False,"mt5_allowed":False,"auto_promotion_allowed":False}
 q=S/"phase2_handoff_guard_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"phase2_handoff_guard_v1.json")
 print("ALL PASS|PHASE2_HANDOFF_GUARD|"+status+"|ORDERS=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("STOP|FAIL|PHASE2_HANDOFF_GUARD|"+type(e).__name__+":"+str(e));sys.exit(3)
