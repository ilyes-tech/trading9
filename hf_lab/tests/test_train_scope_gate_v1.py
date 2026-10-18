"""No-market-data tests: metadata-only guard and exact prefix byte boundary."""
from pathlib import Path
import hashlib
import json

import pytest

from hf_lab.tools.omega_train_scope_gate_v1 import (
    ROOT, hash_exact_prefix, preflight,
)


def safe_state(path: Path) -> None:
    docs = {
        "search_authorization_v1.json": {
            "status": "DENIED", "authorized": False, "max_candidates": 0,
            "orders_allowed": False, "holdout_allowed": False,
        },
        "search_execution_gate_v1.json": {
            "status": "DENIED", "ready": False,
            "search_process_started": False, "orders_allowed": False,
            "holdout_allowed": False,
        },
        "research_continuous_runner_v1.json": {
            "status": "SAFE_IDLE", "search_executed": False,
            "orders_allowed": False, "holdout_allowed": False,
        },
    }
    for filename, content in docs.items():
        (path / filename).write_text(json.dumps(content))


def test_internal_preflight_is_metadata_only_and_denies_experiment(tmp_path):
    safe_state(tmp_path)
    result = preflight(ROOT, tmp_path)
    assert result["status"] == "PASS_METADATA_ONLY"
    assert result["candidate_limit"] == 1
    assert result["new_experiments_authorized"] == 0
    assert result["scientific_admission"] is False
    assert result["market_signal_or_return_computed"] is False
    assert result["holdout_read"] is False
    assert result["orders_allowed"] is False


@pytest.mark.parametrize("file,key,value", [
    ("search_authorization_v1.json", "authorized", True),
    ("search_execution_gate_v1.json", "ready", True),
    ("research_continuous_runner_v1.json", "search_executed", True),
    ("search_authorization_v1.json", "max_candidates", 1),
    ("search_authorization_v1.json", "holdout_allowed", True),
])
def test_global_safety_mutation_is_denied(tmp_path, file, key, value):
    safe_state(tmp_path)
    p = tmp_path / file
    doc = json.loads(p.read_text())
    doc[key] = value
    p.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="GLOBAL_SAFETY_GATE_NOT_DENIED"):
        preflight(ROOT, tmp_path)


def test_missing_or_symlinked_global_denial_is_rejected(tmp_path):
    safe_state(tmp_path)
    original = tmp_path / "search_execution_gate_v1.json"
    original.unlink()
    with pytest.raises(ValueError, match="MISSING_DENIAL"):
        preflight(ROOT, tmp_path)
    original.symlink_to(tmp_path / "search_authorization_v1.json")
    with pytest.raises(ValueError, match="MISSING_DENIAL"):
        preflight(ROOT, tmp_path)


def test_immutable_protocol_changed_fails_closed(tmp_path):
    safe_state(tmp_path)
    root = tmp_path / "repo"
    root.mkdir()
    source = ROOT / "OMEGA_STAGE03_BTC_ETH_LEAD_LAG_REVIEW_ONLY_V1.json"
    (root / source.name).write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="PINNED_SHA256_MISMATCH"):
        preflight(root, tmp_path)


def test_prefix_byte_read_stops_before_reserved_tail(tmp_path):
    p = tmp_path / "safe.csv"
    header = b"header\n"
    rows = [b"first_train\n", b"second_train\n"]
    reserved = b"RESERVED_HOLDOUT_MUST_NEVER_BE_READ\n"
    p.write_bytes(header + b"".join(rows) + reserved)
    assert hash_exact_prefix(p, 2) == hashlib.sha256(header + b"".join(rows)).hexdigest()
    with pytest.raises(ValueError, match="ROW_SCOPE_INVALID"):
        hash_exact_prefix(p, 100001)
    with pytest.raises(ValueError, match="ROW_SCOPE_INVALID"):
        hash_exact_prefix(p, True)


def test_prefix_truncation_and_symlinks_fail_closed(tmp_path):
    p = tmp_path / "short.csv"
    p.write_bytes(b"header\nrow1\n")
    with pytest.raises(ValueError, match="TRAIN_PREFIX_TRUNCATED"):
        hash_exact_prefix(p, 2)
    s = tmp_path / "link.csv"
    s.symlink_to(p)
    with pytest.raises(ValueError, match="TRAIN_FILE_MISSING_OR_SYMLINK"):
        hash_exact_prefix(s, 1)
