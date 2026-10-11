import json,sys,hashlib
from pathlib import Path
R=Path("/home/trading/TradingAI-HF-Lab");S=Path("/home/trading/.local/state/tradingai/jarvis-autonomous");P=R/"research_agent_v57_quantum_searcher/tools/v57_jarvis/v3/registry"
sys.path.insert(0,str(P));sys.path.insert(0,str(R/"research_agent_v57_quantum_searcher/src"))
import v57_hypothesis_generator_v4 as H
import v57_constrained_generator_v4 as C
def main():
 a=json.loads((S/"capability_admission_v1.json").read_text())
 if a.get("status")!="ADMIT" or a.get("capability")!="price_action" or not a.get("build_authorized") or a.get("execution_authorized") is not False: raise RuntimeError("ADMISSION_MISMATCH")
 raw="XAUUSD M5 SHORT price_action researchonly"; h=H.parse(raw)
 if h["families"]!=["price_action"] or h["market"]!="XAUUSD" or h["timeframe"]!="M5" or h["side"]!="SHORT": raise RuntimeError("PARSER_BINDING_FAILED")
 out=C.generate(h,n=4,seed=574361)
 fam=sorted({x["family"] for _,m in out for x in m["conditions"]}); feats=sorted({x["feature"] for _,m in out for x in m["conditions"]}); logics=sorted({m["logic"] for _,m in out})
 if fam!=["price_action"] or set(logics)&C.BLOCKED_FOR_PRICE_ACTION: raise RuntimeError("GENERATOR_BINDING_FAILED")
 if not all(s["execution"]["orders_allowed"] is False and s["execution"]["mode"]=="RESEARCH_ONLY" for s,_ in out): raise RuntimeError("SAFETY_FAILED")
 rec={"schema_version":1,"kind":"V57_PRICE_ACTION_PREFLIGHT_V1","status":"PASS","hypothesis":h,"families":fam,"features":feats,"logics":logics,"candidate_count":4,"evaluation_started":False,"orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False}
 q=S/"price_action_preflight_v1.tmp";q.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n");q.replace(S/"price_action_preflight_v1.json")
 print("ALL PASS|PRICE_ACTION_PREFLIGHT_V1|FAMILY=price_action|FEATURES="+",".join(feats)+"|N=4|EVALUATION=NOT_STARTED")
if __name__=="__main__":main()
