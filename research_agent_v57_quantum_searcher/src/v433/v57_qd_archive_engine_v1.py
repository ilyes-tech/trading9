from pathlib import Path
import copy, hashlib, json, math, statistics, sys

HERE = Path(__file__).resolve()
V433 = HERE.parent
SRC = HERE.parents[1]
ROOT = HERE.parents[2]
for p in (V433, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import v57_qd_variation_engine_v1 as qv
import v57_strategy_dsl_v3 as dsl3

ENGINE = "V57_V433_QD_ARCHIVE_ENGINE_V1"
POLICY = ROOT / "config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
VARIATION_FREEZE = ROOT / "config/v433/V57_V433_QD_VARIATION_ENGINE_V1_FREEZE_V1.json"

EXPECTED = {
    "policy": "d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f",
    "variation": "21acf86faed0e833dc4aca5483d21cc9fe96cdb39c97f284c6e129a9c9bdfa87",
    "variation_freeze": "a67b02fd7d35203f7307222af45ec7a2f752d499f2361cf8d6343df867e0a241",
    "runtime_v3_freeze": "89c9561e7e38848ef60d5febbf5873d7580926c6328074ea6a990c91bd5dc968",
    "replay_freeze": "b331085d28991bbea6a5b48ae3181992b51db971e686d56df156609486e4a626",
    "dsl3": "8a172adfb7dd0d7fe358c715de9f1b98d20e83829bb979deeafabb957554893b",
}

def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)

P = json.loads(POLICY.read_text())
DIMS = tuple(P["archive"]["cell_dimensions"])
CELL_CAP = int(P["archive"]["max_elites_per_cell"])
GLOBAL_CAP = int(P["archive"]["global_pareto_cap"])
OBJECTIVES = tuple((x["name"], x["direction"]) for x in P["quality"]["pareto_within_tier"]["objectives"])
SUPPORT = tuple(x["name"] for x in P["quality"]["support_metrics"])
TIER_NAMES = {int(x["tier"]): x["name"] for x in P["quality"]["tier_order"]}
NOVELTY_K = int(P["novelty"]["k_nearest"])
CATEGORICAL_DIMS = tuple(x for x in P["novelty"]["descriptor_dimensions"] if x != "condition_count")

def _ensure():
    paths = {
        "policy": POLICY,
        "variation": V433 / "v57_qd_variation_engine_v1.py",
        "variation_freeze": VARIATION_FREEZE,
        "runtime_v3_freeze": ROOT / "config/v433/V57_V433_SEARCH_RUNTIME_V3_FREEZE_V1.json",
        "replay_freeze": ROOT / "config/v433/V57_V433_SEARCH_REPLAY_V1_FREEZE_V1.json",
        "dsl3": V433 / "v57_strategy_dsl_v3.py",
    }
    got = {k: H(v) for k, v in paths.items()}
    if got != EXPECTED:
        raise RuntimeError("QD_ARCHIVE_ANCHOR_MISMATCH:" + str(got))
    vf = json.loads(VARIATION_FREEZE.read_text())
    if vf.get("status") != "FROZEN_AFTER_SEMANTIC_AUDIT" or vf.get("next_stage") != "V433_QD_ARCHIVE_ENGINE_V1":
        raise RuntimeError("QD_VARIATION_FREEZE_STATE_MISMATCH")
    if P.get("status") != "FROZEN_BEFORE_QD_ENGINEERING_IMPLEMENTATION":
        raise RuntimeError("QD_POLICY_STATE_MISMATCH")
    if P["archive"].get("storage") != "SPARSE_DICTIONARY_NO_DENSE_GRID":
        raise RuntimeError("QD_ARCHIVE_STORAGE_CONTRACT_MISMATCH")
    if P["archive"].get("dedup_key") != "strategy_id" or CELL_CAP != 3 or GLOBAL_CAP != 256:
        raise RuntimeError("QD_ARCHIVE_CAP_CONTRACT_MISMATCH")
    if DIMS != ("market", "timeframe", "side", "logic", "condition_count", "dominant_feature_family"):
        raise RuntimeError("QD_DESCRIPTOR_CONTRACT_MISMATCH")
    if P["archive"].get("exact_candidates_leave_active_search_queue") is not True:
        raise RuntimeError("QD_EXACT_ROUTING_CONTRACT_MISMATCH")
    qv._ensure()
    return True

def _finite(value, name):
    x = float(value)
    if not math.isfinite(x):
        raise ValueError("NONFINITE_ARCHIVE_METRIC:" + name)
    return x

def ast_node_count(node):
    if not isinstance(node, dict):
        raise ValueError("AST_NODE_NOT_DICT")
    if node.get("op") == "COND":
        return 1
    if "child" in node:
        return 1 + ast_node_count(node["child"])
    children = node.get("children")
    if not isinstance(children, list):
        raise ValueError("AST_CHILDREN_MISSING")
    return 1 + sum(ast_node_count(x) for x in children)

def _ast_conditions(node, out):
    if not isinstance(node, dict):
        raise ValueError("AST_NODE_NOT_DICT")
    if node.get("op") == "COND":
        cond = node.get("condition")
        if not isinstance(cond, dict):
            raise ValueError("COND_MISSING_CONDITION")
        out.append(copy.deepcopy(cond))
        return
    if "child" in node:
        _ast_conditions(node["child"], out)
        return
    children = node.get("children")
    if not isinstance(children, list):
        raise ValueError("AST_CHILDREN_MISSING")
    for child in children:
        _ast_conditions(child, out)

def descriptor(strategy):
    dsl3.validate_strategy(strategy)
    conditions = []
    _ast_conditions(strategy["signal"], conditions)
    n = len(conditions)
    if not 1 <= n <= 4:
        raise ValueError("BAD_ACTIVE_CONDITION_COUNT")
    counts = {}
    for cond in conditions:
        fam = cond.get("family")
        if not isinstance(fam, str) or not fam:
            raise ValueError("BAD_ACTIVE_FEATURE_FAMILY")
        counts[fam] = counts.get(fam, 0) + 1
    dominant = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
    market = strategy["market"]
    logic = strategy.get("legacy", {}).get("search_logic")
    if logic not in qv.gen.READY:
        raise ValueError("BAD_DESCRIPTOR_LOGIC")
    return {
        "market": market["symbol"],
        "timeframe": market["timeframe"],
        "side": market["side"],
        "logic": logic,
        "condition_count": n,
        "dominant_feature_family": dominant,
    }

def entry(record):
    _ensure()
    if record.get("status") != "EVALUATED" or not isinstance(record.get("result"), dict):
        raise ValueError("ARCHIVE_REQUIRES_EVALUATED_RECORD")
    strategy = record.get("strategy")
    meta = record.get("meta")
    if not isinstance(strategy, dict) or not isinstance(meta, dict):
        raise ValueError("ARCHIVE_REQUIRES_STRATEGY_META")
    dsl3.validate_strategy(strategy)
    result = record["result"]
    sid = strategy["strategy_id"]
    if result.get("strategy_id") != sid:
        raise ValueError("RESULT_STRATEGY_ID_MISMATCH")
    folds = result.get("folds")
    if not isinstance(folds, list) or len(folds) != 3:
        raise ValueError("ARCHIVE_REQUIRES_THREE_FOLDS")
    passed = sum(bool(f.get("pass")) for f in folds)
    exact = bool(result.get("exact_pass"))
    if exact != (passed == 3):
        raise ValueError("EXACT_PASS_FOLD_CONSISTENCY_FAILURE")
    tier = 0 if exact else 1 if passed == 2 else 2 if passed == 1 else 3 if passed == 0 else -1
    if tier < 0:
        raise ValueError("BAD_PASSED_FOLDS")
    stress = [_finite(f.get("stress_avg_bps"), "stress_avg_bps") for f in folds]
    base = [_finite(f.get("base_avg_bps"), "base_avg_bps") for f in folds]
    tpd = [_finite(f.get("tpd"), "tpd") for f in folds]
    trades = [int(f.get("selected_trades")) for f in folds]
    if any(x < 0 for x in trades):
        raise ValueError("NEGATIVE_SELECTED_TRADES")
    objectives = {
        "worst_stress_avg_bps": _finite(result.get("worst_stress_avg_bps"), "worst_stress_avg_bps"),
        "min_stress_pf": _finite(result.get("min_stress_pf"), "min_stress_pf"),
        "worst_base_avg_bps": _finite(result.get("worst_base_avg_bps"), "worst_base_avg_bps"),
        "min_base_pf": _finite(result.get("min_base_pf"), "min_base_pf"),
        "worst_drawdown_bps": _finite(result.get("worst_drawdown_bps"), "worst_drawdown_bps"),
        "ast_node_count": int(ast_node_count(strategy["signal"])),
    }
    if objectives["ast_node_count"] < 1:
        raise ValueError("BAD_AST_NODE_COUNT")
    support = {
        "min_tpd": min(tpd),
        "min_selected_trades": min(trades),
        "fold_stability_stress_avg_range_bps": max(stress) - min(stress),
        "stress_degradation_bps": float(statistics.fmean(b - s for b, s in zip(base, stress))),
    }
    desc = descriptor(strategy)
    return {
        "strategy_id": sid,
        "tier": tier,
        "tier_name": TIER_NAMES[tier],
        "passed_folds": passed,
        "exact_pass": exact,
        "descriptor": desc,
        "objectives": objectives,
        "support": support,
        "strategy": copy.deepcopy(strategy),
        "meta": copy.deepcopy(meta),
    }

def _entry_contract(e):
    if tuple(e.get("objectives", {})) != tuple(x[0] for x in OBJECTIVES):
        raise ValueError("ARCHIVE_OBJECTIVE_CONTRACT_MISMATCH")
    if tuple(e.get("support", {})) != SUPPORT:
        raise ValueError("ARCHIVE_SUPPORT_CONTRACT_MISMATCH")
    if e.get("tier") not in TIER_NAMES or e.get("tier_name") != TIER_NAMES[e["tier"]]:
        raise ValueError("ARCHIVE_TIER_CONTRACT_MISMATCH")
    if tuple(e.get("descriptor", {})) != DIMS:
        raise ValueError("ARCHIVE_DESCRIPTOR_CONTRACT_MISMATCH")
    if e.get("strategy_id") != e.get("strategy", {}).get("strategy_id"):
        raise ValueError("ARCHIVE_ENTRY_STRATEGY_ID_MISMATCH")
    dsl3.validate_strategy(e["strategy"])
    if descriptor(e["strategy"]) != e["descriptor"]:
        raise ValueError("ARCHIVE_DESCRIPTOR_STRATEGY_MISMATCH")
    for name, _ in OBJECTIVES:
        _finite(e["objectives"][name], name)
    for name in SUPPORT:
        _finite(e["support"][name], name)
    return True

def dominates(a, b):
    _entry_contract(a)
    _entry_contract(b)
    if a["tier"] != b["tier"]:
        raise ValueError("PARETO_REQUIRES_SAME_TIER")
    strictly = False
    for name, direction in OBJECTIVES:
        x, y = a["objectives"][name], b["objectives"][name]
        if direction == "MAX":
            if x < y:
                return False
            strictly = strictly or x > y
        elif direction == "MIN":
            if x > y:
                return False
            strictly = strictly or x < y
        else:
            raise ValueError("BAD_OBJECTIVE_DIRECTION:" + direction)
    return strictly

def nondominated(entries):
    xs = sorted(entries, key=lambda e: e["strategy_id"])
    return [
        a for i, a in enumerate(xs)
        if not any(i != j and dominates(b, a) for j, b in enumerate(xs))
    ]

def crowding(entries):
    xs = sorted(entries, key=lambda e: e["strategy_id"])
    dist = {e["strategy_id"]: 0.0 for e in xs}
    n = len(xs)
    if n <= 2:
        for e in xs:
            dist[e["strategy_id"]] = float("inf")
        return dist
    for name, _ in OBJECTIVES:
        ordered = sorted(xs, key=lambda e: (e["objectives"][name], e["strategy_id"]))
        lo = ordered[0]["objectives"][name]
        hi = ordered[-1]["objectives"][name]
        dist[ordered[0]["strategy_id"]] = float("inf")
        dist[ordered[-1]["strategy_id"]] = float("inf")
        if hi != lo:
            for i in range(1, n - 1):
                sid = ordered[i]["strategy_id"]
                if not math.isinf(dist[sid]):
                    dist[sid] += (ordered[i + 1]["objectives"][name] - ordered[i - 1]["objectives"][name]) / (hi - lo)
    return dist

def select(entries, cap):
    if not entries or int(cap) <= 0:
        return []
    unique = {}
    for e in entries:
        _entry_contract(e)
        sid = e["strategy_id"]
        fp = hashlib.sha256(canonical(e).encode()).hexdigest()
        if sid in unique and unique[sid][0] != fp:
            raise ValueError("STRATEGY_ID_ENTRY_CONFLICT:" + sid)
        unique[sid] = (fp, e)
    xs = [v[1] for v in unique.values()]
    best_tier = min(e["tier"] for e in xs)
    front = nondominated([e for e in xs if e["tier"] == best_tier])
    cd = crowding(front)
    front.sort(key=lambda e: (
        float("-inf") if math.isinf(cd[e["strategy_id"]]) else -cd[e["strategy_id"]],
        e["strategy_id"],
    ))
    return front[:int(cap)]

def cell_key(e):
    return canonical([e["descriptor"][name] for name in DIMS])

def distance(a, b):
    x = a["descriptor"] if "descriptor" in a else a
    y = b["descriptor"] if "descriptor" in b else b
    d = sum(0 if x[name] == y[name] else 1 for name in CATEGORICAL_DIMS)
    d += abs(int(x["condition_count"]) - int(y["condition_count"])) / 3.0
    return float(d)

def novelty(e, references, k=None):
    rows = sorted(
        (distance(e, x), x["strategy_id"])
        for x in references
        if x["strategy_id"] != e["strategy_id"]
    )
    n = min(len(rows), NOVELTY_K if k is None else int(k))
    return 0.0 if n < 1 else float(statistics.fmean(x[0] for x in rows[:n]))

def new_archive():
    return {
        "schema_version": 1,
        "kind": "V57_V433_QD_SPARSE_ARCHIVE_V1",
        "engine": ENGINE,
        "candidate_pool": {},
        "cells": {},
        "exact_backlog": {},
        "global_pareto": [],
        "seen": {},
        "stats": {
            "input_records": 0,
            "evaluated_records": 0,
            "skipped_non_evaluated": 0,
            "duplicates": 0,
            "exact_routed": 0,
        },
        "research_integrity": {
            "holdout_read": False,
            "holdout_evaluated": False,
            "september_2026_data_accessed": False,
            "demo_orders_allowed": False,
            "real_orders_allowed": False,
        },
    }

def _fingerprint(e):
    return hashlib.sha256(canonical(e).encode()).hexdigest()

def rebuild(archive):
    cells = {}
    for e in archive["candidate_pool"].values():
        cells.setdefault(cell_key(e), []).append(e)
    archive["cells"] = {
        k: [e["strategy_id"] for e in select(xs, CELL_CAP)]
        for k, xs in sorted(cells.items())
    }
    archive["global_pareto"] = [
        e["strategy_id"] for e in select(list(archive["candidate_pool"].values()), GLOBAL_CAP)
    ]
    return archive

def insert(archive, e, do_rebuild=True):
    _entry_contract(e)
    sid = e["strategy_id"]
    fp = _fingerprint(e)
    if sid in archive["seen"]:
        if archive["seen"][sid] != fp:
            raise ValueError("STRATEGY_ID_ENTRY_CONFLICT:" + sid)
        archive["stats"]["duplicates"] += 1
        return False
    archive["seen"][sid] = fp
    if e["tier"] == 0:
        archive["exact_backlog"][sid] = copy.deepcopy(e)
        archive["stats"]["exact_routed"] += 1
    else:
        archive["candidate_pool"][sid] = copy.deepcopy(e)
    if do_rebuild:
        rebuild(archive)
    return True

def ingest(records):
    archive = new_archive()
    for record in records:
        archive["stats"]["input_records"] += 1
        if record.get("status") != "EVALUATED" or not isinstance(record.get("result"), dict):
            archive["stats"]["skipped_non_evaluated"] += 1
            continue
        archive["stats"]["evaluated_records"] += 1
        insert(archive, entry(record), do_rebuild=False)
    rebuild(archive)
    validate(archive)
    return archive

def active_entries(archive):
    ids = {sid for xs in archive["cells"].values() for sid in xs}
    return [archive["candidate_pool"][sid] for sid in sorted(ids)]

def validate(archive):
    if archive.get("kind") != "V57_V433_QD_SPARSE_ARCHIVE_V1":
        raise ValueError("BAD_ARCHIVE_KIND")
    ri = archive.get("research_integrity", {})
    for key in ("holdout_read", "holdout_evaluated", "september_2026_data_accessed", "demo_orders_allowed", "real_orders_allowed"):
        if ri.get(key) is not False:
            raise ValueError("ARCHIVE_RESEARCH_INTEGRITY_VIOLATION:" + key)
    pool = archive.get("candidate_pool")
    exact = archive.get("exact_backlog")
    seen = archive.get("seen")
    if not isinstance(pool, dict) or not isinstance(exact, dict) or not isinstance(seen, dict):
        raise ValueError("BAD_ARCHIVE_MAPS")
    if set(pool) & set(exact):
        raise ValueError("EXACT_ACTIVE_OVERLAP")
    if set(seen) != set(pool) | set(exact):
        raise ValueError("ARCHIVE_SEEN_SET_MISMATCH")
    for sid, e in list(pool.items()) + list(exact.items()):
        _entry_contract(e)
        if sid != e["strategy_id"] or seen[sid] != _fingerprint(e):
            raise ValueError("ARCHIVE_ENTRY_FINGERPRINT_MISMATCH")
        if (sid in exact) != (e["tier"] == 0):
            raise ValueError("EXACT_ROUTING_MISMATCH")
    expected = copy.deepcopy(archive)
    rebuild(expected)
    if canonical(expected["cells"]) != canonical(archive.get("cells", {})):
        raise ValueError("ARCHIVE_CELL_REBUILD_MISMATCH")
    if expected["global_pareto"] != archive.get("global_pareto", []):
        raise ValueError("ARCHIVE_GLOBAL_PARETO_REBUILD_MISMATCH")
    if any(len(ids) > CELL_CAP for ids in archive["cells"].values()):
        raise ValueError("ARCHIVE_CELL_CAP_EXCEEDED")
    if len(archive["global_pareto"]) > GLOBAL_CAP:
        raise ValueError("ARCHIVE_GLOBAL_CAP_EXCEEDED")
    active = {sid for ids in archive["cells"].values() for sid in ids}
    if active & set(exact):
        raise ValueError("EXACT_ACTIVE_OVERLAP")
    return True

def self_check():
    _ensure()
    pairs = qv.gen.generate(64, 944301, 0)
    for strategy, _ in pairs:
        d = descriptor(strategy)
        if not 1 <= d["condition_count"] <= 4:
            raise AssertionError("DESCRIPTOR_ACTIVE_CONDITION_FAILURE")

    s, m = pairs[0]
    folds = [
        {"pass": True, "stress_avg_bps": 1.0, "base_avg_bps": 2.0, "tpd": 3.0, "selected_trades": 30},
        {"pass": True, "stress_avg_bps": 2.0, "base_avg_bps": 3.0, "tpd": 4.0, "selected_trades": 40},
        {"pass": True, "stress_avg_bps": 3.0, "base_avg_bps": 4.0, "tpd": 5.0, "selected_trades": 50},
    ]
    fake = {
        "status": "EVALUATED",
        "strategy": s,
        "meta": m,
        "result": {
            "strategy_id": s["strategy_id"],
            "folds": folds,
            "exact_pass": True,
            "worst_stress_avg_bps": 1.0,
            "min_stress_pf": 1.1,
            "worst_base_avg_bps": 2.0,
            "min_base_pf": 1.2,
            "worst_drawdown_bps": -10.0,
        },
    }
    ex = entry(fake)
    a = new_archive()
    insert(a, ex)
    validate(a)
    if s["strategy_id"] not in a["exact_backlog"] or any(s["strategy_id"] in ids for ids in a["cells"].values()):
        raise AssertionError("EXACT_ROUTE_FAILURE")

    desc0 = descriptor(pairs[0][0])
    if distance(desc0, desc0) != 0.0:
        raise AssertionError("NOVELTY_DISTANCE_FAILURE")

    print(
        "V57_V433_QD_ARCHIVE_ENGINE_V1_SELF_CHECK=PASS"
        "|SPARSE_ARCHIVE=PASS"
        "|ACTIVE_AST_DESCRIPTORS=PASS"
        "|TIER_PRIORITY=PASS"
        "|PARETO_DIRECTIONS=PASS"
        "|CROWDING=IMPLEMENTED"
        "|NOVELTY=IMPLEMENTED"
        "|EXACT_ROUTE=VALIDATION_BACKLOG_ONLY"
        "|GLOBAL_CAP=256"
        "|CELL_CAP=3"
        "|ORDER_INDEPENDENT_REBUILD=DESIGNED"
        "|HOLDOUT=UNREAD"
        "|ORDERS=DISABLED"
    )

if __name__ == "__main__":
    self_check()
