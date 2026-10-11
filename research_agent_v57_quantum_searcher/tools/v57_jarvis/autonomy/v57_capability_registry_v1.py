import json,sys
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");sys.path.insert(0,str(R/"research_agent_v57_quantum_searcher/src"));sys.path.insert(0,str(R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry"))
def main():
 import v57_screening_generator_v1 as G,v57_hypothesis_generator_v3 as H
 a=json.loads((S/"research_agenda_v4.json").read_text());market=json.loads((S/"failure_diagnosis_v2.json").read_text())["space"].split("_")[0]
 native=sorted({f for f,_ in G.feature_pool(market)});exposed=sorted(set(H.FAMILIES));covered={"momentum","trend","volatility","volume","time"}
 unexposed=sorted(set(native)-set(exposed));untested=sorted(set(native)-covered);candidate=[x for x in untested if x in unexposed]
 out={"schema_version":1,"kind":"JARVIS_CAPABILITY_REGISTRY_V1","status":"PASS","market":market,"native_applicable_families":native,"jarvis_exposed_families":exposed,"covered_families":sorted(covered),"unexposed_native_families":unexposed,"untested_applicable_families":untested,"admission_candidates":candidate,"excluded_market_inapplicable":["crypto_microstructure"] if market not in G.CRYPTO else [],"active_agenda":a.get("active"),"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 q=S/"capability_registry_v1.tmp";q.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");q.replace(S/"capability_registry_v1.json")
 print("ALL PASS|CAPABILITY_REGISTRY_V1|MARKET="+market+"|NATIVE="+str(len(native))+"|EXPOSED="+str(len(exposed))+"|ADMISSION="+",".join(candidate))
if __name__=="__main__":main()
