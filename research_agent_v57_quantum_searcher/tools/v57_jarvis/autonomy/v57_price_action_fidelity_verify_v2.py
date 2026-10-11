import json,hashlib,sys
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab/research_agent_v57_quantum_searcher");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def canon(x):return json.dumps(x,sort_keys=True,separators=(",",":"))
def main():
 source=json.loads((S/"price_action_result_v1.json").read_text());records=source["result"]["records"];out=[]
 for row in records:
  result=row.get("result"); 
  if not isinstance(result,dict) or result.get("exact_pass") is not True:continue
  strategy=row["strategy"];sid=strategy["strategy_id"];p=R/"work/deployment_fidelity_v1/proofs"/(sid+".json")
  if not p.is_file():raise RuntimeError("PROOF_MISSING:"+sid)
  proof=json.loads(p.read_text());digest=proof.get("proof_sha256");payload={k:v for k,v in proof.items() if k!="proof_sha256"}
  if hashlib.sha256(canon(payload).encode()).hexdigest()!=digest:raise RuntimeError("PROOF_HASH_MISMATCH:"+sid)
  if hashlib.sha256(canon(strategy).encode()).hexdigest()!=proof.get("strategy_sha256"):raise RuntimeError("STRATEGY_HASH_MISMATCH:"+sid)
  if proof.get("strategy_id")!=sid or proof.get("kind")!="V57_DEPLOYMENT_FIDELITY_PROOF_V1":raise RuntimeError("PROOF_IDENTITY_MISMATCH:"+sid)
  verdict=proof["verdict"];integ=verdict.get("research_integrity",{})
  safe=proof.get("holdout_read") is False and proof.get("orders_allowed") is False and proof.get("september_2026_data_accessed") is False and integ.get("holdout_read") is False and integ.get("orders_allowed") is False and integ.get("september_2026_data_accessed") is False
  if not safe:raise RuntimeError("RESEARCH_INTEGRITY_FAILED:"+sid)
  accepted=verdict.get("conclusion")=="DEPLOYMENT_VERIFIED" and verdict.get("promotion_allowed") is True and proof.get("promotion_allowed") is True
  out.append({"strategy_id":sid,"proof_hash_valid":True,"strategy_hash_valid":True,"integrity_valid":True,"fixed_exact_pass":verdict.get("fixed_exact_pass"),"fixed_min_stress_pf":verdict.get("fixed_min_stress_pf"),"verdict":verdict.get("conclusion"),"deployment_evidence_pass":accepted,"admission_granted":False})
 if len(out)!=2:raise RuntimeError("EXPECTED_TWO_INITIAL_PASS")
 doc={"schema_version":2,"kind":"PRICE_ACTION_FIDELITY_VERIFY_V2","status":"PASS","checked":len(out),"results":out,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"admission_granted":False}
 q=S/"price_action_fidelity_verify_v2.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"price_action_fidelity_verify_v2.json")
 print("ALL PASS|PRICE_ACTION_FIDELITY_VERIFY_V2|CHECKED="+str(len(out))+"|DEPLOYMENT_EVIDENCE_PASS="+str(sum(x["deployment_evidence_pass"] for x in out))+"|ADMISSION=DENIED")
if __name__=="__main__":main()
