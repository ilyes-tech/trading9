from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import v57_qd_archive_engine_v1 as archive

ENGINE = "V57_V433_QD_CHECKPOINT_RESUME_ENGINE_V1"
ROOT = Path(__file__).resolve().parents[2]

POLICY_PATH = ROOT / "config/v433/V57_V433_QD_SEARCH_POLICY_V1.json"
ORCHESTRATOR_PATH = ROOT / "src/v433/v57_qd_orchestrator_engine_v1.py"
ORCHESTRATOR_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_ORCHESTRATOR_ENGINE_V1_FREEZE_V1.json"
SCHEDULER_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_SCHEDULER_ENGINE_V1_FREEZE_V1.json"
ARCHIVE_FREEZE_PATH = ROOT / "config/v433/V57_V433_QD_ARCHIVE_ENGINE_V1_FREEZE_V1.json"

EXPECTED = {
    str(POLICY_PATH): "d17db736f2675750e787da8ad8b02b3f178f2a042fd4b273dde15dde2604d29f",
    str(ORCHESTRATOR_PATH): "a8d477e184ab1e7d62024549731a7a5cf15d8904d6cae03a5b1d1f058de978ff",
    str(ORCHESTRATOR_FREEZE_PATH): "5b29ffe897fbd421c3295ce989b7731c5a5e01d32c8a5b58e22c5681e80ff21b",
    str(SCHEDULER_FREEZE_PATH): "f23c4916de2555f9e28d7167061638743b09b7bd398a117239651686fce44535",
    str(ARCHIVE_FREEZE_PATH): "0bfa5c7ab8c84e96ab09a3e3bfda860b0440daf2af6b1c9a63b28b588522535f",
}

P = json.loads(POLICY_PATH.read_text())
CHECKPOINT_EVERY = int(P["budget"]["checkpoint_every_candidates"])
BOOTSTRAP_BUDGET = int(P["budget"]["bootstrap"]["candidate_budget"])
CYCLE_EXPLORATION_BUDGET = int(P["budget"]["cycle"]["exploration_budget"])
CYCLE_EXPLOITATION_BUDGET = int(P["budget"]["cycle"]["exploitation_budget"])
PHASES = ("BOOTSTRAP", "CYCLE_EXPLORATION", "CYCLE_EXPLOITATION", "COMPLETE")
RI_KEYS = (
    "holdout_authorized",
    "holdout_read",
    "holdout_evaluated",
    "september_2026_data_accessed",
    "demo_orders_allowed",
    "real_orders_allowed",
)


def H(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _ensure():
    for path, expected in EXPECTED.items():
        if H(path) != expected:
            raise ValueError("ANCHOR_HASH_MISMATCH:" + path)
    if CHECKPOINT_EVERY != 128:
        raise ValueError("CHECKPOINT_INTERVAL_DRIFT")
    if BOOTSTRAP_BUDGET != 2048 or CYCLE_EXPLORATION_BUDGET != 1434 or CYCLE_EXPLOITATION_BUDGET != 2662:
        raise ValueError("BUDGET_DRIFT")
    return True


def checkpoint_due(completed_candidates):
    n = int(completed_candidates)
    if n < 0:
        raise ValueError("NEGATIVE_COMPLETED_CANDIDATES")
    return n > 0 and n % CHECKPOINT_EVERY == 0


def next_checkpoint_boundary(completed_candidates):
    n = int(completed_candidates)
    if n < 0:
        raise ValueError("NEGATIVE_COMPLETED_CANDIDATES")
    return ((n // CHECKPOINT_EVERY) + 1) * CHECKPOINT_EVERY


def _progress_contract(progress):
    if not isinstance(progress, dict):
        raise ValueError("BAD_PROGRESS")
    required = {
        "phase",
        "completed_candidates",
        "bootstrap_next_start",
        "cycle_exploration_next_start",
        "cycle_exploitation_completed",
        "exploitation_round",
        "exploitation_remaining_budget",
        "parent_ids",
    }
    if set(progress) != required:
        raise ValueError("BAD_PROGRESS_KEYS")
    phase = progress["phase"]
    if phase not in PHASES:
        raise ValueError("BAD_PHASE")
    ints = (
        "completed_candidates",
        "bootstrap_next_start",
        "cycle_exploration_next_start",
        "cycle_exploitation_completed",
        "exploitation_round",
        "exploitation_remaining_budget",
    )
    for key in ints:
        v = progress[key]
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise ValueError("BAD_PROGRESS_INT:" + key)
    if progress["bootstrap_next_start"] > BOOTSTRAP_BUDGET:
        raise ValueError("BOOTSTRAP_CURSOR_OVER_BUDGET")
    if progress["cycle_exploration_next_start"] > CYCLE_EXPLORATION_BUDGET:
        raise ValueError("EXPLORATION_CURSOR_OVER_BUDGET")
    if progress["cycle_exploitation_completed"] > CYCLE_EXPLOITATION_BUDGET:
        raise ValueError("EXPLOITATION_CURSOR_OVER_BUDGET")
    if progress["exploitation_remaining_budget"] != CYCLE_EXPLOITATION_BUDGET - progress["cycle_exploitation_completed"]:
        raise ValueError("EXPLOITATION_REMAINING_MISMATCH")
    parents = progress["parent_ids"]
    if not isinstance(parents, list) or any(not isinstance(x, str) or not x for x in parents):
        raise ValueError("BAD_PARENT_IDS")
    if parents != list(dict.fromkeys(parents)):
        raise ValueError("DUPLICATE_PARENT_IDS")
    return True


def make_progress(
    phase,
    completed_candidates=0,
    bootstrap_next_start=0,
    cycle_exploration_next_start=0,
    cycle_exploitation_completed=0,
    exploitation_round=0,
    parent_ids=(),
):
    done = int(cycle_exploitation_completed)
    p = {
        "phase": str(phase),
        "completed_candidates": int(completed_candidates),
        "bootstrap_next_start": int(bootstrap_next_start),
        "cycle_exploration_next_start": int(cycle_exploration_next_start),
        "cycle_exploitation_completed": done,
        "exploitation_round": int(exploitation_round),
        "exploitation_remaining_budget": CYCLE_EXPLOITATION_BUDGET - done,
        "parent_ids": list(dict.fromkeys(str(x) for x in parent_ids)),
    }
    _progress_contract(p)
    return p


def make_state(ar, progress, seen_strategy_ids=(), journal_records=0, journal_sha256=None):
    _ensure()
    archive.validate(ar)
    _progress_contract(progress)
    seen = sorted(set(str(x) for x in seen_strategy_ids))
    if any(not x for x in seen):
        raise ValueError("BAD_SEEN_STRATEGY_ID")
    jr = int(journal_records)
    if jr < 0:
        raise ValueError("BAD_JOURNAL_RECORDS")
    empty_sha = hashlib.sha256(b"").hexdigest()
    js = empty_sha if journal_sha256 is None else str(journal_sha256)
    if len(js) != 64 or any(c not in "0123456789abcdef" for c in js):
        raise ValueError("BAD_JOURNAL_SHA256")
    state = {
        "schema_version": 1,
        "kind": "V57_V433_QD_CHECKPOINT_STATE_V1",
        "engine": ENGINE,
        "anchors": {
            "policy_sha256": EXPECTED[str(POLICY_PATH)],
            "orchestrator_sha256": EXPECTED[str(ORCHESTRATOR_PATH)],
            "orchestrator_freeze_sha256": EXPECTED[str(ORCHESTRATOR_FREEZE_PATH)],
            "scheduler_freeze_sha256": EXPECTED[str(SCHEDULER_FREEZE_PATH)],
            "archive_freeze_sha256": EXPECTED[str(ARCHIVE_FREEZE_PATH)],
        },
        "progress": copy.deepcopy(progress),
        "seen_strategy_ids": seen,
        "journal": {"records": jr, "sha256": js},
        "archive": copy.deepcopy(ar),
        "research_integrity": {k: False for k in RI_KEYS},
    }
    validate_state(state)
    return state


def validate_state(state):
    _ensure()
    if not isinstance(state, dict) or state.get("schema_version") != 1:
        raise ValueError("BAD_STATE_SCHEMA")
    if state.get("kind") != "V57_V433_QD_CHECKPOINT_STATE_V1" or state.get("engine") != ENGINE:
        raise ValueError("BAD_STATE_KIND")
    expected_anchors = {
        "policy_sha256": EXPECTED[str(POLICY_PATH)],
        "orchestrator_sha256": EXPECTED[str(ORCHESTRATOR_PATH)],
        "orchestrator_freeze_sha256": EXPECTED[str(ORCHESTRATOR_FREEZE_PATH)],
        "scheduler_freeze_sha256": EXPECTED[str(SCHEDULER_FREEZE_PATH)],
        "archive_freeze_sha256": EXPECTED[str(ARCHIVE_FREEZE_PATH)],
    }
    if state.get("anchors") != expected_anchors:
        raise ValueError("STATE_ANCHOR_MISMATCH")
    _progress_contract(state.get("progress"))
    seen = state.get("seen_strategy_ids")
    if not isinstance(seen, list) or seen != sorted(set(seen)) or any(not isinstance(x, str) or not x for x in seen):
        raise ValueError("BAD_SEEN_STRATEGY_IDS")
    journal = state.get("journal")
    if not isinstance(journal, dict) or set(journal) != {"records", "sha256"}:
        raise ValueError("BAD_JOURNAL")
    if isinstance(journal["records"], bool) or not isinstance(journal["records"], int) or journal["records"] < 0:
        raise ValueError("BAD_JOURNAL_RECORDS")
    js = journal["sha256"]
    if not isinstance(js, str) or len(js) != 64 or any(c not in "0123456789abcdef" for c in js):
        raise ValueError("BAD_JOURNAL_SHA256")
    archive.validate(state.get("archive"))
    ri = state.get("research_integrity", {})
    if set(ri) != set(RI_KEYS) or any(ri[k] is not False for k in RI_KEYS):
        raise ValueError("CHECKPOINT_RESEARCH_INTEGRITY_VIOLATION")
    return True


def state_fingerprint(state):
    validate_state(state)
    return hashlib.sha256(canonical(state).encode()).hexdigest()


def save_checkpoint(path, state):
    validate_state(state)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(state)
    envelope = {
        "schema_version": 1,
        "kind": "V57_V433_QD_CHECKPOINT_ENVELOPE_V1",
        "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "payload": state,
    }
    data = (json.dumps(envelope, indent=2, sort_keys=True) + "\n").encode()
    fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, target)
        try:
            dfd = os.open(str(target.parent), os.O_DIRECTORY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except (AttributeError, OSError):
            pass
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return H(target)


def _restore_archive_contract_order(obj):
    if isinstance(obj, dict):
        specs=(("objectives",[x[0] for x in archive.OBJECTIVES]),("support",list(archive.SUPPORT)),("descriptor",list(archive.DIMS)))
        for field,keys in specs:
            value=obj.get(field)
            if isinstance(value,dict) and set(value)==set(keys):
                obj[field]={k:value[k] for k in keys}
        for value in obj.values():
            _restore_archive_contract_order(value)
    elif isinstance(obj,list):
        for value in obj:
            _restore_archive_contract_order(value)
    return obj

def load_checkpoint(path):
    _ensure()
    p = Path(path)
    envelope = json.loads(p.read_text())
    if envelope.get("schema_version") != 1 or envelope.get("kind") != "V57_V433_QD_CHECKPOINT_ENVELOPE_V1":
        raise ValueError("BAD_CHECKPOINT_ENVELOPE")
    state = envelope.get("payload")
    digest = hashlib.sha256(canonical(state).encode()).hexdigest()
    if digest != envelope.get("payload_sha256"):
        raise ValueError("CHECKPOINT_PAYLOAD_HASH_MISMATCH")
    _restore_archive_contract_order(state.get("archive"))
    validate_state(state)
    return state


def resume_contract():
    return {
        "engine": ENGINE,
        "checkpoint_every_candidates": CHECKPOINT_EVERY,
        "write_mode": "ATOMIC_TEMP_FSYNC_REPLACE",
        "integrity": "CANONICAL_PAYLOAD_SHA256_PLUS_FROZEN_ANCHORS",
        "archive_snapshot": True,
        "seen_strategy_ids_persisted": True,
        "journal_fingerprint_persisted": True,
        "resume_replays_completed_candidates": False,
        "holdout_read": False,
        "orders_allowed": False,
    }


def self_check():
    _ensure()
    if checkpoint_due(0) or checkpoint_due(127) or not checkpoint_due(128) or checkpoint_due(129):
        raise AssertionError("CHECKPOINT_DUE_CONTRACT_FAILURE")
    if next_checkpoint_boundary(0) != 128 or next_checkpoint_boundary(128) != 256:
        raise AssertionError("CHECKPOINT_BOUNDARY_FAILURE")
    ar = archive.new_archive()
    archive.validate(ar)
    p = make_progress("CYCLE_EXPLORATION", completed_candidates=128, cycle_exploration_next_start=128)
    state = make_state(ar, p, ["b", "a", "a"], 128, hashlib.sha256(b"x").hexdigest())
    if state["seen_strategy_ids"] != ["a", "b"]:
        raise AssertionError("SEEN_DEDUP_SORT_FAILURE")
    fp = state_fingerprint(state)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "checkpoint.json"
        save_checkpoint(path, state)
        loaded = load_checkpoint(path)
        if canonical(loaded) != canonical(state) or state_fingerprint(loaded) != fp:
            raise AssertionError("CHECKPOINT_ROUNDTRIP_FAILURE")
        env = json.loads(path.read_text())
        env["payload"]["progress"]["completed_candidates"] = 129
        path.write_text(json.dumps(env, sort_keys=True))
        try:
            load_checkpoint(path)
        except ValueError as exc:
            if str(exc) != "CHECKPOINT_PAYLOAD_HASH_MISMATCH":
                raise
        else:
            raise AssertionError("TAMPER_NOT_DETECTED")
    c = resume_contract()
    if c["checkpoint_every_candidates"] != 128 or c["resume_replays_completed_candidates"] is not False:
        raise AssertionError("RESUME_CONTRACT_DRIFT")
    print("V57_V433_QD_CHECKPOINT_RESUME_ENGINE_V1_SELF_CHECK=PASS|INTERVAL=128|ATOMIC_WRITE=YES|PAYLOAD_HASH=SHA256|ANCHORS=FROZEN|SEEN_IDS=PERSISTED|ARCHIVE_SNAPSHOT=YES|NO_COMPLETED_REPLAY=YES|HOLDOUT=UNREAD|ORDERS=DISABLED")


if __name__ == "__main__":
    self_check()
