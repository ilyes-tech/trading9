import hashlib,json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
from v57_autonomous_decision_policy_v1 import decide
def main():
 guard=A/"v57_global_autonomy_freeze_guard_v1.py"
 proc=subprocess.run([sys.executable,str(guard)],capture_output=True,text=True,timeout=60)
 if proc.returncode!=0 or not proc.stdout.startswith("ALL PASS|GLOBAL_AUTONOMY_FREEZE_GUARD|"):raise RuntimeError("GUARD_FAIL:"+proc.stdout.strip())
 p=S/"multimarket_evidence_registry_v3.json";r=json.loads(p.read_text())
 a=json.loads((S/"research_e2e_acceptance_v1.json").read_text())
 if r.get("kind")!="V57_MULTIMARKET_EVIDENCE_REGISTRY_V3" or r.get("status")!="PASS":raise RuntimeError("REGISTRY")
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if a.get("status")!="PASS" or a.get("registry_sha256")!=digest:raise RuntimeError("ACCEPTANCE")
 if set(r["markets"])!={"BTCUSD","ETHUSD","LTCUSD","EURUSD","GBPUSD","USDJPY","XAUUSD"}:raise RuntimeError("MARKETS")
 if any(r.get(k) is not False for k in ("auto_promotion_allowed","orders_allowed","mt5_allowed","holdout_allowed")):raise RuntimeError("SAFETY")
 decisions={m:decide(m,r) for m in sorted(r["markets"])}
 if set(decisions.values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"}:raise RuntimeError("DECISION")
 doc={"schema_version":2,"kind":"V57_RESEARCH_ENTRYPOINT_V2","status":"PASS","registry_sha256":digest,"guard":"PASS","acceptance":"PASS","decisions":decisions,"scope":"READ_ONLY_POLICY_ENTRYPOINT_NOT_CONNECTED_TO_UNATTENDED_SCHEDULER","execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_entrypoint_v2.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"research_entrypoint_v2.json")
 print("ALL PASS|RESEARCH_ENTRYPOINT_V2|REGISTRY=V3|GUARD=PASS|MARKETS=7|SAFE_STOP=7|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|RESEARCH_ENTRYPOINT_V2|"+str(e));sys.exit(3)
