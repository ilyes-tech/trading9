import json,hashlib,sys
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
sys.path.insert(0,str(R/"research_agent_v57_quantum_searcher/src/v435_ltc"))
def main():
 import v57_v435_ltc_generator_v1 as L
 import v57_v435_ltc_context_v1 as C
 L.patch_generator()
 generated=L.generate(4,seed=574351,start=0)
 if len(generated)!=4 or any(s["market"]["symbol"]!="LTCUSD" or s["execution"]["orders_allowed"] is not False for s,m in generated):raise RuntimeError("LTC_GENERATOR_INVALID")
 paths=[R/("historical/kraken_micro_m1/extracted/LTCUSD_MICRO_2026_%02d_M1.csv"%m) for m in range(3,7)]
 if not all(x.is_file() for x in paths):raise RuntimeError("LTC_DATA_MISSING")
 caps={"schema_version":1,"kind":"V57_LTC_CAPABILITY_ADAPTER_V1","status":"DISCOVERED","market":"LTCUSD","timeframes":list(C.TFS),"native_feature_pool":len(L.gen.feature_pool("LTCUSD")),"sample_generated":len(generated),"data_months":[3,4,5,6],"evaluation_authorized":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"next_gate":"SCIENTIST_LTC_ADAPTER_PREFLIGHT"}
 q=S/"ltc_capability_adapter_v1.tmp";q.write_text(json.dumps(caps,indent=2,sort_keys=True)+"\n");q.replace(S/"ltc_capability_adapter_v1.json")
 print("ALL PASS|LTC_CAPABILITY_ADAPTER_V1|MARKET=LTCUSD|POOL="+str(caps["native_feature_pool"])+"|GENERATED=4|EVALUATION=FALSE")
if __name__=="__main__":main()
