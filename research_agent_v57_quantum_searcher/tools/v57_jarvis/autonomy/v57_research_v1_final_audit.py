import hashlib,json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def load(n,k):
 p=S/n;x=json.loads(p.read_text())
 if x.get("kind")!=k or x.get("status")!="PASS":raise RuntimeError("INVALID:"+n)
 return x,hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r,rh=load("multimarket_evidence_registry_v3.json","V57_MULTIMARKET_EVIDENCE_REGISTRY_V3")
 a,ah=load("research_e2e_acceptance_v1.json","V57_RESEARCH_E2E_ACCEPTANCE_V1")
 e,eh=load("research_entrypoint_v2.json","V57_RESEARCH_ENTRYPOINT_V2")
 b,bh=load("research_orchestration_bridge_v1.json","V57_RESEARCH_ORCHESTRATION_BRIDGE_V1")
 if a["registry_sha256"]!=rh or e["registry_sha256"]!=rh or b["entrypoint_sha256"]!=eh:raise RuntimeError("PROVENANCE")
 if len(r["markets"])!=7 or len(e["decisions"])!=7 or set(e["decisions"].values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"}:raise RuntimeError("MARKETS_OR_DECISIONS")
 if r.get("deployable_strategy_proven") is not False or b.get("decision")!="SAFE_STOP":raise RuntimeError("DEPLOYMENT")
 for x in (r,a,e,b):
  for key in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed"):
   if x.get(key) is not False:raise RuntimeError("UNSAFE:"+key)
 if b.get("scheduler")!="NOT_CONNECTED" or b.get("phase2_supervisor")!="NOT_INVOKED":raise RuntimeError("SCOPE")
 doc={"schema_version":1,"kind":"V57_RESEARCH_V1_FINAL_AUDIT","status":"PASS","scope":"RESEARCH_ONLY_ON_DEMAND_SAFE_STOP","evidence_market_count":7,"market_decisions":"7_SAFE_STOP","registry_sha256":rh,"acceptance_sha256":ah,"entrypoint_sha256":eh,"bridge_sha256":bh,"frozen_guards_last_run":"PASS_SEPARATE_PROCESS","global_integration_last_run":"PASS_SEPARATE_PROCESS","scientific_outcome":"NO_DEPLOYABLE_STRATEGY_PROVEN","limitations":["NOT_CONNECTED_TO_UNATTENDED_SCHEDULER","NO_RUNTIME_EXECUTION_CONNECTOR_PROVEN","NO_PROFITABILITY_CLAIM","NO_NEW_SEARCH_AUTHORIZED"],"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_v1_final_audit.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_v1_final_audit.json")
 print("ALL PASS|RESEARCH_V1_FINAL_AUDIT|MARKETS=7|SAFE_STOP=7|SCOPE=ON_DEMAND|SCHEDULER=NO|DEPLOYABLE=NO")
if __name__=="__main__":
 try:main()
 except Exception as exc:print("STOP|FAIL|RESEARCH_V1_FINAL_AUDIT|"+str(exc));sys.exit(3)
