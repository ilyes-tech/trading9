import json,time
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 d=json.loads((S/"bounded_research_result_v1.json").read_text());records=d["result"]["records"]
 pre=sum(r.get("status")=="PREFILTER_REJECT" for r in records);ev=sum(r.get("status")=="EVALUATED" for r in records);exact=sum(bool((r.get("result") or {}).get("exact_pass")) for r in records)
 lesson="NO_EXACT_PASS_IN_BOUNDED_PROBE" if exact==0 else "EXACT_PASS_FOUND_REQUIRES_DEEP_VALIDATION"
 out={"schema_version":1,"kind":"JARVIS_RESEARCH_FEEDBACK_V1","status":"LEARNED","hypothesis_id":d["hypothesis_id"],"candidates":len(records),"prefilter_reject":pre,"evaluated":ev,"exact_pass":exact,"lesson":lesson,
 "next_action":"DO_NOT_REPEAT_IDENTICAL_PROBE","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 t=S/"research_feedback_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"research_feedback_v1.json")
 with (S/"research_learning_v1.jsonl").open("a") as f:f.write(json.dumps({"ts_ns":time.time_ns(),**out},sort_keys=True)+"\n")
 print("ALL PASS|RESEARCH_FEEDBACK_V1|LEARNED|EXACT_PASS="+str(exact)+"|NO_REPEAT=TRUE")
if __name__=="__main__":main()
