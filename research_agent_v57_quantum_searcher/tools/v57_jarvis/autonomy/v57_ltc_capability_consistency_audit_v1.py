import json,hashlib,sys
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def main():
 reg=json.loads((S/"multimarket_evidence_registry_v3.json").read_text())
 gate=json.loads((S/"ltc_evidence_gate_v1.json").read_text())
 adapter=json.loads((S/"ltc_capability_adapter_v1.json").read_text())
 if reg.get("status")!="PASS" or gate.get("status")!="SAFE_STOP" or adapter.get("status")!="DISCOVERED":raise RuntimeError("SOURCE_STATUS")
 ltc=reg["markets"]["LTCUSD"]
 if ltc.get("hypothesis_generator_supported") is not False or adapter.get("sample_generated",0)<1:raise RuntimeError("EXPECTED_SCOPE_DIFFERENCE_MISSING")
 if gate.get("historical_exact_pass")!=0 or gate.get("historical_budget")!=4096 or gate.get("repeat_unconstrained_search_allowed") is not False:raise RuntimeError("LTC_EVIDENCE")
 if any(x.get("orders_allowed") is not False or x.get("mt5_allowed") is not False or x.get("holdout_allowed") is not False for x in (reg,gate,adapter)):raise RuntimeError("SAFETY")
 doc={"schema_version":1,"kind":"V57_LTC_CAPABILITY_CONSISTENCY_AUDIT_V1","status":"PASS","finding":"REGISTRY_V3_GENERATOR_SUPPORTED_FALSE_WHILE_SPECIALIST_ADAPTER_DISCOVERED","interpretation":"CAPABILITY_SCOPE_MISMATCH_NOT_PROOF_OF_UNTESTED_EDGE","adapter_sample_generated":adapter["sample_generated"],"historical_budget":4096,"historical_exact_pass":0,"repeat_search_authorized":False,"research_execution_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"ltc_capability_consistency_audit_v1.tmp";q.write_text(json.dumps(doc,sort_keys=True,indent=2)+"\n");q.replace(S/"ltc_capability_consistency_audit_v1.json")
 print("ALL PASS|LTC_CAPABILITY_CONSISTENCY_AUDIT_V1|MISMATCH=DOCUMENTED|EXACT_PASS=0|RESEARCH=NO")
if __name__=="__main__":
 try:main()
 except Exception as e:print("STOP|FAIL|LTC_CAPABILITY_CONSISTENCY_AUDIT_V1|"+str(e));sys.exit(3)
