import hashlib,json,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 h=json.loads((S/"refined_hypothesis_v1.json").read_text());m=json.loads((S/"metacognition_v1.json").read_text());term=json.loads((S/"branch_terminal_v2.json").read_text()) if (S/"branch_terminal_v2.json").exists() else {}
 terminal=h.get("status")=="EXHAUSTED";e=json.loads((S/"executive_v2.json").read_text()) if (S/"executive_v2.json").exists() else {};op=json.loads((S/"causal_operator_v1.json").read_text()) if (S/"causal_operator_v1.json").exists() else {}
 terminal_verified=terminal and term.get("status")=="TERMINAL_VALID" and term.get("hypothesis_id")==h.get("hypothesis_id") and term.get("agenda_id")==h.get("objective",{}).get("agenda_id") and m.get("status")=="PASS"
 normal_verified=(not terminal) and e.get("status")=="PASS" and op.get("status")=="READY" and op.get("design",{}).get("hypothesis_id")==h.get("hypothesis_id") and m.get("status")=="PASS"
 verified=terminal_verified or normal_verified;mode="TERMINAL" if terminal else "NORMAL";evidence={"mode":mode,"hypothesis_id":h.get("hypothesis_id"),"agenda_id":h.get("objective",{}).get("agenda_id"),"terminal_hypothesis_id":term.get("hypothesis_id"),"terminal_agenda_id":term.get("agenda_id"),"operator_hypothesis_id":op.get("design",{}).get("hypothesis_id"),"metacognition":m.get("status")}
 fid=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest();out={"schema_version":3,"kind":"JARVIS_ACTION_FEEDBACK_V3","status":"VERIFIED" if verified else "REJECTED","feedback_id":fid,"evidence":evidence,"lesson":"CURRENT_BRANCH_EVIDENCE_BOUND" if verified else "STALE_OR_INCOHERENT_BRANCH_EVIDENCE","feed_memory":verified,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 payload=json.dumps(out,indent=2,sort_keys=True)+"\n"
 for name in ("action_feedback_v3.json","action_feedback_v1.json"):
  t=S/(name+".tmp");t.write_text(payload);t.replace(S/name)
 with (S/"feedback_journal_v3.jsonl").open("a") as f:f.write(json.dumps({"ts_ns":time.time_ns(),**out},sort_keys=True)+"\n")
 print(("ALL PASS" if verified else "STOP|FAIL")+"|ACTION_FEEDBACK_V3|"+mode+"|"+out["status"]+"|"+fid[:12])
if __name__=="__main__":main()
