import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 r=json.loads((S/"capability_registry_v1.json").read_text());d=json.loads((S/"failure_diagnosis_v2.json").read_text());a=json.loads((S/"research_agenda_v4.json").read_text())
 cand=r.get("admission_candidates",[]);robust=d.get("conclusion")=="ROBUSTNESS_INSUFFICIENT";terminal=a.get("active") is None and all(x.get("status")=="EXHAUSTED" for x in a.get("items",[]))
 admitted=cand[0] if len(cand)==1 and cand[0]=="price_action" and robust and terminal else None
 out={"schema_version":1,"kind":"JARVIS_CAPABILITY_ADMISSION_V1","status":"ADMIT" if admitted else "REJECT","capability":admitted,"evidence":{"native_applicable":admitted in r.get("native_applicable_families",[]) if admitted else False,"currently_exposed":admitted in r.get("jarvis_exposed_families",[]) if admitted else False,"already_covered":admitted in r.get("covered_families",[]) if admitted else False,"diagnosis":d.get("conclusion"),"agenda_terminal":terminal},"constraints":["NATIVE_GENERATOR_SUPPORT_REQUIRED","MARKET_APPLICABLE_REQUIRED","UNEXPOSED_REQUIRED","UNTESTED_REQUIRED","PERSISTENT_DIAGNOSIS_REQUIRED","RESEARCH_ONLY"],"next_action":"BUILD_VERSIONED_PARSER_SUPPORT" if admitted else "SAFE_STOP","build_authorized":bool(admitted),"execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"capability_admission_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"capability_admission_v1.json")
 print(("ALL PASS" if admitted else "STOP|FAIL")+"|CAPABILITY_ADMISSION_V1|STATUS="+out["status"]+"|CAPABILITY="+str(admitted)+"|BUILD="+str(out["build_authorized"])+"|EXECUTION=FALSE")
if __name__=="__main__":main()
