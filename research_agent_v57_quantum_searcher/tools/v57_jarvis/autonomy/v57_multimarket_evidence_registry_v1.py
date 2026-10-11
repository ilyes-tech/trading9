import json,hashlib
from pathlib import Path
S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
def load(name,kind):
 p=S/name;x=json.loads(p.read_text())
 if x.get("kind")!=kind:raise RuntimeError("INVALID_SOURCE:"+name)
 return x,hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 l,lh=load("ltc_evidence_gate_v1.json","V57_LTC_EVIDENCE_GATE_V1")
 v,vh=load("volume_feedback_v1.json","JARVIS_VOLUME_FEEDBACK_V1")
 p,ph=load("price_action_feedback_v1.json","V57_PRICE_ACTION_FEEDBACK_V1")
 if l["status"]!="SAFE_STOP" or l["historical_exact_pass"]!=0 or l["historical_budget"]!=4096:raise RuntimeError("LTC_GATE")
 if v["verdict"]!="NO_EVIDENCE" or v["exact_pass_count"]!=0:raise RuntimeError("VOLUME_GATE")
 if p["verdict"]!="NO_DEPLOYMENT_EVIDENCE" or p["deployment_evidence_pass"]!=0:raise RuntimeError("PRICE_ACTION_GATE")
 markets={k:{"hypothesis_generator_supported":True,"market_specific_outcome":"NOT_AUDITED_IN_THIS_REGISTRY"} for k in ("BTCUSD","ETHUSD","EURUSD","GBPUSD","USDJPY","XAUUSD")}
 markets["LTCUSD"]={"hypothesis_generator_supported":False,"specialized_generator_supported":True,"historical_candidates":4096,"exact_pass":0,"market_specific_outcome":"SAFE_STOP_NO_EXACT_PASS","source_sha256":lh}
 branches={"volume":{"verdict":"NO_EVIDENCE","scope":"BOUNDED_PROBE_NOT_MARKET_WIDE","source_sha256":vh},"price_action":{"verdict":"NO_DEPLOYMENT_EVIDENCE","scope":"XAUUSD_BOUNDED_PROBE","initial_exact_pass":2,"deployment_pass":0,"source_sha256":ph}}
 result={"schema_version":1,"kind":"V57_MULTIMARKET_EVIDENCE_REGISTRY_V1","status":"PASS","markets":markets,"branches":branches,"auto_promotion_allowed":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"next_gate":"MARKET_SPECIFIC_FOREX_EVIDENCE_AUDIT"}
 q=S/"multimarket_evidence_registry_v1.tmp";q.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");q.replace(S/"multimarket_evidence_registry_v1.json")
 print("ALL PASS|MULTIMARKET_EVIDENCE_REGISTRY_V1|MARKETS=7|LTC=SAFE_STOP|FOREX=NOT_AUDITED|PROMOTION=DENIED")
if __name__=="__main__":main()
