from pathlib import Path
import copy, hashlib, json, math, sys

HERE = Path(__file__).resolve()
V433 = HERE.parent
SRC = HERE.parents[1]
ROOT = HERE.parents[2]
for p in (V433, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v57_qd_scheduler_engine_v1 as scheduler
import v57_qd_archive_engine_v1 as archive
import v57_qd_variation_engine_v1 as variation
import v57_search_runtime_v3 as runtime
import v57_search_replay_v1 as replay
import v57_fold_signal_adapter_v2 as adapter2
import v57_strategy_signal_engine_v5 as signal5

ENGINE = "V57_V433_QD_ORCHESTRATOR_ENGINE_V1"
EXPECTED = {
    "policy": ("config/v433/V57_V433_QD_SEARCH_POLICY_V1.json", "d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f"),
    "archive_freeze": ("config/v433/V57_V433_QD_ARCHIVE_ENGINE_V1_FREEZE_V1.json", "0bfa5c7ab8c84e96ab09a3e3bfda860b0440daf2af6b1c9a63b28b588522535f"),
    "variation_freeze": ("config/v433/V57_V433_QD_VARIATION_ENGINE_V1_FREEZE_V1.json", "a67b02fd7d35203f7307222af45ec7a2f752d499f2361cf8d6343df867e0a241"),
    "runtime_freeze": ("config/v433/V57_V433_SEARCH_RUNTIME_V3_FREEZE_V1.json", "89c9561e7e38848ef60d5febbf5873d7580926c6328074ea6a990c91bd5dc968"),
    "replay_freeze": ("config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json", "b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626"),
    "scheduler_freeze": ("config/v433/V57_V433_QD_SCHEDULER_ENGINE_V1_FREEZE_V1.json", "f23c4916de2555f9e28d7167061638743b09b7bd398a117239651686fce44535"),
}
P = json.loads((ROOT / EXPECTED["policy"][0]).read_text())
B = P["budget"]
BOOTSTRAP = B["bootstrap"]
CYCLE = B["cycle"]
CHECKPOINT_EVERY = int(B["checkpoint_every_candidates"])

def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _ensure():
    for name, (rel, sha) in EXPECTED.items():
        p = ROOT / rel
        got = H(p)
        if got != sha:
            raise RuntimeError("ORCHESTRATOR_ANCHOR_MISMATCH:%s:%s" % (name, got))
    sf = json.loads((ROOT / EXPECTED["scheduler_freeze"][0]).read_text())
    if sf.get("status") != "FROZEN_AFTER_SEMANTIC_AUDIT" or sf.get("next_stage") != "V433_QD_ORCHESTRATOR_ENGINE_V1":
        raise RuntimeError("SCHEDULER_FREEZE_STATE_MISMATCH")
    if BOOTSTRAP["candidate_budget"] != 2048 or BOOTSTRAP["batch_size"] != 128 or BOOTSTRAP["seed"] != 943301:
        raise RuntimeError("BOOTSTRAP_POLICY_DRIFT")
    if CYCLE["total_budget"] != 4096 or CYCLE["exploration_budget"] != 1434 or CYCLE["exploitation_budget"] != 2662:
        raise RuntimeError("CYCLE_POLICY_DRIFT")
    if CYCLE["batch_size"] != 128 or CYCLE["workers"] != 3 or CYCLE["seed_base"] != 943310:
        raise RuntimeError("CYCLE_EXECUTION_POLICY_DRIFT")
    if CHECKPOINT_EVERY != 128:
        raise RuntimeError("CHECKPOINT_POLICY_DRIFT")
    if BOOTSTRAP["audit_184_reused_as_search_seed"] is not False:
        raise RuntimeError("AUDIT_184_REUSE_POLICY_DRIFT")
    scheduler._ensure()
    archive._ensure()
    variation._ensure()
    runtime._ensure()
    return True

def orchestrator_contract():
    return {
        "engine": ENGINE,
        "bootstrap_budget": int(BOOTSTRAP["candidate_budget"]),
        "bootstrap_batch_size": int(BOOTSTRAP["batch_size"]),
        "bootstrap_seed": int(BOOTSTRAP["seed"]),
        "cycle_total_budget": int(CYCLE["total_budget"]),
        "cycle_exploration_budget": int(CYCLE["exploration_budget"]),
        "cycle_exploitation_budget": int(CYCLE["exploitation_budget"]),
        "cycle_batch_size": int(CYCLE["batch_size"]),
        "cycle_workers": int(CYCLE["workers"]),
        "cycle_seed_base": int(CYCLE["seed_base"]),
        "checkpoint_every_candidates": CHECKPOINT_EVERY,
        "duplicate_key": "strategy_id",
        "prefilter": "FROZEN_RUNTIME_V3_NECESSARY_SIGNAL_DENSITY_ONLY",
        "replay_unit": "COMPLETE_CANDIDATE_THREE_FOLD_REPLAY",
        "exact_destination": "ARCHIVE_EXACT_BACKLOG_ONLY",
        "holdout_read": False,
        "orders_allowed": False,
    }

def exploration_items(count, seed, start=0):
    _ensure()
    n = int(count)
    st = int(start)
    if n < 0 or st < 0:
        raise ValueError("BAD_EXPLORATION_RANGE")
    pairs = variation.gen.generate(n, int(seed), st)
    items = []
    seen = set()
    for strategy, meta in pairs:
        sid = strategy["strategy_id"]
        if sid in seen:
            raise RuntimeError("EXPLORATION_DUPLICATE_STRATEGY_ID:" + sid)
        seen.add(sid)
        if strategy["execution"]["orders_allowed"] is not False:
            raise RuntimeError("EXPLORATION_ORDERS_ALLOWED")
        if strategy["research_integrity"]["holdout_read"] is not False:
            raise RuntimeError("EXPLORATION_HOLDOUT_READ")
        items.append({"strategy": strategy, "meta": meta, "parent_strategy_id": None,
                      "lineage": {"kind": "PURE_EXPLORATION", "seed": int(seed), "index": st + len(items)}})
    return items

def _donor_pairs(parent_entry, active_entries):
    market = parent_entry["descriptor"]["market"]
    rows = [e for e in active_entries if e["strategy_id"] != parent_entry["strategy_id"] and e["descriptor"]["market"] == market]
    rows.sort(key=lambda e: e["strategy_id"])
    return [(e["strategy"], e["meta"]) for e in rows]

def _unique_offspring(parent_entry, active_entries, count, seed, forbidden):
    need = int(count)
    if need < 0:
        raise ValueError("NEGATIVE_OFFSPRING_COUNT")
    out = []
    blocked = set(forbidden)
    blocked.add(parent_entry["strategy_id"])
    donors = _donor_pairs(parent_entry, active_entries)
    attempt = 0
    while len(out) < need and attempt < 64:
        missing = need - len(out)
        sub_seed = int(seed) + attempt * 10000019
        batch = variation.generate_offspring(parent_entry["strategy"], parent_entry["meta"], missing, sub_seed, donors)
        for strategy, meta, lineage in batch:
            sid = strategy["strategy_id"]
            if sid in blocked:
                continue
            blocked.add(sid)
            out.append({"strategy": strategy, "meta": meta, "parent_strategy_id": parent_entry["strategy_id"],
                        "lineage": {"kind": "QD_EXPLOITATION", "parent_strategy_id": parent_entry["strategy_id"],
                                    "generation_seed": sub_seed, **copy.deepcopy(lineage)}})
        attempt += 1
    if len(out) != need:
        raise RuntimeError("INSUFFICIENT_GLOBAL_UNIQUE_OFFSPRING:%d/%d" % (len(out), need))
    return out

def exploitation_items(ar, parent_ids, round_index, remaining_budget, seed_base, seen_strategy_ids=()):
    _ensure()
    active = archive.active_entries(ar)
    amap = {e["strategy_id"]: e for e in active}
    parents = list(dict.fromkeys(str(x) for x in parent_ids))
    cap = scheduler.round_capacity(len(parents), int(remaining_budget), int(round_index))
    parents = parents[:cap]
    per = scheduler.offspring_per_parent(int(round_index))
    forbidden = set(str(x) for x in seen_strategy_ids)
    forbidden.update(ar.get("seen", {}).keys())
    items = []
    for rank, pid in enumerate(parents):
        if pid not in amap:
            raise ValueError("PARENT_NOT_ACTIVE:" + pid)
        if int(amap[pid]["passed_folds"]) < int(P["scheduler"]["parent_eligibility"]["minimum_passed_folds"]):
            raise ValueError("PARENT_NOT_ELIGIBLE:" + pid)
        seed = int(seed_base) + int(round_index) * 1000003 + rank * 1009
        kids = _unique_offspring(amap[pid], active, per, seed, forbidden)
        for item in kids:
            forbidden.add(item["strategy"]["strategy_id"])
            items.append(item)
    return items

def _record(phase, candidate_index, item, status, prefilter, result, error):
    return {"schema_version": 1, "kind": "V57_V433_QD_ORCHESTRATOR_RECORD_V1", "engine": ENGINE,
            "phase": str(phase), "candidate_index": int(candidate_index), "status": status,
            "parent_strategy_id": item.get("parent_strategy_id"), "strategy": item["strategy"],
            "meta": item["meta"], "lineage": copy.deepcopy(item.get("lineage")), "prefilter": prefilter,
            "result": result, "error": error, "research_integrity": {"holdout_read": False,
            "holdout_evaluated": False, "september_2026_data_accessed": False,
            "demo_orders_allowed": False, "real_orders_allowed": False}}

def evaluate_item(item, phase, candidate_index, contexts=None, stores=None):
    _ensure()
    contexts = {} if contexts is None else contexts
    stores = {} if stores is None else stores
    strategy = item["strategy"]
    meta = item["meta"]
    key = (meta["market"], meta["timeframe"])
    if key not in contexts:
        contexts[key] = adapter2.prepare_context(*key)
    if key not in stores:
        stores[key] = signal5.bitcache.MaskBitsetCache()
    try:
        pref = runtime.signal_prefilter(contexts[key], strategy, stores[key])
        if not pref["pass"]:
            return _record(phase, candidate_index, item, "PREFILTER_REJECT", pref, None, None)
        result = replay.evaluate_strategy(contexts[key], strategy, stores[key])
        folds = result.get("folds")
        if not isinstance(folds, list) or len(folds) != 3:
            raise RuntimeError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
        return _record(phase, candidate_index, item, "EVALUATED", pref, result, None)
    except ValueError as e:
        if str(e) == "NO_FINITE_TRAIN_VALUES":
            pref = {"pass": False, "reason": "NO_FINITE_TRAIN_VALUES_FAIL_CLOSED",
                    "source_exception": "ValueError:NO_FINITE_TRAIN_VALUES", "folds": []}
            return _record(phase, candidate_index, item, "PREFILTER_REJECT", pref, None, None)
        return _record(phase, candidate_index, item, "ERROR", None, None, type(e).__name__ + ":" + str(e))
    except Exception as e:
        return _record(phase, candidate_index, item, "ERROR", None, None, type(e).__name__ + ":" + str(e))

def evaluate_items(items, phase, start_index=0):
    contexts, stores, records = {}, {}, []
    for i, item in enumerate(items):
        records.append(evaluate_item(item, phase, int(start_index) + i, contexts, stores))
    return records

def apply_records(ar, records):
    archive.validate(ar)
    added = 0
    for record in records:
        if record.get("status") == "EVALUATED" and isinstance(record.get("result"), dict):
            folds = record["result"].get("folds")
            if not isinstance(folds, list) or len(folds) != 3:
                raise ValueError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
            if archive.insert(ar, archive.entry(record), do_rebuild=False):
                added += 1
    archive.rebuild(ar)
    archive.validate(ar)
    return added

def self_check():
    _ensure()
    c = orchestrator_contract()
    if c["bootstrap_budget"] != 2048 or c["cycle_total_budget"] != 4096:
        raise AssertionError("BUDGET_CONTRACT_FAILURE")
    if c["cycle_exploration_budget"] + c["cycle_exploitation_budget"] != c["cycle_total_budget"]:
        raise AssertionError("CYCLE_SPLIT_FAILURE")
    xs = exploration_items(48, 950001, 0)
    ids = [x["strategy"]["strategy_id"] for x in xs]
    if len(ids) != len(set(ids)) or len(xs) != 48:
        raise AssertionError("EXPLORATION_DEDUP_FAILURE")
    if not all(x["parent_strategy_id"] is None for x in xs):
        raise AssertionError("EXPLORATION_PARENT_LEAK")
    if scheduler.survivor_count(6) != 3 or scheduler.offspring_per_parent(2) != 16:
        raise AssertionError("SCHEDULER_CONTRACT_FAILURE")
    if c["holdout_read"] is not False or c["orders_allowed"] is not False:
        raise AssertionError("SAFETY_CONTRACT_FAILURE")
    print("V57_V433_QD_ORCHESTRATOR_ENGINE_V1_SELF_CHECK=PASS|BOOTSTRAP=2048|CYCLE=4096|EXPLORE=1434|EXPLOIT=2662|BATCH=128|WORKERS=3|DUPLICATE_KEY=STRATEGY_ID|PREFILTER=FROZEN_RUNTIME_V3|REPLAY=COMPLETE_3_FOLD_ONLY|EXACT=BACKLOG_ONLY|HOLDOUT=UNREAD|ORDERS=DISABLED")

if __name__ == "__main__":
    self_check()
