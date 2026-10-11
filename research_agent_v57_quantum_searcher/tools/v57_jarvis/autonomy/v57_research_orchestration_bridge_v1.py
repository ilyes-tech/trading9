import json,hashlib,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 p=subprocess.run([sys.executable,str(A/"v57_research_entrypoint_v2.py")],capture_output=True,text=True,timeout=90)
 if p.returncode!=0 or "ALL PASS|RESEARCH_ENTRYPOINT_V2" not in p.stdout:raise RuntimeError("ENTRYPOINT_DENIED")
 x=json.loads((S/"research_entrypoint_v2.json").read_text())
 if x.get("status")!="PASS" or x.get("guard")!="PASS" or x.get("acceptance")!="PASS":raise RuntimeError("ENTRYPOINT_STATE")
 if len(x.get("decisions",{}))!=7 or set(x["decisions"].values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"}:raise RuntimeError("DECISIONS")
 if any(x.get(k) is not False for k in ("execution_authorized","orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):raise RuntimeError("SAFETY")
 doc={"schema_version":1,"kind":"V57_RESEARCH_ORCHESTRATION_BRIDGE_V1","status":"PASS","decision":"SAFE_STOP","entrypoint_sha256":hashlib.sha256((S/"research_entrypoint_v2.json").read_bytes()).hexdigest(),"autonomous_core_v15":"NOT_INVOKED","phase2_supervisor":"NOT_INVOKED","scheduler":"NOT_CONNECTED","research_execution_requested":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_orchestration_bridge_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_orchestration_bridge_v1.json")
 print("ALL PASS|RESEARCH_ORCHESTRATION_BRIDGE_V1|DECISION=SAFE_STOP|CORE=NOT_INVOKED|SUPERVISOR=NOT_INVOKED|SCHEDULER=NOT_CONNECTED")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|RESEARCH_ORCHESTRATION_BRIDGE_V1|"+str(e));sys.exit(3)
