import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 x=json.loads((S/"bounded_research_result_v5.json").read_text());rs=x["result"]["records"]
 if len(rs)!=4 or x.get("native_family")!="volume" or x.get("causal_dimension")!="VOLUME_CONFIRMATION":raise RuntimeError("BAD_VOLUME_PROBE")
 if any({c["family"] for c in r.get("meta",{}).get("conditions",[])}!={"volume"} for r in rs):raise RuntimeError("FAMILY_CONTAMINATION")
 ev=[r for r in rs if r.get("status")=="EVALUATED" and isinstance(r.get("result"),dict)];rej=[r for r in rs if r.get("status")=="PREFILTER_REJECT"];exact=[r for r in ev if r["result"].get("exact_pass") is True]
 if len(ev)+len(rej)!=4:verdict="INVALID";reason="UNACCOUNTED_RECORD_STATUS"
 elif exact:verdict="IMPROVED";reason="AT_LEAST_ONE_EXACT_PASS"
 else:verdict="NO_EVIDENCE";reason="ZERO_EXACT_PASS_IN_BOUNDED_VOLUME_PROBE"
 out={"schema_version":1,"kind":"JARVIS_VOLUME_FEEDBACK_V1","status":"PASS" if verdict!="INVALID" else "FAIL","verdict":verdict,"reason":reason,"hypothesis_id":x["hypothesis_id"],"agenda_id":x["agenda_id"],"candidate_count":4,"evaluated_count":len(ev),"prefilter_reject_count":len(rej),"exact_pass_count":len(exact),"record_family_binding":"volume","do_not_repeat":verdict=="NO_EVIDENCE","next_action":"EXHAUST_VOLUME_BRANCH" if verdict=="NO_EVIDENCE" else ("VALIDATE_EXACT_PASS" if verdict=="IMPROVED" else "STOP"),"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"volume_feedback_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"volume_feedback_v1.json")
 print(("ALL PASS" if out["status"]=="PASS" else "STOP|FAIL")+"|VOLUME_FEEDBACK_V1|VERDICT="+verdict+"|EVALUATED="+str(len(ev))+"|PREFILTER_REJECT="+str(len(rej))+"|EXACT_PASS="+str(len(exact)))
if __name__=="__main__":main()
