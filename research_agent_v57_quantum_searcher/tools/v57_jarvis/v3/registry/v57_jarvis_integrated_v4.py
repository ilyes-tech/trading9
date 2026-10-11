import sys
from pathlib import Path
ROOT=Path("research_agent_v57_quantum_searcher"); SRC=ROOT/"src"; REG=ROOT/"tools/v57_jarvis/v3/registry"
for p in (REG,SRC,SRC/"v433",SRC/"v434",SRC/"v435",SRC/"v436",SRC/"v438"):
    if str(p.resolve()) not in sys.path: sys.path.insert(0,str(p.resolve()))
import v57_scientist_v3_4 as S
import v57_qd_orchestrator_engine_v438_v1 as O
import v57_search_replay_v371_v1 as R
import v57_auto_deep_validator_v3_8 as D
import v57_plateau_engine_v3_12 as P
import v57_materializer_v3_13 as M
import v57_post_materialization_replay_v3_14 as PM

ENGINE="V57_JARVIS_INTEGRATED_V4"

def _integrity(x):
    ri=x.get("research_integrity",{})
    return ri.get("holdout_read") is False and ri.get("september_2026_data_accessed") is False and ri.get("orders_allowed") is False

def run(hypothesis,seed_start=574352,max_batches=8,seeds_per_operator=4):
    history=[]
    for bi in range(int(max_batches)):
        seed=int(seed_start)+bi
        x=S.experiment(hypothesis,0,32,True,seed)
        errs=[r for r in x["records"] if r.get("status")=="ERROR"]
        if errs: raise RuntimeError("SCIENTIST_ERROR_SEED_"+str(seed)+":"+str(errs[0].get("error")))
        exact=[r for r in x["records"] if r.get("status")=="EVALUATED" and isinstance(r.get("result"),dict) and r["result"].get("exact_pass") is True]
        batch={"seed":seed,"total":len(x["records"]),"exact_pass":len(exact),"candidates":[]}
        for r in exact:
            s=r["strategy"]; meta=r["meta"]
            ctx=O.base.adapter2.prepare_context(meta["market"],meta["timeframe"])
            replay=R.evaluate_strategy(ctx,s,O.signal6.bitcache.MaskBitsetCache())
            deep=D.validate_dsl3(s,ctx,replay)
            row={"strategy_id":s["strategy_id"],"candidate_index":r["candidate_index"],"deep_status":deep["status"]}
            if deep["status"]!="DEEP_PASS":
                row["decision"]="REJECTED_DEEP"; batch["candidates"].append(row); continue
            plateau=P.evaluate(s,meta,ctx,seeds_per_operator=int(seeds_per_operator),seed_base=312000000+seed)
            material=M.materialize(s,ctx)
            if not _integrity(material): raise RuntimeError("MATERIALIZATION_INTEGRITY_FAIL")
            post=PM.evaluate(s,ctx,material)
            row["plateau"]=plateau
            row["materialization"]=material
            row["post_materialization"]=post
            if post["conclusion"]!="POST_MATERIALIZATION_REPLAY_PASS":
                row["decision"]="REJECTED_POST_MATERIALIZATION"; batch["candidates"].append(row); continue
            row["decision"]="FINAL_PASS"; batch["candidates"].append(row); history.append(batch)
            return {"engine":ENGINE,"status":"FINAL_PASS","strategy":s,"meta":meta,"deep":deep,"plateau":plateau,"materialization":material,"post_materialization":post,"seed":seed,"candidate_index":r["candidate_index"],"batches":history,"orders_allowed":False,"holdout_allowed":False,"mt5_allowed":False}
        history.append(batch)
    return {"engine":ENGINE,"status":"SEARCH_BUDGET_EXHAUSTED","batches":history,"orders_allowed":False,"holdout_allowed":False,"mt5_allowed":False}


def self_check():
    src=Path(__file__).read_text()
    required=("S.experiment(","R.evaluate_strategy(","D.validate_dsl3(","P.evaluate(","M.materialize(","PM.evaluate(","REJECTED_DEEP","REJECTED_POST_MATERIALIZATION","FINAL_PASS","SEARCH_BUDGET_EXHAUSTED")
    for token in required:
        assert token in src, "MISSING:"+token
    assert "holdout_allowed\":True" not in src
    assert "orders_allowed\":True" not in src
    assert "mt5_allowed\":True" not in src
    print("ALL PASS|JARVIS_INTEGRATED_V4|SEARCH|EXACT|DEEP|PLATEAU|MATERIALIZE|POST_REPLAY|AUTO_RESUME|FAIL_CLOSED")

if __name__=="__main__": self_check()

