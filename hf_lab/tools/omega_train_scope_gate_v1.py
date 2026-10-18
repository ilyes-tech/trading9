"""Internal train-prefix preflight, isolated from JARVIS scientific admission and execution.

Metadata + byte hashes ONLY: never parses prices, scores returns, runs a search,
opens the reserved validation/holdout tail, or authorizes an order.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
PROTOCOL_SHA = "a8a784356ad9dfb39271ecd44afb61a46226c7f81720b63acab80de6e0c4a437"
TIMING_SHA = "0a8f125958bb628a145304955f4017eedea61c53c21ee584e7335298c6dd09a7"
ROWS = {"BTCUSD": 79267, "ETHUSD": 79269}


def pinned_json(path: Path, digest: str) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("PINNED_FILE_MISSING_OR_SYMLINK")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError("PINNED_SHA256_MISMATCH")
    return json.loads(content)


def hash_exact_prefix(path: Path, count: int) -> str:
    """Read exactly header + count rows with an unbuffered descriptor.

    No read, seek, iteration or peek into reserved later rows.
    """
    if type(count) is not int or count < 1 or count > 100000:
        raise ValueError("ROW_SCOPE_INVALID")
    if path.is_symlink() or not path.is_file():
        raise ValueError("TRAIN_FILE_MISSING_OR_SYMLINK")
    digest = hashlib.sha256()
    with path.open("rb", buffering=0) as source:
        for _ in range(count + 1):
            row = source.readline()
            if not row:
                raise ValueError("TRAIN_PREFIX_TRUNCATED")
            digest.update(row)
    return digest.hexdigest()


def preflight(root: Path = ROOT, state: Path = STATE, *, inspect_train_bytes: bool = False) -> dict:
    protocol = pinned_json(root / "OMEGA_STAGE03_BTC_ETH_LEAD_LAG_REVIEW_ONLY_V1.json", PROTOCOL_SHA)
    timing = pinned_json(root / "OMEGA_STAGE03_BTC_ETH_TRAIN_ONLY_TIMING_PREFLIGHT_V1.json", TIMING_SHA)
    budget = {"max_holdout_evaluations": 0, "max_hypotheses": 1,
              "max_parameter_variants": 1, "new_experiments_authorized": 0}
    if protocol.get("budget") != budget or any(protocol.get(k) is not False for k in
        ("research_execution_authorized", "search_execution_authorized", "orders_allowed",
         "mt5_allowed", "holdout_allowed", "auto_promotion_allowed")):
        raise ValueError("PROTOCOL_SCOPE_CHANGED")
    design = protocol["review_only_fixed_exploratory_development_design"]
    if (design["one_candidate_only"]["name"] != "BTC_TO_ETH_ONE_MINUTE_DELAY_DIRECTION_BASELINE_V1"
            or design["assessment_without_tuning"]["max_candidate_rules"] != 1
            or design["assessment_without_tuning"]["no_final_holdout"] is not True):
        raise ValueError("CANDIDATE_SCOPE_CHANGED")
    if (timing["manifest_serialization_reconciliation"]["status"]
            != "RECONCILED_AS_REEXPORT_TIMESTAMP_FORMAT_CHANGE_NO_RAW_DATA_MODIFIED"
            or timing["original_download_database_train_prefix_reconciliation"]["status"]
            != "TRAIN_ONLY_FULL_ROW_EXACT_MATCH_LOCAL_CAPTURE_DB_TO_CSV"):
        raise ValueError("TRAIN_CUSTODY_NOT_RECONCILED")
    if any(timing.get(k) is not False for k in
        ("research_execution_authorized", "search_execution_authorized", "holdout_accessed",
         "orders_allowed", "mt5_allowed")):
        raise ValueError("TRAIN_CUSTODY_STATUS_CHANGED")
    expected_states = {
        "search_authorization_v1.json": {"status": "DENIED", "authorized": False,
                                          "max_candidates": 0, "orders_allowed": False,
                                          "holdout_allowed": False},
        "search_execution_gate_v1.json": {"status": "DENIED", "ready": False,
                                           "search_process_started": False,
                                           "orders_allowed": False, "holdout_allowed": False},
        "research_continuous_runner_v1.json": {"status": "SAFE_IDLE",
                                                "search_executed": False,
                                                "orders_allowed": False, "holdout_allowed": False},
    }
    for filename, required in expected_states.items():
        file = state / filename
        if file.is_symlink() or not file.is_file():
            raise ValueError("MISSING_DENIAL:" + filename)
        current = json.loads(file.read_bytes())
        if any(current.get(key) != value or type(current.get(key)) is not type(value)
               for key, value in required.items()):
            raise ValueError("GLOBAL_SAFETY_GATE_NOT_DENIED:" + filename)
    hashes = {}
    for market, count in ROWS.items():
        metadata = timing["training"][market]
        expected = protocol["proposed_data"][market[:3].lower() + "_train_prefix_sha256"]
        if metadata.get("train_rows") != count or metadata.get("train_prefix_sha256") != expected:
            raise ValueError("TRAIN_PREFIX_NOT_BOUND:" + market)
        if inspect_train_bytes:
            path = root / "data" / "coinbase_m1_q4_2025" / (market + "_M1.csv")
            if hash_exact_prefix(path, count) != expected:
                raise ValueError("TRAIN_PREFIX_SHA256_MISMATCH:" + market)
        hashes[market] = expected if inspect_train_bytes else None
    return {"status": "PASS_METADATA_AND_TRAIN_PREFIX_ONLY" if inspect_train_bytes
            else "PASS_METADATA_ONLY", "market_prefix_rows": ROWS,
            "verified_train_prefix_sha256": hashes,
            "candidate_limit": 1, "market_signal_or_return_computed": False,
            "new_experiments_authorized": 0, "scientific_admission": False,
            "searcher_executed": False, "orders_allowed": False,
            "mt5_allowed": False, "holdout_read": False, "holdout_allowed": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-pinned-train-prefixes", action="store_true")
    args = parser.parse_args()
    result = preflight(inspect_train_bytes=args.verify_pinned_train_prefixes)
    print(json.dumps(result, sort_keys=True))
