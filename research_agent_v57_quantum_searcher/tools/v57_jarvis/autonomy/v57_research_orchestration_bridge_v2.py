import hashlib,json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 proc=subprocess.run([sys.executable,str(A/"v57_research_entrypoint_v3.py")],capture_output=True,text=True,timeout=120)
 if proc.returncode!=0 or not proc.stdout.startswith("ALL PASS|RESEARCH_ENTRYPOINT_V3|"):raise RuntimeError("ENTRYPOINT_DENIED:"+proc.stdout.strip())
 p=S/"research_entrypoint_v3.json";x=json.loads(p.read_text())
 if x.get("kind")!="V57_RESEARCH_ENTRYPOINT_V3" or x.get("status")!="PASS" or x.get("guard")!="PASS" or x.get("acceptance")!="PASS":raise RuntimeError("GATES")
 if x.get("causal_admission")!="DENIED_NO_INDEPENDENT_NOVELTY" or x.get("independent_evidence")!="PASS_INTEGRITY_ONLY":raise RuntimeError("NOVELTY")
 if len(x.get("market_decisions",{}))!=7 or set(x["market_decisions"].values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"}:raise RuntimeError("DECISIONS")
 if any(x.get(k) is not False for k in ("research_execution_authorized","orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):raise RuntimeError("SAFETY")
 doc={"schema_version":2,"kind":"V57_RESEARCH_ORCHESTRATION_BRIDGE_V2","status":"PASS","entrypoint_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"decision":"SAFE_STOP_NO_CAUSAL_NOVELTY","core_invoked":False,"supervisor_invoked":False,"scheduler_connected":False,"research_execution_requested":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_orchestration_bridge_v2.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_orchestration_bridge_v2.json")
 print("ALL PASS|RESEARCH_BRIDGE_V2|ENTRYPOINT=V3|MARKETS=7|SAFE_STOP=YES|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|RESEARCH_BRIDGE_V2|"+str(e));sys.exit(3)
