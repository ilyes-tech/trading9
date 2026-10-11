import json,sys
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab")
REG=ROOT/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry"
STATE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
sys.path.insert(0,str(REG))
import v57_critic_v3_4 as C
FORBIDDEN=("holdout","hold-out","held-out","september 2026","mt5","broker","order_send","live order","demo order","shell command","subprocess")
def main():
 ref=json.loads((STATE/"reflection_v1.json").read_text())
 if ref.get("next_action")!="CRITIQUE_DEEP_REJECTION":
  print("ALL PASS|CRITIQUE_V2|SKIP"); return
 f=ref["focus"][0]
 prompt=("Scientific failure analysis for "+f["space"]+". Strategy "+f["strategy_id"]+
  " reached exact-pass but failed DEEP validation. Use ONLY already-authorized development folds. "
  "Do not propose reserved evaluation data, broker access, trading actions, file mutation, commands, or external tools. "
  "Identify one falsifiable weakness and a test using only existing development-fold evidence.")
 r=C.critique(prompt)
 body=" ".join(r["critique"].values()).lower()
 bad=[x for x in FORBIDDEN if x in body]
 status="REJECTED_UNSAFE_PROPOSAL" if bad else "SAFE_PROPOSAL"
 out={"schema_version":1,"kind":"JARVIS_CRITIQUE_EXECUTOR_V2","status":status,"source":f,
 "proposal":r.get("critique") if not bad else None,"blocked_terms":bad,"execution_allowed":False,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=STATE/"critique_v2.tmp"; t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 t.replace(STATE/"critique_v2.json")
 print("ALL PASS|CRITIQUE_V2|SAFE_PROPOSAL" if not bad else "STOP|FAIL|CRITIQUE_V2|UNSAFE_PROPOSAL_BLOCKED")
if __name__=="__main__": main()
