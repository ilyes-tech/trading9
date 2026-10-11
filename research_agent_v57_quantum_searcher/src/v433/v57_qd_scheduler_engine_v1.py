from pathlib import Path
import copy, hashlib, json, math, sys

HERE=Path(__file__).resolve()
V433=HERE.parent
SRC=HERE.parents[1]
ROOT=HERE.parents[2]
for p in (V433,SRC):
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

import v57_qd_archive_engine_v1 as archive
import v57_qd_variation_engine_v1 as variation
import v57_search_runtime_v3 as runtime

ENGINE="V57_V433_QD_SCHEDULER_ENGINE_V1"
POLICY_PATH=ROOT/"config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
P=json.loads(POLICY_PATH.read_text())

EXPECTED={
    "policy":"d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f",
    "archive_engine":"419d4c405dc55b2a574e3ee304b8542a1a15490b41229a05aa1dada12aab287f",
    "archive_freeze":"0bfa5c7ab8c84e96ab09a3e3bfda860b0440daf2af6b1c9a63b28b588522535f",
    "variation_engine":"21acf86faed0e833dc4aca5483d21cc9fe96cdb39c97f284c6e129a9c9bdfa87",
    "variation_freeze":"a67b02fd7d35203f7307222af45ec7a2f752d499f2361cf8d6343df867e0a241",
    "runtime_engine":"6d6f747e4d3c1ef3a67a2544b0de5ac783ee7bb9cbdf7aa180f30bc99bce04a0",
    "runtime_freeze":"89c9561e7e38848ef60d5febbf5873d7580926c6328074ea6a990c91bd5dc968",
    "replay_engine":"4732f4e824f5af4b2942733367239fecbef8198750c0a7af6f96f68d27bf8706",
    "replay_freeze":"b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626",
}
MIN_PASSED=int(P["scheduler"]["parent_eligibility"]["minimum_passed_folds"])
INITIAL=int(P["scheduler"]["successive_halving"]["initial_offspring_per_parent"])
MULTIPLIER=int(P["scheduler"]["successive_halving"]["offspring_multiplier_per_round"])
SURVIVOR_FRACTION=float(P["scheduler"]["successive_halving"]["survivor_fraction_per_round"])
SURVIVOR_ROUNDING="FLOOR_MIN_ONE"
PARENT_POOL_RULE="ALL_ACTIVE_ARCHIVE_ENTRIES_WITH_PASSED_FOLDS_GTE_POLICY_MIN"
RANK_RULE="TIER_THEN_REPEATED_NONDOMINATED_FRONTS_THEN_CROWDING_THEN_STRATEGY_ID"

def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _ensure():
    paths={
        "policy":POLICY_PATH,
        "archive_engine":V433/"v57_qd_archive_engine_v1.py",
        "archive_freeze":ROOT/"config/v433/V57_V433_QD_ARCHIVE_ENGINE_V1_FREEZE_V1.json",
        "variation_engine":V433/"v57_qd_variation_engine_v1.py",
        "variation_freeze":ROOT/"config/v433/V57_V433_QD_VARIATION_ENGINE_V1_FREEZE_V1.json",
        "runtime_engine":V433/"v57_search_runtime_v3.py",
        "runtime_freeze":ROOT/"config/v433/V57_V433_SEARCH_RUNTIME_V3_FREEZE_V1.json",
        "replay_engine":V433/"v57_search_replay_v1.py",
        "replay_freeze":ROOT/"config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json",
    }
    got={k:H(v) for k,v in paths.items()}
    if got!=EXPECTED:
        raise RuntimeError("QD_SCHEDULER_ANCHOR_MISMATCH:"+str(got))
    af=json.loads(paths["archive_freeze"].read_text())
    if af.get("status")!="FROZEN_AFTER_SEMANTIC_AUDIT" or af.get("next_stage")!="V433_QD_SCHEDULER_ENGINE_V1":
        raise RuntimeError("ARCHIVE_FREEZE_STATE_MISMATCH")
    if P["scheduler"]["bootstrap"]!="PURE_EXPLORATION":
        raise RuntimeError("BOOTSTRAP_POLICY_CHANGED")
    if P["scheduler"]["parent_eligibility"]["fallback_if_empty"]!="PURE_EXPLORATION":
        raise RuntimeError("PARENT_FALLBACK_CHANGED")
    if P["scheduler"]["side_independent_search"] is not True or P["scheduler"]["automatic_long_short_mirroring"] is not False:
        raise RuntimeError("SIDE_INDEPENDENCE_CHANGED")
    h=P["scheduler"]["successive_halving"]
    if h["unit"]!="COMPLETE_CANDIDATE_REPLAY" or h["partial_fold_semantics_change_forbidden"] is not True:
        raise RuntimeError("HALVING_REPLAY_UNIT_CHANGED")
    if (INITIAL,MULTIPLIER,SURVIVOR_FRACTION)!=(4,2,0.5):
        raise RuntimeError("HALVING_NUMERIC_POLICY_CHANGED")
    if int(P["budget"]["cycle"]["exploration_budget"])+int(P["budget"]["cycle"]["exploitation_budget"])!=int(P["budget"]["cycle"]["total_budget"]):
        raise RuntimeError("CYCLE_BUDGET_MISMATCH")
    archive._ensure()
    variation._ensure()
    runtime._ensure()
    return True

def _dedup_entries(entries):
    out={}
    for e in entries:
        archive._entry_contract(e)
        sid=e["strategy_id"]
        fp=hashlib.sha256(archive.canonical(e).encode()).hexdigest()
        if sid in out and out[sid][0]!=fp:
            raise ValueError("STRATEGY_ID_ENTRY_CONFLICT:"+sid)
        out[sid]=(fp,e)
    return [out[s][1] for s in sorted(out)]

def rank_entries(entries):
    remaining=_dedup_entries(entries)
    ranked=[]
    for tier in sorted({int(e["tier"]) for e in remaining}):
        pool=[e for e in remaining if int(e["tier"])==tier]
        while pool:
            front=archive.nondominated(pool)
            cd=archive.crowding(front)
            front=sorted(front,key=lambda e:(
                float("-inf") if math.isinf(cd[e["strategy_id"]]) else -cd[e["strategy_id"]],
                e["strategy_id"],
            ))
            ranked.extend(front)
            used={e["strategy_id"] for e in front}
            pool=[e for e in pool if e["strategy_id"] not in used]
    return ranked

def eligible_parents(ar):
    archive.validate(ar)
    rows=[e for e in archive.active_entries(ar) if int(e["passed_folds"])>=MIN_PASSED]
    return rank_entries(rows)

def initial_parent_ids(ar, exploitation_budget):
    budget=max(0,int(exploitation_budget))
    capacity=budget//INITIAL
    return [e["strategy_id"] for e in eligible_parents(ar)[:capacity]]

def offspring_per_parent(round_index):
    r=int(round_index)
    if r<0:
        raise ValueError("NEGATIVE_ROUND")
    return INITIAL*(MULTIPLIER**r)

def survivor_count(parent_count):
    n=int(parent_count)
    if n<=0:
        return 0
    if n==1:
        return 1
    return max(1,int(math.floor(n*SURVIVOR_FRACTION)))

def round_capacity(parent_count, remaining_budget, round_index):
    n=max(0,int(parent_count))
    budget=max(0,int(remaining_budget))
    per=offspring_per_parent(round_index)
    return min(n,budget//per)

def _record_entry(record):
    if record.get("status")!="EVALUATED" or not isinstance(record.get("result"),dict):
        return None
    folds=record["result"].get("folds")
    if not isinstance(folds,list) or len(folds)!=3:
        raise ValueError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
    return archive.entry(record)

def parent_representatives(parent_ids, round_records):
    ids=list(dict.fromkeys(str(x) for x in parent_ids))
    allowed=set(ids)
    groups={sid:[] for sid in ids}
    for r in round_records:
        pid=str(r.get("parent_strategy_id",""))
        if pid not in allowed:
            raise ValueError("UNKNOWN_PARENT_STRATEGY_ID:"+pid)
        e=_record_entry(r)
        if e is not None:
            groups[pid].append(e)
    reps={}
    for sid,entries in groups.items():
        if entries:
            reps[sid]=rank_entries(entries)[0]
    return reps

def survivor_parent_ids(parent_ids, round_records):
    ids=list(dict.fromkeys(str(x) for x in parent_ids))
    if not ids:
        return []
    reps=parent_representatives(ids,round_records)
    ranked_rep=rank_entries(list(reps.values())) if reps else []
    ordered=[]
    for e in ranked_rep:
        ordered.extend(sorted(pid for pid,x in reps.items() if x["strategy_id"]==e["strategy_id"] and pid not in ordered))
    ordered.extend(sorted(set(ids)-set(ordered)))
    return ordered[:survivor_count(len(ids))]

def scheduler_contract():
    return {
        "engine":ENGINE,
        "parent_pool_rule":PARENT_POOL_RULE,
        "minimum_passed_folds":MIN_PASSED,
        "rank_rule":RANK_RULE,
        "survivor_rounding":SURVIVOR_ROUNDING,
        "initial_offspring_per_parent":INITIAL,
        "offspring_multiplier_per_round":MULTIPLIER,
        "survivor_fraction_per_round":SURVIVOR_FRACTION,
        "complete_candidate_replay_only":True,
        "novelty_acceptance_gate":False,
        "automatic_long_short_mirroring":False,
        "holdout_read":False,
        "orders_allowed":False,
    }

def self_check():
    _ensure()
    if survivor_count(6)!=3 or survivor_count(3)!=1 or survivor_count(1)!=1:
        raise AssertionError("FLOOR_HALVING_CONTRACT_FAILURE")
    if [offspring_per_parent(i) for i in range(4)]!=[4,8,16,32]:
        raise AssertionError("OFFSPRING_MULTIPLIER_FAILURE")
    if round_capacity(6,23,0)!=5 or round_capacity(6,24,0)!=6:
        raise AssertionError("ROUND_CAPACITY_FAILURE")
    pairs=variation.gen.generate(8,949001,0)
    entries=[]
    for i,(s,m) in enumerate(pairs):
        folds=[
            {"fold_index":fi,"pass":fi==0,"tpd":4.0+i*0.01+fi*0.01,"selected_trades":35+i+fi,
             "stress_avg_bps":-2.0+i*0.2+fi*0.01,"base_avg_bps":-1.0+i*0.2+fi*0.01}
            for fi in range(3)
        ]
        rec={"status":"EVALUATED","strategy":copy.deepcopy(s),"meta":copy.deepcopy(m),
             "result":{"strategy_id":s["strategy_id"],"market":m["market"],"timeframe":m["timeframe"],"side":m["side"],
                       "exact_pass":False,"folds":folds,
                       "worst_stress_avg_bps":min(f["stress_avg_bps"] for f in folds),
                       "min_stress_pf":0.70+i*0.01,
                       "worst_base_avg_bps":min(f["base_avg_bps"] for f in folds),
                       "min_base_pf":0.80+i*0.01,
                       "worst_drawdown_bps":-300.0+i,
                       "total_selected_trades":sum(f["selected_trades"] for f in folds)}}
        entries.append(archive.entry(rec))
    a=rank_entries(entries)
    b=rank_entries(list(reversed(entries)))
    if [e["strategy_id"] for e in a]!=[e["strategy_id"] for e in b]:
        raise AssertionError("RANK_ORDER_DEPENDENCE")
    c=scheduler_contract()
    if c["parent_pool_rule"]!=PARENT_POOL_RULE or c["survivor_rounding"]!="FLOOR_MIN_ONE":
        raise AssertionError("CONTRACT_DRIFT")
    print("V57_V433_QD_SCHEDULER_ENGINE_V1_SELF_CHECK=PASS|PARENT_POOL=ALL_ACTIVE_ELIGIBLE|MIN_PASSED_FOLDS=1|RANK=REPEATED_PARETO_FRONTS|HALVING=FLOOR_MIN_ONE|OFFSPRING=4_X2|COMPLETE_REPLAY_ONLY=YES|NOVELTY_NOT_ACCEPTANCE_GATE=YES|SIDE_INDEPENDENT=YES|HOLDOUT=UNREAD|ORDERS=DISABLED")

if __name__=="__main__":
    self_check()
