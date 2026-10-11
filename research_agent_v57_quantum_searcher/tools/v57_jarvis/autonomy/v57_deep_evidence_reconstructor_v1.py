import json,sys
from pathlib import Path
ROOT=Path("/home/trading/TradingAI-HF-Lab")
R=ROOT/"research_agent_v57_quantum_searcher"; REG=R/"tools/v57_jarvis/v3/registry"; SRC=R/"src"
for p in (REG,SRC,SRC/"v433",SRC/"v434",SRC/"v435",SRC/"v436",SRC/"v437",SRC/"v438"): sys.path.insert(0,str(p))
import v57_scientist_v3_4 as S, v57_qd_orchestrator_engine_v438_v1 as O
import v57_search_replay_v371_v1 as Replay, v57_auto_deep_validator_v3_8 as D
STATE=Path("/home/trading/.local/state/tradingai/jarvis-v438")
def main():
 plan=json.loads((STATE/"evidence_plan_v1.json").read_text())["plan"]
 if plan["action"]!="RECONSTRUCT_EXISTING_DEEP_EVIDENCE": raise RuntimeError("BAD_PLAN")
 market,tf,side=plan["space"].split("_"); seed=615352; target=plan["strategy_id"]
 h={"market":market,"timeframe":tf,"side":side,"hypothesis":"robust systematic trading strategy"}
 x=S.experiment(h,0,32,False,seed); hits=[i for i in x["items"] if i["strategy"]["strategy_id"]==target]
 if len(hits)!=1: raise RuntimeError("TARGET_RECONSTRUCTION_MISMATCH:"+str(len(hits)))
 item=hits[0]; ctx=O.base.adapter2.prepare_context(market,tf)
 replay=Replay.evaluate_strategy(ctx,item["strategy"],O.signal6.bitcache.MaskBitsetCache())
 if replay.get("exact_pass") is not True: raise RuntimeError("REPLAY_NO_LONGER_EXACT_PASS")
 deep=D.validate_dsl3(item["strategy"],ctx,replay)
 out={"schema_version":1,"kind":"JARVIS_DEEP_EVIDENCE_RECONSTRUCTION_V1","status":"PASS",
 "space":plan["space"],"strategy_id":target,"seed":seed,"deep":deep,
 "orders_allowed":False,"mt5_allowed":False,"holdout_allowed":False,"auto_promotion_allowed":False}
 t=STATE/"deep_evidence_v1.tmp";t.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");t.replace(STATE/"deep_evidence_v1.json")
 print("ALL PASS|DEEP_EVIDENCE_RECONSTRUCTED|"+deep["status"]+"|"+target[:12])
if __name__=="__main__": main()
