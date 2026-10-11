import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def load(n,k):
 p=S/n;x=json.loads(p.read_text())
 if x.get("kind")!=k or x.get("status")!="PASS":raise RuntimeError("INVALID:"+n)
 return x,hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r,rh=load("multimarket_evidence_registry_v3.json","V57_MULTIMARKET_EVIDENCE_REGISTRY_V3")
 n,nh=load("hypothesis_novelty_gate_v1.json","V57_HYPOTHESIS_NOVELTY_GATE_V1")
 h,hh=load("hypothesis_history_dedup_v1.json","V57_HYPOTHESIS_HISTORY_DEDUP_V1")
 b,bh=load("research_orchestration_bridge_v1.json","V57_RESEARCH_ORCHESTRATION_BRIDGE_V1")
 if n["registry_sha256"]!=rh or h["history_items"]!=6 or h["tests"]!=4 or n["cases_checked"]!=5:raise RuntimeError("PROVENANCE")
 if any(x.get("execution_authorized") is not False for x in (n,h)):raise RuntimeError("EXECUTION")
 if b.get("decision")!="SAFE_STOP" or b.get("scheduler")!="NOT_CONNECTED":raise RuntimeError("BRIDGE")
 if any(x.get("orders_allowed") is not False or x.get("mt5_allowed") is not False or x.get("holdout_allowed") is not False for x in (r,n,h,b)):raise RuntimeError("SAFETY")
 doc={"schema_version":1,"kind":"V57_HYPOTHESIS_NOVELTY_INTEGRATION_V1","status":"PASS","registry_sha256":rh,"novelty_gate_sha256":nh,"history_dedup_sha256":hh,"bridge_sha256":bh,"checks":4,"decision":"SAFE_STOP_PENDING_VERIFIABLE_NOVEL_CAUSAL_EVIDENCE","historical_scope":"6_SIGNATURES_ONLY","semantic_novelty_verified":False,"research_execution_authorized":False,"scheduler_connected":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"hypothesis_novelty_integration_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"hypothesis_novelty_integration_v1.json")
 print("ALL PASS|HYPOTHESIS_NOVELTY_INTEGRATION_V1|CHECKS=4|HISTORY=6|SAFE_STOP=YES|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|HYPOTHESIS_NOVELTY_INTEGRATION_V1|"+str(e));sys.exit(3)
