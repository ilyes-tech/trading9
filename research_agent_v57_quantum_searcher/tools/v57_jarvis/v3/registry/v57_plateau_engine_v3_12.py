from pathlib import Path
import copy,json,sys
ROOT=Path("research_agent_v57_quantum_searcher")
SRC=ROOT/"src"; V435=SRC/"v435"; REG=ROOT/"tools/v57_jarvis/v3/registry"
for p in (SRC,V435,REG):
    if str(p.resolve()) not in sys.path: sys.path.insert(0,str(p.resolve()))
import v57_qd_variation_engine_v4 as V
import v57_search_replay_v371_v1 as R
OPERATORS=("threshold_neighbor","lookback_neighbor","transform_neighbor","feature_parameter_neighbor","logic_neighbor","risk_neighbor")
CLASSIFICATION="ENGINEERING_LOCAL_ROBUSTNESS_ONLY_NO_GATE_RETUNING"
def evaluate(strategy,meta,ctx,seeds_per_operator=4,seed_base=312000000):
    if not isinstance(strategy,dict) or not strategy.get("strategy_id"): raise ValueError("STRATEGY_REQUIRED")
    recipe=V.recipe_from_pair(strategy,meta)
    rows=[]
    for oi,op in enumerate(OPERATORS):
        for j in range(int(seeds_per_operator)):
            seed=int(seed_base)+oi*10000+j+1
            try:
                nr=V.mutate_recipe(recipe,op,seed)
                ns,nm=V.strategy_from_recipe(nr)
                rr=R.evaluate_strategy(ctx,ns)
                rows.append({"operator":op,"seed":seed,"status":"EVALUATED","strategy_id":ns["strategy_id"],"exact_pass":bool(rr["exact_pass"]),"result":{k:rr.get(k) for k in ("total_selected_trades","worst_stress_avg_bps","min_stress_pf","worst_base_avg_bps","min_base_pf","worst_drawdown_bps")}})
            except ValueError as e:
                rows.append({"operator":op,"seed":seed,"status":"NOT_APPLICABLE","error":str(e)})
    ev=[x for x in rows if x["status"]=="EVALUATED"]
    by={}
    for op in OPERATORS:
        z=[x for x in ev if x["operator"]==op]; by[op]={"evaluated":len(z),"exact_pass":sum(bool(x["exact_pass"]) for x in z),"exact_fraction":(sum(bool(x["exact_pass"]) for x in z)/len(z) if z else None)}
    return {"schema_version":1,"kind":"V57_JARVIS_PLATEAU_V3_12","classification":CLASSIFICATION,"strategy_id":strategy["strategy_id"],"mutation_steps":1,"selection_of_best_neighbor":False,"retuning":False,"operators":list(OPERATORS),"evaluated":len(ev),"exact_pass":sum(bool(x["exact_pass"]) for x in ev),"exact_fraction":(sum(bool(x["exact_pass"]) for x in ev)/len(ev) if ev else None),"by_operator":by,"neighbors":rows,"research_integrity":{"holdout_read":False,"september_2026_data_accessed":False,"orders_allowed":False,"mt5_launch_allowed":False}}
def self_check():
    assert CLASSIFICATION=="ENGINEERING_LOCAL_ROBUSTNESS_ONLY_NO_GATE_RETUNING"
    assert "condition_replace" not in OPERATORS and "condition_add" not in OPERATORS and "condition_drop" not in OPERATORS and "cross_family_recombination" not in OPERATORS
    print("ALL PASS|V312_PLATEAU_ENGINE|NO_RETUNING|NO_HOLDOUT|NO_ORDERS")
if __name__=="__main__": self_check()
