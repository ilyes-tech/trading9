import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");NATIVE={"momentum","trend","volatility","volume","time"};MAP={"IMPROVE_STABILITY":"momentum","PRESERVE_CONCENTRATION_GATES":"volatility","EXPLORE_DISTINCT_CAUSAL_DIMENSION":"trend","IMPROVE_TEMPORAL_CONSISTENCY":"time","TEST_VOLUME_CONFIRMATION":"volume"}
def main():
 a=json.loads((S/"research_agenda_v4.json").read_text());covered={MAP[x["objective"]] for x in a["items"] if x.get("status")=="EXHAUSTED" and x.get("objective") in MAP};missing=sorted(NATIVE-covered);extra=sorted(covered-NATIVE)
 ok=a.get("active") is None and len(a.get("items",[]))==5 and all(x.get("status")=="EXHAUSTED" for x in a["items"]) and covered==NATIVE
 out={"schema_version":1,"kind":"JARVIS_NATIVE_COVERAGE_AUDIT_V1","status":"PASS" if ok else "FAIL","native_families":sorted(NATIVE),"covered_families":sorted(covered),"missing_families":missing,"unexpected_families":extra,"agenda_items":len(a.get("items",[])),"all_exhausted":all(x.get("status")=="EXHAUSTED" for x in a.get("items",[])),"active":a.get("active"),"next_action":"SAFE_STOP_NATIVE_CATALOG_EXHAUSTED" if ok else "REPAIR_COVERAGE","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"native_coverage_audit_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"native_coverage_audit_v1.json")
 print(("ALL PASS" if ok else "STOP|FAIL")+"|NATIVE_COVERAGE_AUDIT_V1|COVERED="+str(len(covered))+"/5|MISSING="+str(len(missing))+"|ACTIVE="+str(a.get("active"))+"|NEXT="+out["next_action"])
if __name__=="__main__":main()
