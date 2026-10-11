#!/usr/bin/env python3
"""Read-only MT5 packaging readiness gate. No package generation or execution."""
import hashlib,json,sys,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
def load(p):
 if p.is_symlink() or not p.is_file():return None
 return json.loads(p.read_text())
def canon(v):return json.dumps(v,sort_keys=True,separators=(",",":"))
def main():
 d=load(S/"phase2_deep_validation_v1.json")
 result=load(S/"phase2_scientific_result_v1.json")
 reasons=[]
 sid=d.get("strategy_id") if d else None
 if not d or d.get("status")!="COMPLETED" or (d.get("deep") or {}).get("status")!="DEEP_PASS" or d.get("independent_replay_exact_pass") is not True:reasons.append("DEEP_PASS_MISSING")
 if not result or not d or result.get("execution_token")!=d.get("execution_token"):reasons.append("SCIENTIFIC_BINDING_MISSING")
 token=(result or {}).get("execution_token")
 gate=load(S/"search_execution_gate_v1.json")
 ledger=load(S/"search_execution_ledger_v1.json")
 scientific_ledger=load(S/"phase2_scientific_execution_ledger_v1.json")
 if not isinstance(token,str) or len(token)!=64 or not gate or gate.get("ready") is not True or gate.get("execution_token")!=token or not ledger or (ledger.get("consumed_tokens") or []).count(token)!=1 or not scientific_ledger or (scientific_ledger.get("completed_tokens") or []).count(token)!=1:reasons.append("SCIENTIFIC_EXECUTION_PROVENANCE_MISSING")
 triage=load(S/"phase2_result_triage_v1.json")
 promotion=load(S/"phase2_promotion_decision_v1.json")
 if not triage or triage.get("execution_token")!=(d or {}).get("execution_token") or triage.get("decision")!="VALIDATION_REQUIRED" or triage.get("deep_validation_allowed") is not True:reasons.append("TRIAGE_BINDING_MISSING")
 if not promotion or promotion.get("execution_token")!=(d or {}).get("execution_token") or promotion.get("strategy_id")!=sid or promotion.get("decision")!="REVIEW_ELIGIBLE" or promotion.get("promotion_executed") is not False:reasons.append("PROMOTION_REVIEW_MISSING")
 if not result or result.get("status")!="COMPLETED_RESEARCH_ONLY" or result.get("independent_validation_required") is not True or result.get("pool_mutation_allowed") is not False or any(result.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):reasons.append("SCIENTIFIC_SAFETY_MISSING")
 if d and any(d.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):reasons.append("DEEP_SAFETY_MISSING")
 if not isinstance(sid,str) or len(sid)!=64:reasons.append("STRATEGY_ID_MISSING")
 proof=None
 if not reasons:
  records=(result.get("result") or {}).get("records") or []
  matches=[x for x in records if (x.get("strategy") or {}).get("strategy_id")==sid and (x.get("result") or {}).get("exact_pass") is True]
  if len(matches)!=1:reasons.append("EXACT_STRATEGY_NOT_UNIQUE")
  else:
   strategy=matches[0]["strategy"]
   proof=load(R/"work/deployment_fidelity_v1/proofs"/(sid+".json"))
   if not proof:reasons.append("FIDELITY_PROOF_MISSING")
   else:
    h=proof.get("proof_sha256");body=dict(proof);body.pop("proof_sha256",None)
    if hashlib.sha256(canon(body).encode()).hexdigest()!=h:reasons.append("PROOF_HASH_INVALID")
    if proof.get("strategy_sha256")!=hashlib.sha256(canon(strategy).encode()).hexdigest() or proof.get("strategy_id")!=sid:reasons.append("STRATEGY_PROOF_MISMATCH")
    v=proof.get("verdict") or {};integrity=v.get("research_integrity") or {}
    if proof.get("promotion_allowed") is not True or v.get("conclusion")!="DEPLOYMENT_VERIFIED":reasons.append("FIDELITY_NOT_VERIFIED")
    if any(integrity.get(k) is not False for k in ("holdout_read","orders_allowed","september_2026_data_accessed")):reasons.append("FIDELITY_INTEGRITY_UNPROVEN")
 status="REVIEW_ELIGIBLE" if not reasons else "BLOCKED"
 out={"kind":"JARVIS_MT5_PACKAGE_READINESS_V1","status":status,"strategy_id":sid,"reasons":reasons,"checked_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"package_generated":False,"human_approval_required":True,"orders_allowed":False,"mt5_allowed":False,"auto_promotion_allowed":False}
 p=S/"mt5_package_readiness_v1.tmp";p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");p.replace(S/"mt5_package_readiness_v1.json")
 print("ALL PASS|MT5_PACKAGE_READINESS|"+status+"|PACKAGE=NO|ORDERS=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("STOP|FAIL|MT5_PACKAGE_READINESS|"+type(e).__name__+":"+str(e));sys.exit(3)
