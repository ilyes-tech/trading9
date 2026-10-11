#!/usr/bin/env python3
"""Build a review-only evidence manifest for a proven candidate. No MT5 code."""
import hashlib,json,sys,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher")
def load(p):
 if not p.is_file() or p.is_symlink():raise ValueError("MISSING_OR_SYMLINK:"+p.name)
 return json.loads(p.read_text())
def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def main():
 readiness=load(S/"mt5_package_readiness_v1.json")
 if readiness.get("status")!="REVIEW_ELIGIBLE":
  stale=S/"review_evidence_manifest_v1.json"
  if stale.is_symlink():raise ValueError("MANIFEST_SYMLINK_REFUSED")
  if stale.exists():stale.unlink()
  print("ALL PASS|PACKAGE_MANIFEST|SAFE_IDLE|ORDERS=NO");return
 sid=readiness.get("strategy_id")
 if not isinstance(sid,str) or len(sid)!=64 or any(c not in "0123456789abcdef" for c in sid):raise ValueError("INVALID_STRATEGY_ID")
 deep=load(S/"phase2_deep_validation_v1.json")
 sci=load(S/"phase2_scientific_result_v1.json")
 if deep.get("strategy_id")!=sid or deep.get("status")!="COMPLETED" or (deep.get("deep") or {}).get("status")!="DEEP_PASS" or deep.get("independent_replay_exact_pass") is not True:raise ValueError("DEEP_BINDING_FAILED")
 if sci.get("execution_token")!=deep.get("execution_token"):raise ValueError("TOKEN_MISMATCH")
 matches=[r for r in (sci.get("result") or {}).get("records",[]) if (r.get("strategy") or {}).get("strategy_id")==sid and (r.get("result") or {}).get("exact_pass") is True]
 if len(matches)!=1:raise ValueError("CANDIDATE_NOT_UNIQUE")
 strategy=matches[0]["strategy"]
 proof=load(R/"work/deployment_fidelity_v1/proofs"/(sid+".json"))
 body=dict(proof);digest=body.pop("proof_sha256",None)
 if digest!=hashlib.sha256(canon(body).encode()).hexdigest() or proof.get("strategy_sha256")!=hashlib.sha256(canon(strategy).encode()).hexdigest():raise ValueError("FIDELITY_HASH_FAILED")
 v=proof.get("verdict") or {};integrity=v.get("research_integrity") or {}
 if proof.get("strategy_id")!=sid or proof.get("promotion_allowed") is not True or v.get("conclusion")!="DEPLOYMENT_VERIFIED" or any(integrity.get(k) is not False for k in ("holdout_read","orders_allowed","september_2026_data_accessed")):raise ValueError("FIDELITY_VERDICT_FAILED")
 package={"kind":"JARVIS_REVIEW_EVIDENCE_MANIFEST_V1","strategy_id":sid,"execution_token":deep["execution_token"],"strategy_sha256":proof["strategy_sha256"],"fidelity_proof_sha256":digest,"deep_evidence_sha256":hashlib.sha256(canon(deep).encode()).hexdigest(),"scientific_result_sha256":hashlib.sha256(canon(sci).encode()).hexdigest(),"created_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"status":"REVIEW_ONLY","mt5_executable_included":False,"human_approval_required":True,"orders_allowed":False,"mt5_allowed":False,"auto_promotion_allowed":False}
 package["manifest_sha256"]=hashlib.sha256(canon(package).encode()).hexdigest()
 dest=S/"review_evidence_manifest_v1.json";temp=S/"review_evidence_manifest_v1.tmp";temp.write_text(json.dumps(package,indent=2,sort_keys=True)+"\n");temp.replace(dest)
 print("ALL PASS|PACKAGE_MANIFEST|REVIEW_ONLY|"+sid[:12]+"|ORDERS=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:
  print("STOP|FAIL|PACKAGE_MANIFEST|"+type(e).__name__+":"+str(e));sys.exit(3)
