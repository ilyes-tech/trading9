import v57_scientist_v3_4 as S
import v57_qd_orchestrator_engine_v438_v1 as O
import v57_search_replay_v371_v1 as R
import v57_auto_deep_validator_v3_8 as D
ENGINE="V57_JARVIS_SCIENCE_LOOP_V3_9"
def run(hypothesis,seed_start=574352,max_batches=8):
    out=[]
    for bi in range(int(max_batches)):
        seed=int(seed_start)+bi
        x=S.experiment(hypothesis,0,32,True,seed)
        errs=[r for r in x["records"] if r["status"]=="ERROR"]
        if errs: raise RuntimeError("SCIENTIST_ERROR_SEED_"+str(seed)+":"+str(errs[0].get("error")))
        exact=[r for r in x["records"] if r["status"]=="EVALUATED" and isinstance(r.get("result"),dict) and r["result"].get("exact_pass")]
        row={"seed":seed,"total":len(x["records"]),"exact_pass":len(exact),"deep":[]}
        for r in exact:
            s=r["strategy"]; m=r["meta"]; c=O.base.adapter2.prepare_context(m["market"],m["timeframe"]); q=R.evaluate_strategy(c,s,O.signal6.bitcache.MaskBitsetCache()); d=D.validate_dsl3(s,c,q)
            row["deep"].append({"strategy_id":s["strategy_id"],"candidate_index":r["candidate_index"],"status":d["status"],"deep":d.get("deep")})
            if d["status"]=="DEEP_PASS":
                out.append(row); return {"engine":ENGINE,"status":"DEEP_PASS_FOUND","winner":d,"strategy":s,"seed":seed,"candidate_index":r["candidate_index"],"batches":out,"orders_allowed":False,"holdout_allowed":False}
        out.append(row)
    return {"engine":ENGINE,"status":"SEARCH_BUDGET_EXHAUSTED","batches":out,"orders_allowed":False,"holdout_allowed":False}
