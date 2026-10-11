import hashlib,json,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 e=json.loads((S/"executive_v2.json").read_text());op=json.loads((S/"causal_operator_v1.json").read_text());m=json.loads((S/"metacognition_v1.json").read_text())
 evidence={"executive_decision":e["decision"],"operator_status":op["status"],"metacognition":m["status"],"design_id":op.get("design_id")}
 verified=e["status"]=="PASS" and op["status"]=="READY" and m["status"]=="PASS"
 fid=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
 out={"schema_version":1,"kind":"JARVIS_ACTION_FEEDBACK_V1","status":"VERIFIED" if verified else "REJECTED","feedback_id":fid,"evidence":evidence,
 "lesson":"DESIGN_PIPELINE_COHERENT_NO_RESEARCH_EXECUTED" if verified else "PIPELINE_INCOHERENT","feed_memory":verified,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"action_feedback_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"action_feedback_v1.json")
 with (S/"feedback_journal_v1.jsonl").open("a") as f:f.write(json.dumps({"ts_ns":time.time_ns(),**out},sort_keys=True)+"\n")
 print(("ALL PASS" if verified else "STOP|FAIL")+"|ACTION_FEEDBACK_V1|"+out["status"]+"|"+fid[:12])
if __name__=="__main__":main()
