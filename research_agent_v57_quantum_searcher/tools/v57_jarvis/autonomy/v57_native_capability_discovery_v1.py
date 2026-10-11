import json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
NATIVE=("momentum","trend","volatility","volume","time")
KNOWN={"IMPROVE_STABILITY":"momentum","PRESERVE_CONCENTRATION_GATES":"volatility","EXPLORE_DISTINCT_CAUSAL_DIMENSION":"trend","IMPROVE_TEMPORAL_CONSISTENCY":"time"}
def main():
 a=json.loads((S/"research_agenda_v3.json").read_text());d=json.loads((S/"failure_diagnosis_v2.json").read_text())
 if a.get("active") is not None or not a.get("items") or any(x.get("status")!="EXHAUSTED" for x in a["items"]):raise RuntimeError("CAPABILITY_DISCOVERY_PRECONDITION_FAILED")
 covered={KNOWN[x["objective"]] for x in a["items"] if x["objective"] in KNOWN};uncovered=[x for x in NATIVE if x not in covered]
 failed={x["metric"] for x in d.get("failed_gates",[])};robust=bool(failed & {"min_boot_mean_positive_probability","min_boot_pf_ge1_probability","positive_half_segments"})
 selected="volume" if robust and "volume" in uncovered else None
 out={"schema_version":1,"kind":"JARVIS_NATIVE_CAPABILITY_DISCOVERY_V1","status":"DISCOVERED" if selected else "NO_JUSTIFIED_CAPABILITY","native_families":list(NATIVE),"covered_families":sorted(covered),"uncovered_families":uncovered,"selected_family":selected,"reason":"UNTESTED_NATIVE_FAMILY_RELEVANT_TO_PERSISTENT_ROBUSTNESS_FAILURE" if selected else "NO_UNTESTED_JUSTIFIED_NATIVE_FAMILY","next_action":"PROPOSE_VOLUME_CONFIRMATION_BRANCH" if selected else "SAFE_STOP","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=S/"native_capability_discovery_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(S/"native_capability_discovery_v1.json")
 print("ALL PASS|NATIVE_CAPABILITY_DISCOVERY_V1|STATUS="+out["status"]+"|UNCOVERED="+",".join(uncovered)+"|SELECTED="+str(selected))
if __name__=="__main__":main()
