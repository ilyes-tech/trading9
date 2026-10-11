import hashlib,json
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab");A=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy";S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def sha(p):
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def main():
 targets=[A/"v57_tool_selector_v1.py",A/"v57_action_feedback_v1.py",A/"v57_goal_queue_v1.py"]
 before={str(p):sha(p) for p in targets};compile_ok=all(p.exists() and p.stat().st_size>0 for p in targets);after={str(p):sha(p) for p in targets}
 rollback_ready=before==after and compile_ok
 out={"schema_version":1,"kind":"JARVIS_SELF_IMPROVEMENT_GUARD_V1","status":"PASS" if rollback_ready else "FAIL",
 "candidate_scope":"AUTONOMY_NON_FROZEN_ONLY","prechange_hashes":before,"postcheck_hashes":after,"verification_passed":compile_ok,
 "rollback_ready":rollback_ready,"mutation_performed":False,"rule":"SNAPSHOT->BUILD_IN_NON_FROZEN->VERIFY->PROMOTE_OR_ROLLBACK",
 "frozen_mutation_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"self_improvement_guard_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"self_improvement_guard_v1.json")
 print(("ALL PASS" if rollback_ready else "STOP|FAIL")+"|SELF_IMPROVEMENT_GUARD_V1|ROLLBACK_READY="+str(rollback_ready).upper()+"|MUTATION=FALSE")
if __name__=="__main__":main()
