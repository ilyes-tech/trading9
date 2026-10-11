import hashlib,json
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 d=json.loads((S/"native_capability_discovery_v1.json").read_text()); f=json.loads((S/"failure_diagnosis_v2.json").read_text())
 if d.get("status")!="DISCOVERED" or d.get("selected_family")!="volume": raise RuntimeError("NO_VOLUME_CAPABILITY_DISCOVERED")
 obj="TEST_VOLUME_CONFIRMATION"; oid=hashlib.sha256((f["space"]+"|"+obj+"|volume").encode()).hexdigest()
 out={"schema_version":1,"kind":"JARVIS_CAPABILITY_REPLAN_V1","status":"PROPOSED","proposal":{"id":oid,"space":f["space"],"objective":obj,"causal_dimension":"VOLUME_CONFIRMATION","native_family":"volume","target_metrics":[x["metric"] for x in f["failed_gates"]],"preserve_metrics":[x["metric"] for x in f["passed_gates"]]},"max_new_objectives":1,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"capability_replan_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"capability_replan_v1.json")
 print("ALL PASS|CAPABILITY_REPLAN_V1|OBJECTIVE="+obj+"|DIMENSION=VOLUME_CONFIRMATION|FAMILY=volume")
if __name__=="__main__": main()
