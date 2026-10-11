import hashlib,json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def run(script,marker):
 p=subprocess.run([sys.executable,str(A/script)],capture_output=True,text=True,timeout=90)
 if p.returncode!=0 or not p.stdout.startswith(marker):raise RuntimeError("GATE_FAILED:"+script+":"+p.stdout.strip())
def main():
 run("v57_research_entrypoint_v2.py","ALL PASS|RESEARCH_ENTRYPOINT_V2|")
 run("v57_independent_evidence_verifier_v2.py","ALL PASS|INDEPENDENT_EVIDENCE_VERIFIER_V2|")
 run("v57_causal_family_admission_v2.py","ALL PASS|CAUSAL_FAMILY_ADMISSION_V2|")
 old=json.loads((S/"research_entrypoint_v2.json").read_text())
 ev=json.loads((S/"independent_evidence_verifier_v2.json").read_text())
 ca=json.loads((S/"causal_family_admission_v2.json").read_text())
 reg=S/"multimarket_evidence_registry_v3.json"
 if old.get("registry_sha256")!=hashlib.sha256(reg.read_bytes()).hexdigest() or ev.get("source_sha256")!=old["registry_sha256"]:raise RuntimeError("PROVENANCE")
 if old.get("guard")!="PASS" or old.get("acceptance")!="PASS" or set(old.get("decisions",{}).values())!={"SAFE_STOP_NO_NEW_HYPOTHESIS"} or len(old["decisions"])!=7:raise RuntimeError("SAFE_STOP")
 if ca.get("new_family_admitted") is not False or ev.get("causal_novelty_proven") is not False:raise RuntimeError("NOVELTY")
 for obj in (old,ev,ca):
  if any(obj.get(k) is not False for k in ("orders_allowed","mt5_allowed","holdout_allowed","auto_promotion_allowed")):raise RuntimeError("SAFETY")
 doc={"schema_version":3,"kind":"V57_RESEARCH_ENTRYPOINT_V3","status":"PASS","registry_sha256":old["registry_sha256"],"guard":"PASS","acceptance":"PASS","independent_evidence":"PASS_INTEGRITY_ONLY","causal_admission":"DENIED_NO_INDEPENDENT_NOVELTY","market_decisions":old["decisions"],"scheduler":"NOT_CONNECTED","research_execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_entrypoint_v3.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"research_entrypoint_v3.json")
 print("ALL PASS|RESEARCH_ENTRYPOINT_V3|GATES=3|SAFE_STOP=7|NOVELTY=NO|EXECUTION=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|RESEARCH_ENTRYPOINT_V3|"+str(e));sys.exit(3)
