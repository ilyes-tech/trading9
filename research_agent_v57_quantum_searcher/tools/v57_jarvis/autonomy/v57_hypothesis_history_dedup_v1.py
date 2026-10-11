import json,hashlib,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def read(n):return json.loads((S/n).read_text())
def fingerprint(x):
 keys=("market","space","causal_dimension","native_family","objective","parent_strategy_id")
 return hashlib.sha256(json.dumps({k:x.get(k) for k in keys},sort_keys=True,separators=(",",":")).encode()).hexdigest()
def classify(x,history):
 if not isinstance(x,dict) or not x.get("causal_dimension"):return "DENY_INCOMPLETE"
 if x.get("hypothesis_id") in history["ids"]:return "DENY_REPEATED_ID"
 if fingerprint(x) in history["fingerprints"]:return "DENY_REPEATED_CAUSAL_SIGNATURE"
 return "REVIEW_REQUIRED_NOT_AUTHORIZED"
def main():
 a=read("research_agenda_v4.json");h=read("refined_hypothesis_v3.json");pa=read("capability_agenda_v5.json")
 if len(a["items"])!=5 or h.get("status")!="EXHAUSTED" or pa.get("repeat_same_probe_allowed") is not False:raise RuntimeError("HISTORY")
 items=[]
 for x in a["items"]:
  items.append({"hypothesis_id":x["id"],"market":x["space"].split("_")[0],"space":x["space"],"causal_dimension":x.get("causal_dimension",x["objective"]),"native_family":x.get("native_family"),"objective":x["objective"],"parent_strategy_id":None})
 items.append({"hypothesis_id":h["hypothesis_id"],"market":"XAUUSD","space":h["objective"]["space"],"causal_dimension":h["objective"]["agenda_objective"],"native_family":None,"objective":h["objective"]["agenda_objective"],"parent_strategy_id":h["objective"]["parent_strategy_id"]})
 hist={"ids":{x["hypothesis_id"] for x in items},"fingerprints":{fingerprint(x) for x in items}}
 tests=[(items[0],"DENY_REPEATED_ID"),(dict(items[0],hypothesis_id="new"),"DENY_REPEATED_CAUSAL_SIGNATURE"),({"causal_dimension":""},"DENY_INCOMPLETE"),({"market":"XAUUSD","space":"XAUUSD_M5_SHORT","causal_dimension":"UNSEEN_CAUSE","hypothesis_id":"new"},"REVIEW_REQUIRED_NOT_AUTHORIZED")]
 if any(classify(x,hist)!=expected for x,expected in tests):raise RuntimeError("TESTS")
 doc={"schema_version":1,"kind":"V57_HYPOTHESIS_HISTORY_DEDUP_V1","status":"PASS","history_items":len(items),"fingerprints":len(hist["fingerprints"]),"tests":len(tests),"novelty_proven":False,"execution_authorized":False,"limitations":"EXACT_CAUSAL_SIGNATURE_ONLY_NOT_SEMANTIC_NOVELTY","orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"hypothesis_history_dedup_v1.tmp";q.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n");q.replace(S/"hypothesis_history_dedup_v1.json")
 print("ALL PASS|HYPOTHESIS_HISTORY_DEDUP_V1|HISTORY="+str(len(items))+"|TESTS=4|EXECUTION=DENIED")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|HYPOTHESIS_HISTORY_DEDUP_V1|"+str(e));sys.exit(3)
