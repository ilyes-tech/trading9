"""Fail-closed custody audit for OMEGA's bounded, public Kraken raw capture.

This checks structural integrity, not clock trust, causal novelty or admission.
No strategy execution, network access, holdout access or trading is permitted.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path("/home/trading/TradingAI-HF-Lab")
STATE = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
CAPTURE = STATE / "stage03_prospective_public_capture_v2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_capture(capture: Path, state: Path, source: Path) -> dict:
    preflight_file = capture / "preflight.json"
    status_file = capture / "collector_status.json"
    db = capture / "spot_raw.sqlite3"
    for file in (preflight_file, status_file, db, source):
        if not file.is_file() or file.is_symlink():
            raise ValueError("MISSING_OR_SYMLINKED_EVIDENCE")

    auth = json.loads((state / "search_authorization_v1.json").read_text())
    if (auth.get("status") != "DENIED" or auth.get("authorized") is not False
            or auth.get("execution_started") is not False
            or any(auth.get(x) is not False for x in
                   ("orders_allowed", "mt5_allowed", "holdout_allowed"))):
        raise ValueError("UNSAFE_AUTHORIZATION_STATE")

    preflight = json.loads(preflight_file.read_text())
    status = json.loads(status_file.read_text())
    if (preflight.get("kind") != "OMEGA_STAGE03_KRAKEN_PUBLIC_PROSPECTIVE_CAPTURE_V2"
            or preflight.get("status") != "CAPTURE_PREFLIGHT_ONLY_NOT_SCIENTIFIC_ADMISSION"
            or preflight.get("max_runtime_seconds") != 7200):
        raise ValueError("INVALID_PREFLIGHT")
    for flag in ("research_execution_authorized", "orders_allowed", "mt5_allowed",
                 "holdout_allowed", "search_executed", "candidate_admitted"):
        if preflight.get(flag) is not False:
            raise ValueError("UNSAFE_PREFLIGHT")

    if sha256(source) != preflight.get("source_code_sha256"):
        raise ValueError("COLLECTOR_CODE_MISMATCH")
    runner = capture / "collector_runner.py"
    if not runner.is_file() or runner.is_symlink() or sha256(runner) != preflight.get("wrapper_sha256"):
        raise ValueError("COLLECTOR_RUNNER_MISMATCH")

    # Never hash a live SQLite database as an immutable proof.
    if status.get("state") != "STOPPED":
        raise ValueError("CAPTURE_NOT_STOPPED")
    wal = capture / "spot_raw.sqlite3-wal"
    if wal.exists() and wal.stat().st_size:
        raise ValueError("UNCHECKPOINTED_SQLITE_WAL")
    if status.get("private_api") is not False or status.get("real_orders") is not False:
        raise ValueError("UNSAFE_COLLECTOR_STATUS")
    if status.get("checksum_fail") != 0:
        raise ValueError("CHECKSUM_FAILURE_REQUIRES_REVIEW")

    try:
        conn = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True, timeout=5)
        conn.execute("PRAGMA query_only=ON")
        if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("SQLITE_INTEGRITY_FAILED")
        sessions = conn.execute(
            "SELECT status, started_at, ended_at, reconnects, messages, "
            "samples_inserted, trades_inserted, checksum_ok, checksum_fail, last_error "
            "FROM collector_sessions"
        ).fetchall()
        if len(sessions) != 1 or sessions[0][0] != "STOPPED" or not sessions[0][2]:
            raise ValueError("INCOMPLETE_SESSION")
        session = sessions[0]
        started = datetime.fromisoformat(session[1])
        ended = datetime.fromisoformat(session[2])
        declared = datetime.fromisoformat(preflight["created_at_utc"])
        if not (declared < started < ended):
            raise ValueError("BAD_DECLARED_SEQUENCE")
        if (ended - started).total_seconds() > 7222:
            raise ValueError("EXCEEDED_BOUNDED_CAPTURE_WINDOW")
        if session[8] != 0:
            raise ValueError("COLLECTOR_CHECKSUM_FAILURE")
        if (session[5] != status.get("samples_inserted")
                or session[6] != status.get("trades_inserted")
                or session[7] != status.get("checksum_ok")):
            raise ValueError("SESSION_STATUS_MISMATCH")

        by_market = []
        for symbol in ("BTC/USD", "ETH/USD"):
            samples = conn.execute(
                "SELECT COUNT(*), MIN(bucket_ns), MAX(bucket_ns), COUNT(DISTINCT bucket_ns),"
                " SUM(CASE WHEN bid<=0 OR ask<bid OR mid<=0 OR bid_qty<=0 OR ask_qty<=0 "
                " OR abs(imbalance_10)>1.000001 OR received_ns<bucket_ns "
                " OR received_ns>=bucket_ns+1000000000 THEN 1 ELSE 0 END) "
                "FROM microstructure_500ms WHERE symbol=?", (symbol,)
            ).fetchone()
            trades = conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT trade_id),"
                " SUM(CASE WHEN price<=0 OR qty<=0 OR received_ns<=0 THEN 1 ELSE 0 END)"
                "FROM public_trades WHERE symbol=?", (symbol,)
            ).fetchone()
            gaps = conn.execute(
                "WITH ordered AS (SELECT bucket_ns, LAG(bucket_ns) OVER"
                " (ORDER BY bucket_ns) AS prev FROM microstructure_500ms WHERE symbol=?) "
                "SELECT COUNT(CASE WHEN prev IS NOT NULL AND bucket_ns-prev>500000000 "
                "THEN 1 END), MAX(bucket_ns-prev) FROM ordered", (symbol,)
            ).fetchone()
            if (samples[0] <= 0 or trades[0] <= 0 or samples[0] != samples[3]
                    or samples[4] != 0 or trades[0] != trades[1] or trades[2] != 0):
                raise ValueError("INVALID_MARKET_ROWS")
            expected = (samples[2] - samples[1]) // 500000000 + 1
            by_market.append({
                "symbol": symbol, "book_samples": samples[0],
                "public_trades": trades[0],
                "expected_half_second_slots_between_observed_extremes": expected,
                "observed_slot_ratio": round(samples[0] / expected, 6),
                "gaps_over_500ms": gaps[0],
                "longest_gap_seconds": (gaps[1] or 0) / 1e9,
                "bad_sample_rows": samples[4], "bad_trade_rows": trades[2]
            })
        if (sum(r["book_samples"] for r in by_market) != session[5]
                or sum(r["public_trades"] for r in by_market) != session[6]):
            raise ValueError("SESSION_COUNT_MISMATCH")
    finally:
        conn.close()

    return {
        "kind": "OMEGA_STAGE03_KRAKEN_PUBLIC_FINAL_CUSTODY_V1",
        "status": "RAW_CAPTURE_INTEGRITY_VERIFIED_NOT_SCIENTIFICALLY_ADMITTED",
        "dataset_role": "EXPLORATORY_RAW_FEED_NOT_FINAL_HOLDOUT",
        "source": "KRAKEN_PUBLIC_WEBSOCKET_V2",
        "final_audit_script_sha256": sha256(Path(__file__)),
        "preflight_sha256": sha256(preflight_file),
        "collector_source_sha256": preflight["source_code_sha256"],
        "collector_runner_sha256": sha256(runner),
        "collector_status_sha256": sha256(status_file),
        "sqlite_raw_sha256": sha256(db),
        "session_started_at_utc_local_untrusted": session[1],
        "session_ended_at_utc_local_untrusted": session[2],
        "capture_seconds_local_untrusted": round((ended - started).total_seconds(), 3),
        "checksum_validations": session[7], "checksum_failures": session[8],
        "reconnects": session[3],
        "network_error_history_retained": bool(status.get("last_error") or session[9]),
        "network_error_last_text": str(status.get("last_error") or session[9])[:200],
        "no_gap_free_continuity_claimed": True,
        "markets": by_market,
        "clock_ntp_sync_verified": False,
        "independent_clock_and_source_provenance_verified": False,
        "independent_replication_proven": False,
        "scientific_novelty_proven": False,
        "research_execution_authorized": False, "backtest_executed": False,
        "search_executed": False, "candidate_admitted": False,
        "orders_allowed": False, "mt5_allowed": False, "holdout_allowed": False,
        "auto_promotion_allowed": False,
        "decision": "DATA_CUSTODY_ONLY_CLOCK_AND_SCIENTIFIC_ADMISSION_BLOCKED"
    }


def main() -> None:
    report = audit_capture(CAPTURE, STATE, ROOT / "tools/phase4e1_public_collector.py")
    destination = CAPTURE / "final_custody_v1.json"
    if destination.exists():
        if json.loads(destination.read_text()) != report:
            raise ValueError("FINAL_CUSTODY_IMMUTABILITY_CONFLICT")
    else:
        with destination.open("x") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
    print("ALL PASS|FINAL_CAPTURE_CUSTODY|SAMPLES=" +
          str(sum(row["book_samples"] for row in report["markets"])) +
          "|TRADES=" + str(sum(row["public_trades"] for row in report["markets"])) +
          "|NTP=UNVERIFIED|SCIENCE=DENIED|ORDERS=NO")


if __name__ == "__main__":
    main()
