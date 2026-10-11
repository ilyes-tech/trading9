#!/usr/bin/env python3
"""Fail-closed structural DSL-to-MT5 compatibility audit; no execution."""
import hashlib,json,sys
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 readiness=json.loads((S/"mt5_package_readiness_v1.json").read_text())
 if readiness.get("status")!="REVIEW_ELIGIBLE":
  print("ALL PASS|MT5_DSL_MAPPING|SAFE_IDLE|NO_EXPORT|NO_ORDERS");return
 sid=readiness.get("strategy_id")
 if not isinstance(sid,str) or len(sid)!=64 or any(c not in "0123456789abcdef" for c in sid):raise ValueError("INVALID_STRATEGY_ID")
 src=json.loads((S/"phase2_scientific_result_v1.json").read_text())
 matches=[x for x in (src.get("result") or {}).get("records",[]) if (x.get("strategy") or {}).get("strategy_id")==sid and (x.get("result") or {}).get("exact_pass") is True]
 if len(matches)!=1:raise ValueError("STRATEGY_NOT_UNIQUE")
 strategy=matches[0]["strategy"]
 if strategy.get("kind")!="V57_STRATEGY_DSL_V3" or strategy.get("execution",{}).get("orders_allowed") is not False:raise ValueError("DSL_OR_EXECUTION_INVALID")
 signal=strategy.get("signal")
 if not isinstance(signal,dict) or signal.get("op") is None:raise ValueError("SIGNAL_TREE_MISSING")
 proof=json.loads((R/"work/deployment_fidelity_v1/proofs"/(sid+".json")).read_text())
 body=dict(proof);digest=body.pop("proof_sha256",None)
 canon=lambda x:json.dumps(x,sort_keys=True,separators=(",",":"))
 if digest!=hashlib.sha256(canon(body).encode()).hexdigest():raise ValueError("FIDELITY_PROOF_HASH_INVALID")
 if proof.get("strategy_id")!=sid or proof.get("strategy_sha256")!=hashlib.sha256(canon(strategy).encode()).hexdigest():raise ValueError("FIDELITY_STRATEGY_BINDING_INVALID")
 if proof.get("promotion_allowed") is not True or (proof.get("verdict") or {}).get("conclusion")!="DEPLOYMENT_VERIFIED":raise ValueError("FIDELITY_NOT_VERIFIED")
 # The legacy MT5 format has no general DSL AST representation.
 # Never claim exact translation of arbitrary DSL trees to legacy MAJORITY/thresholds.
 print("ALL PASS|MT5_DSL_MAPPING|EXACT_TRANSLATION_UNSUPPORTED|TREE_OP="+str(signal["op"])+"|NO_EXPORT|NO_ORDERS")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|MT5_DSL_MAPPING|"+type(e).__name__+":"+str(e));sys.exit(3)
