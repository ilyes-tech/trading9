import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 a=json.loads((S/"research_agenda_v3.json").read_text());r=json.loads((S/"capability_replan_v1.json").read_text());f=json.loads((S/"volume_feedback_v1.json").read_text());p=r["proposal"]
 if a.get("active") is not None or any(x.get("status")!="EXHAUSTED" for x in a["items"]):raise RuntimeError("V3_NOT_TERMINAL")
 if r.get("status")!="PROPOSED" or p.get("native_family")!="volume" or p.get("causal_dimension")!="VOLUME_CONFIRMATION":raise RuntimeError("BAD_REPLAN")
 if f.get("status")!="PASS" or f.get("verdict")!="NO_EVIDENCE" or f.get("do_not_repeat") is not True or f.get("agenda_id")!=p["id"]:raise RuntimeError("FEEDBACK_BINDING_FAILED")
 items=[dict(x) for x in a["items"]];items.append({"id":p["id"],"objective":p["objective"],"space":p["space"],"native_family":"volume","causal_dimension":"VOLUME_CONFIRMATION","source":"NATIVE_CAPABILITY_DISCOVERY_V1","attempts":1,"status":"EXHAUSTED","terminal_hypothesis_id":f["hypothesis_id"],"terminal_reason":f["reason"]})
 out={"schema_version":4,"kind":"JARVIS_RESEARCH_AGENDA_V4","status":"READY","rule":"IMPORT_V3_TERMINAL; ADD_ONLY_EVIDENCE_BOUND_NATIVE_CAPABILITY; EXHAUSTED_NEVER_REACTIVATED","active":None,"items":items,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"research_agenda_v4.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"research_agenda_v4.json")
 print("ALL PASS|RESEARCH_AGENDA_V4|ITEMS="+str(len(items))+"|EXHAUSTED="+str(sum(x["status"]=="EXHAUSTED" for x in items))+"|ACTIVE=NONE|VOLUME=EXHAUSTED")
if __name__=="__main__":main()
