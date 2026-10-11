import json,hashlib,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
F=("momentum","trend","volatility","volume","time")
M={"IMPROVE_STABILITY":"momentum","PRESERVE_CONCENTRATION_GATES":"volatility","EXPLORE_DISTINCT_CAUSAL_DIMENSION":"trend","IMPROVE_TEMPORAL_CONSISTENCY":"time","TEST_VOLUME_CONFIRMATION":"volume"}
def main():
 p=S/"research_agenda_v4.json";a=json.loads(p.read_text());v=json.loads((S/"capability_agenda_v5.json").read_text())
 if a.get("kind")!="JARVIS_RESEARCH_AGENDA_V4" or len(a.get("items",[]))!=5 or v.get("state")!="EXHAUSTED_FOR_CURRENT_PROBE":raise RuntimeError("INPUT")
 seen={}
 for x in a["items"]:
  if x.get("status")!="EXHAUSTED" or x.get("objective") not in M:raise RuntimeError("UNKNOWN_AGENDA_ITEM")
  family=M[x["objective"]]
  if x.get("native_family",family)!=family:raise RuntimeError("FAMILY_MISMATCH")
  seen[family]=x["id"]
 if set(seen)!=set(F):raise RuntimeError("COVERAGE")
 doc={"schema_version":1,"kind":"V57_NATIVE_CAPABILITY_COVERAGE_V2","status":"PASS","agenda_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"native_families":list(F),"exhausted_families":sorted(seen),"uncovered_native_families":[],"next_action":"SAFE_STOP_UNTIL_EVIDENCE_BACKED_NEW_CAUSAL_FAMILY","new_research_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"native_capability_coverage_v2.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"native_capability_coverage_v2.json")
 print("ALL PASS|NATIVE_CAPABILITY_COVERAGE_V2|FAMILIES=5|EXHAUSTED=5|NEW_SEARCH=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|NATIVE_CAPABILITY_COVERAGE_V2|"+str(e));sys.exit(3)
