import json,subprocess
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab");J=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis"
A=J/"autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
REQ={"safety":J/"kernel/v57_jarvis_safety_v1.py","planner":J/"registry/v57_general_planner_v1.py",
"builder":J/"registry/v57_builder_v1.py","verifier":J/"registry/v57_verifier_v1.py","job_launcher":J/"registry/v57_job_launcher_v1.py",
"memory":A/"v57_learning_memory_v2.py","reflection":A/"v57_reflection_engine_v2.py","core":A/"v57_autonomous_core_v2.py"}
def main():
 caps={k:p.is_file() for k,p in REQ.items()};timer=Path("/home/trading/.config/systemd/user/tradingai-jarvis-autonomous-core-v2.timer").is_file()
 gaps=[k for k,v in caps.items() if not v]
 out={"schema_version":1,"kind":"JARVIS_AUTONOMY_CAPABILITY_AUDIT_V1","status":"PASS" if not gaps and timer else "GAPS",
 "capabilities":caps,"persistent_timer":timer,"gaps":gaps+([] if timer else ["persistent_timer"]),
 "architecture":"OBSERVE->MEMORY->REFLECT->PLAN->AUTHORIZED_ACTION->VERIFY->JOURNAL",
 "searcher_role":"OPTIONAL_TOOL_NOT_CONTROLLER","self_modification":"GATED_BY_SAFETY_AND_VERIFICATION",
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 S.mkdir(parents=True,exist_ok=True);t=S/"capability_audit.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"capability_audit.json")
 print(("ALL PASS" if out["status"]=="PASS" else "STOP|FAIL")+"|AUTONOMY_CAPABILITY_AUDIT|GAPS="+str(len(out["gaps"])))
if __name__=="__main__":main()
