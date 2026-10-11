import copy
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import v57_qd_archive_engine_v1 as archive
import v57_qd_orchestrator_engine_v1 as orchestrator
import v57_qd_checkpoint_resume_engine_v1 as checkpoint

ENGINE = "V57_V433_QD_BOOTSTRAP_RUNNER_V1"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]

POLICY_PATH = ROOT / "config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
ARCHIVE_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_ARCHIVE_ENGINE_V1_FREEZE_V1.json"
ORCHESTRATOR_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_ORCHESTRATOR_ENGINE_V1_FREEZE_V1.json"
CHECKPOINT_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_CHECKPOINT_RESUME_ENGINE_V1_FREEZE_V1.json"
STACK_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_ENGINEERING_STACK_FREEZE_V1.json"

EXPECTED = {
    str(POLICY_PATH): "d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f",
    str(ARCHIVE_FREEZE_PATH): "0bfa5c7ab8c84e96ab09a3e3bfda860b0440daf2af6b1c9a63b28b588522535f",
    str(ORCHESTRATOR_FREEZE_PATH): "5b29ffe897fbd421c3295ce989b7731c5a5e01d32c8a5b58e22c5681e80ff21b",
    str(CHECKPOINT_FREEZE_PATH): "589d73501b52fe79fe18928f71fc24f9d87f766c62ec17ec267c11d545bb663d",
    str(STACK_FREEZE_PATH): "1ac18a3582416465e6d98765012310830b59ecad5cff7d69b5f8098536e52759",
}

BOOTSTRAP_BUDGET = 2048
BATCH_SIZE = 128
SEED = 943301
EXPECTED_SEQUENCE_SHA256 = "5b915130f3282a8a13297ea51a38361b76309f6264a160b554b3e15544decbd2"
RI_KEYS = (
    "holdout_read",
    "holdout_evaluated",
    "september_2026_data_accessed",
    "demo_orders_allowed",
    "real_orders_allowed",
)


def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json_pack(obj):
    if isinstance(obj, float) and not math.isfinite(obj):
        tag = "nan" if math.isnan(obj) else ("inf" if obj > 0 else "-inf")
        return {"__v433_nonfinite_float_v1__": tag}
    if isinstance(obj, dict):
        return {k: _json_pack(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_pack(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_pack(v) for v in obj]
    return obj


def _json_unpack(obj):
    if isinstance(obj, dict):
        if set(obj) == {"__v433_nonfinite_float_v1__"}:
            tag = obj["__v433_nonfinite_float_v1__"]
            if tag == "nan":
                return float("nan")
            if tag == "inf":
                return float("inf")
            if tag == "-inf":
                return float("-inf")
            raise ValueError("BAD_NONFINITE_FLOAT_TAG:" + str(tag))
        return {k: _json_unpack(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_unpack(v) for v in obj]
    return obj


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _ensure():
    for path, expected in EXPECTED.items():
        if H(path) != expected:
            raise ValueError("ANCHOR_HASH_MISMATCH:" + path)
    stack = json.loads(STACK_FREEZE_PATH.read_text())
    if stack.get("kind") != "V57_V433_QD_ENGINEERING_STACK_FREEZE_V1":
        raise ValueError("BAD_ENGINEERING_STACK_KIND")
    if stack.get("status") != "FROZEN_AFTER_END_TO_END_ENGINEERING_AUDIT":
        raise ValueError("BAD_ENGINEERING_STACK_STATUS")
    if stack.get("next_stage") != "V433_QD_BOOTSTRAP_2048_EXECUTION_GATE":
        raise ValueError("BAD_ENGINEERING_STACK_NEXT_STAGE")
    deployment = stack.get("deployment", {})
    for key in ("shadow_authorized", "holdout_authorized", "demo_orders_allowed", "real_orders_allowed", "whitelist_created"):
        if deployment.get(key) is not False:
            raise ValueError("DEPLOYMENT_AUTHORIZATION_VIOLATION:" + key)
    cf = json.loads(CHECKPOINT_FREEZE_PATH.read_text())
    component = cf.get("component", {})
    cp = ROOT / component.get("path", "")
    if component.get("sha256") != "eb4d9887a02d65cd1e084a7963df534e98d29cf5f408df5cf19308bf98f10a07":
        raise ValueError("CHECKPOINT_COMPONENT_FREEZE_DRIFT")
    if H(cp) != component["sha256"]:
        raise ValueError("CHECKPOINT_COMPONENT_HASH_DRIFT")
    if BOOTSTRAP_BUDGET != 2048 or BATCH_SIZE != 128 or SEED != 943301:
        raise ValueError("BOOTSTRAP_CONSTANT_DRIFT")
    archive._ensure()
    orchestrator._ensure()
    checkpoint._ensure()
    return True


def runner_contract():
    return {
        "engine": ENGINE,
        "bootstrap_budget": BOOTSTRAP_BUDGET,
        "batch_size": BATCH_SIZE,
        "seed": SEED,
        "start_archive": "archive.new_archive",
        "audit_184_reused_as_search_seed": False,
        "candidate_identity_sequence_sha256": EXPECTED_SEQUENCE_SHA256,
        "record_commit": "APPEND_ONE_CANONICAL_JSONL_RECORD_THEN_FSYNC",
        "checkpoint_every_candidates": 128,
        "resume": "JOURNAL_TAIL_RECONCILIATION_WITHOUT_REEVALUATION",
        "error_semantics": "FAIL_CLOSED_BEFORE_RECORD_COMMIT",
        "prefilter": "FROZEN_RUNTIME_V3",
        "replay_unit": "COMPLETE_CANDIDATE_THREE_FOLD_REPLAY",
        "exact_destination": "ARCHIVE_EXACT_BACKLOG_ONLY",
        "holdout_read": False,
        "orders_allowed": False,
    }


def _record_line(record):
    return (canonical(_json_pack(record)) + "\n").encode()


def _repair_and_read_journal(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        return [], b""
    data = p.read_bytes()
    if data and not data.endswith(b"\n"):
        cut = data.rfind(b"\n") + 1
        with p.open("r+b") as f:
            f.truncate(cut)
            f.flush()
            os.fsync(f.fileno())
        data = data[:cut]
    records = []
    for i, line in enumerate(data.splitlines()):
        if not line:
            raise ValueError("EMPTY_JOURNAL_LINE:%d" % i)
        record = _json_unpack(json.loads(line))
        if record.get("phase") != "BOOTSTRAP" or record.get("candidate_index") != i:
            raise ValueError("JOURNAL_SEQUENCE_MISMATCH:%d" % i)
        if record.get("status") not in ("EVALUATED", "PREFILTER_REJECT"):
            raise ValueError("JOURNAL_BAD_STATUS:%d:%s" % (i, record.get("status")))
        if record.get("error") is not None:
            raise ValueError("JOURNAL_ERROR_RECORD:%d" % i)
        ri = record.get("research_integrity", {})
        if any(ri.get(k) is not False for k in RI_KEYS):
            raise ValueError("JOURNAL_RESEARCH_INTEGRITY_VIOLATION:%d" % i)
        records.append(record)
    return records, data


def _append_record(path, record):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existed = p.exists()
    line = _record_line(record)
    with p.open("ab") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    if not existed:
        try:
            dfd = os.open(str(p.parent), os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except (AttributeError, OSError):
            pass
    return line


def _verify_records_against_generator(records):
    n = len(records)
    if n > BOOTSTRAP_BUDGET:
        raise ValueError("JOURNAL_OVER_BOOTSTRAP_BUDGET")
    if n == 0:
        return []
    items = orchestrator.exploration_items(n, SEED, 0)
    ids = []
    for i, (record, item) in enumerate(zip(records, items)):
        sid = item["strategy"]["strategy_id"]
        if record.get("candidate_index") != i:
            raise ValueError("CANDIDATE_INDEX_DRIFT:%d" % i)
        if record.get("strategy", {}).get("strategy_id") != sid:
            raise ValueError("CANDIDATE_IDENTITY_DRIFT:%d" % i)
        if canonical(record.get("strategy")) != canonical(item["strategy"]):
            raise ValueError("CANDIDATE_STRATEGY_PAYLOAD_DRIFT:%d" % i)
        if canonical(record.get("meta")) != canonical(item["meta"]):
            raise ValueError("CANDIDATE_META_PAYLOAD_DRIFT:%d" % i)
        if record.get("parent_strategy_id") is not None:
            raise ValueError("BOOTSTRAP_PARENT_PRESENT:%d" % i)
        ids.append(sid)
    return ids


def _archive_entry_or_none(record):
    result = record.get("result")
    folds = result.get("folds") if isinstance(result, dict) else None
    if not isinstance(folds, list) or len(folds) != 3:
        raise ValueError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
    try:
        return archive.entry(record)
    except (TypeError, ValueError):
        def bad(v):
            if v is None:
                return True
            try:
                return not math.isfinite(float(v))
            except (TypeError, ValueError):
                return True
        avg_unrankable = any(bad(f.get(k)) for f in folds for k in ("base_avg_bps", "stress_avg_bps"))
        if avg_unrankable and result.get("exact_pass") is False and not any(bool(f.get("pass")) for f in folds):
            return None
        raise


def _apply_record_fast(ar, record):
    ar["stats"]["input_records"] += 1
    if record.get("status") == "PREFILTER_REJECT":
        ar["stats"]["skipped_non_evaluated"] += 1
        return 0
    if record.get("status") != "EVALUATED" or not isinstance(record.get("result"), dict):
        raise ValueError("UNCOMMITTABLE_RECORD_STATUS")
    folds = record["result"].get("folds")
    if not isinstance(folds, list) or len(folds) != 3:
        raise ValueError("PARTIAL_REPLAY_RESULT_FORBIDDEN")
    ar["stats"]["evaluated_records"] += 1
    entry = _archive_entry_or_none(record)
    if entry is None:
        return 0
    return int(archive.insert(ar, entry, do_rebuild=False))


def _checkpoint_state(ar, completed, seen_ids, journal_sha256, checkpoint_path, phase=None):
    archive.rebuild(ar)
    archive.validate(ar)
    final_phase = "COMPLETE" if completed == BOOTSTRAP_BUDGET else "BOOTSTRAP"
    if phase is not None:
        final_phase = str(phase)
    progress = checkpoint.make_progress(
        final_phase,
        completed_candidates=completed,
        bootstrap_next_start=completed,
    )
    state = checkpoint.make_state(
        ar,
        progress,
        seen_strategy_ids=seen_ids,
        journal_records=completed,
        journal_sha256=journal_sha256,
    )
    checkpoint.save_checkpoint(checkpoint_path, state)
    return state


def _new_state(checkpoint_path):
    ar = archive.new_archive()
    archive.validate(ar)
    empty_sha = hashlib.sha256(b"").hexdigest()
    return _checkpoint_state(ar, 0, [], empty_sha, checkpoint_path, "BOOTSTRAP")


def _reconcile(checkpoint_path, journal_path):
    cp = Path(checkpoint_path)
    jp = Path(journal_path)
    records, data = _repair_and_read_journal(jp)
    all_ids = _verify_records_against_generator(records)
    if cp.exists():
        state = checkpoint.load_checkpoint(cp)
    else:
        if records:
            raise ValueError("JOURNAL_EXISTS_WITHOUT_CHECKPOINT")
        state = _new_state(cp)
    progress = state["progress"]
    completed = int(progress["completed_candidates"])
    if completed != int(progress["bootstrap_next_start"]):
        raise ValueError("CHECKPOINT_BOOTSTRAP_CURSOR_MISMATCH")
    if completed != int(state["journal"]["records"]):
        raise ValueError("CHECKPOINT_JOURNAL_COUNT_MISMATCH")
    if completed > len(records):
        raise ValueError("CHECKPOINT_AHEAD_OF_JOURNAL")
    lines = data.splitlines(keepends=True)
    prefix = b"".join(lines[:completed])
    if hashlib.sha256(prefix).hexdigest() != state["journal"]["sha256"]:
        raise ValueError("CHECKPOINT_JOURNAL_PREFIX_HASH_MISMATCH")
    expected_seen = sorted(all_ids[:completed])
    if state["seen_strategy_ids"] != expected_seen:
        raise ValueError("CHECKPOINT_SEEN_IDS_MISMATCH")
    if completed == BOOTSTRAP_BUDGET and progress["phase"] != "COMPLETE":
        raise ValueError("COMPLETE_PHASE_MISMATCH")
    if completed < BOOTSTRAP_BUDGET and progress["phase"] != "BOOTSTRAP":
        raise ValueError("BAD_BOOTSTRAP_RESUME_PHASE")
    if len(records) == completed:
        return state, records, data
    ar = copy.deepcopy(state["archive"])
    seen = set(state["seen_strategy_ids"])
    for record in records[completed:]:
        sid = record["strategy"]["strategy_id"]
        if sid in seen:
            raise ValueError("JOURNAL_TAIL_DUPLICATE:" + sid)
        _apply_record_fast(ar, record)
        seen.add(sid)
    full_sha = hashlib.sha256(data).hexdigest()
    state = _checkpoint_state(ar, len(records), seen, full_sha, cp)
    return state, records, data


def _summary(outdir, state, records, journal_path, checkpoint_path):
    ar = state["archive"]
    archive.validate(ar)
    ids = [r["strategy"]["strategy_id"] for r in records]
    sequence_sha = hashlib.sha256("".join(ids).encode()).hexdigest()
    if len(records) == BOOTSTRAP_BUDGET and sequence_sha != EXPECTED_SEQUENCE_SHA256:
        raise ValueError("FINAL_BOOTSTRAP_SEQUENCE_HASH_DRIFT")
    statuses = {}
    exact = 0
    for record in records:
        statuses[record["status"]] = statuses.get(record["status"], 0) + 1
        if record["status"] == "EVALUATED" and bool(record["result"].get("exact_pass")):
            exact += 1
    return {
        "schema_version": 1,
        "kind": "V57_V433_QD_BOOTSTRAP_2048_RESULT_V1",
        "status": "COMPLETE" if len(records) == BOOTSTRAP_BUDGET else "PARTIAL",
        "engine": ENGINE,
        "completed_candidates": len(records),
        "budget": BOOTSTRAP_BUDGET,
        "seed": SEED,
        "batch_size": BATCH_SIZE,
        "candidate_sequence_sha256": sequence_sha,
        "expected_complete_sequence_sha256": EXPECTED_SEQUENCE_SHA256,
        "status_counts": dict(sorted(statuses.items())),
        "evaluated": statuses.get("EVALUATED", 0),
        "prefilter_reject": statuses.get("PREFILTER_REJECT", 0),
        "exact_pass": exact,
        "archive_candidate_pool": len(ar["candidate_pool"]),
        "archive_active": len(archive.active_entries(ar)),
        "archive_exact_backlog": len(ar["exact_backlog"]),
        "archive_seen_evaluated": len(ar["seen"]),
        "all_candidate_ids_seen": len(state["seen_strategy_ids"]),
        "journal_records": state["journal"]["records"],
        "journal_sha256": state["journal"]["sha256"],
        "journal_file_sha256": H(journal_path) if Path(journal_path).exists() else hashlib.sha256(b"").hexdigest(),
        "checkpoint_sha256": H(checkpoint_path),
        "checkpoint_state_fingerprint": checkpoint.state_fingerprint(state),
        "audit_184_reused_as_search_seed": False,
        "holdout_authorized": False,
        "holdout_read": False,
        "holdout_evaluated": False,
        "september_2026_data_accessed": False,
        "demo_orders_allowed": False,
        "real_orders_allowed": False,
        "shadow_authorized": False,
        "whitelist_created": False,
    }


def run(outdir, stop_after=None):
    _ensure()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    journal_path = out / "V57_V433_QD_BOOTSTRAP_2048_RECORDS_V1.jsonl"
    checkpoint_path = out / "checkpoint_v1.json"
    summary_path = out / "V57_V433_QD_BOOTSTRAP_2048_RESULT_V1.json"
    state, records, journal_data = _reconcile(checkpoint_path, journal_path)
    completed = len(records)
    if stop_after is None:
        target = BOOTSTRAP_BUDGET
    else:
        target = int(stop_after)
        if target < completed or target > BOOTSTRAP_BUDGET:
            raise ValueError("BAD_STOP_AFTER")
    ar = copy.deepcopy(state["archive"])
    seen = set(state["seen_strategy_ids"])
    hasher = hashlib.sha256()
    hasher.update(journal_data)
    contexts, stores = {}, {}
    while completed < target:
        n = min(BATCH_SIZE, target - completed)
        items = orchestrator.exploration_items(n, SEED, completed)
        for item in items:
            idx = completed
            sid = item["strategy"]["strategy_id"]
            if sid in seen:
                raise ValueError("BOOTSTRAP_GLOBAL_DUPLICATE:" + sid)
            record = orchestrator.evaluate_item(item, "BOOTSTRAP", idx, contexts, stores)
            if record.get("status") == "ERROR":
                raise RuntimeError("BOOTSTRAP_EVALUATION_ERROR:%d:%s" % (idx, record.get("error")))
            if record.get("status") not in ("EVALUATED", "PREFILTER_REJECT"):
                raise RuntimeError("BOOTSTRAP_BAD_STATUS:%d:%s" % (idx, record.get("status")))
            line = _append_record(journal_path, record)
            hasher.update(line)
            records.append(record)
            _apply_record_fast(ar, record)
            seen.add(sid)
            completed += 1
            if checkpoint.checkpoint_due(completed) or completed == target or completed == BOOTSTRAP_BUDGET:
                state = _checkpoint_state(ar, completed, seen, hasher.hexdigest(), checkpoint_path)
                print("BOOTSTRAP_CHECKPOINT=%d|CHECKPOINT_SHA256=%s" % (completed, H(checkpoint_path)), flush=True)
    if state["progress"]["completed_candidates"] != completed:
        state = _checkpoint_state(ar, completed, seen, hasher.hexdigest(), checkpoint_path)
    result = _summary(out, state, records, journal_path, checkpoint_path)
    data = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode()
    summary_path.write_bytes(data)
    return result


def self_check():
    _ensure()
    ar = archive.new_archive()
    archive.validate(ar)
    if ar["seen"] or ar["candidate_pool"] or ar["exact_backlog"] or archive.active_entries(ar):
        raise AssertionError("NONEMPTY_BOOTSTRAP_START")
    full = orchestrator.exploration_items(BOOTSTRAP_BUDGET, SEED, 0)
    ids = [x["strategy"]["strategy_id"] for x in full]
    if len(set(ids)) != BOOTSTRAP_BUDGET:
        raise AssertionError("BOOTSTRAP_ID_DUPLICATE")
    if hashlib.sha256("".join(ids).encode()).hexdigest() != EXPECTED_SEQUENCE_SHA256:
        raise AssertionError("BOOTSTRAP_SEQUENCE_HASH_DRIFT")
    p = checkpoint.make_progress("BOOTSTRAP", completed_candidates=128, bootstrap_next_start=128)
    if p["bootstrap_next_start"] != 128 or not checkpoint.checkpoint_due(128):
        raise AssertionError("CHECKPOINT_128_SEMANTIC_FAILURE")
    c = runner_contract()
    if c["audit_184_reused_as_search_seed"] is not False or c["holdout_read"] is not False or c["orders_allowed"] is not False:
        raise AssertionError("RUNNER_SAFETY_CONTRACT_FAILURE")
    print("V57_V433_QD_BOOTSTRAP_RUNNER_V1_SELF_CHECK=PASS|START=EMPTY_ARCHIVE|BUDGET=2048|BATCH=128|SEED=943301|SEQUENCE_SHA=5b915130...|RECORD_FSYNC=YES|TAIL_RECOVERY=NO_REEVALUATION|HOLDOUT=UNREAD|ORDERS=DISABLED")
    return True


if __name__ == "__main__":
    if len(sys.argv) == 1:
        self_check()
    else:
        limit = None if len(sys.argv) < 3 else int(sys.argv[2])
        result = run(sys.argv[1], limit)
        print("BOOTSTRAP_RUN_RESULT=" + json.dumps(result, sort_keys=True))
