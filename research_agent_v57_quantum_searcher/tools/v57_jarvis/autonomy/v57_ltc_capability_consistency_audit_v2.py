import json,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 reg=json.loads((S/"multimarket_evidence_registry_v3.json").read_text());gate=json.loads((S/"ltc_evidence_gate_v1.json").read_text());adapter=json.loads((S/"ltc_capability_adapter_v1.json").read_text())
 ltc=reg["markets"]["LTCUSD"]
 if reg.get("status")!="PASS" or gate.get("status")!="SAFE_STOP" or adapter.get("status")!="DISCOVERED":raise RuntimeError("STATUS")
 if ltc.get("hypothesis_generator_supported") is not False or ltc.get("specialized_generator_supported") is not True:raise RuntimeError("GENERATOR_SCOPE")
 if adapter.get("sample_generated",0)<1 or adapter.get("evaluation_authorized") is not False:raise RuntimeError("ADAPTER")
 if ltc.get("historical_candidates")!=4096 or ltc.get("exact_pass")!=0 or gate.get("historical_exact_pass")!=0 or gate.get("repeat_unconstrained_search_allowed") is not False:raise RuntimeError("EVIDENCE")
 if any(x.get("orders_allowed") is not False or x.get("mt5_allowed") is not False or x.get("holdout_allowed") is not False for x in (reg,gate,adapter)):raise RuntimeError("SAFETY")
 doc={"schema_version":1,"kind":"V57_LTC_CAPABILITY_CONSISTENCY_AUDIT_V2","status":"PASS","finding":"NO_CONTRADICTION_GENERIC_GENERATOR_UNSUPPORTED_SPECIALIZED_GENERATOR_SUPPORTED","corrects":"ltc_capability_consistency_audit_v1.json","historical_candidates":4096,"exact_pass":0,"specialized_adapter_evaluation_authorized":False,"repeat_search_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"ltc_capability_consistency_audit_v2.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"ltc_capability_consistency_audit_v2.json")
 print("ALL PASS|LTC_CAPABILITY_CONSISTENCY_V2|SCOPES=CONSISTENT|EXACT_PASS=0|SEARCH=DENIED")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|LTC_CAPABILITY_CONSISTENCY_V2|"+str(e));sys.exit(3)
