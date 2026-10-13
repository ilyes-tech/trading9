"""Read-only venue-vs-receive timing audit; NEVER a clock accuracy certificate."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3

STATE = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
CAPTURE = STATE / "stage03_prospective_public_capture_v2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lag_statistics(rows: list[tuple[str, int]]) -> dict:
    lags: list[float] = []
    for iso, receive_ns in rows:
        stamp = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None or type(receive_ns) is not int:
            raise ValueError("INVALID_EVENT_CLOCK_FIELD")
        lag = receive_ns / 1e9 - stamp.timestamp()
        if not -86400 < lag < 86400:
            raise ValueError("INVALID_CLOCK_DIFFERENCE")
        lags.append(lag)
    if not lags:
        raise ValueError("EMPTY_EVENT_TIMING")
    lags.sort()
    n = len(lags)
    return {
        "rows": n,
        "minimum_seconds": round(lags[0], 4),
        "p05_seconds": round(lags[int(.05 * (n - 1))], 4),
        "median_seconds": round((lags[(n - 1) // 2] + lags[n // 2]) / 2, 4),
        "p95_seconds": round(lags[int(.95 * (n - 1))], 4),
        "p99_seconds": round(lags[int(.99 * (n - 1))], 4),
        "maximum_seconds": round(lags[-1], 4),
        "negative_lag_rows": sum(value < 0 for value in lags),
        "lag_over_five_seconds_rows": sum(value > 5 for value in lags),
    }


def audit(capture: Path = CAPTURE, state: Path = STATE) -> dict:
    auth = json.loads((state / "search_authorization_v1.json").read_text())
    if auth.get("status") != "DENIED" or auth.get("authorized") is not False or any(
        auth.get(flag) is not False for flag in ("orders_allowed", "mt5_allowed", "holdout_allowed")
    ):
        raise ValueError("RESEARCH_GATE_NOT_DENIED")
    custody = json.loads((capture / "final_custody_v1.json").read_text())
    if (custody.get("status") != "RAW_CAPTURE_INTEGRITY_VERIFIED_NOT_SCIENTIFICALLY_ADMITTED"
            or custody.get("clock_ntp_sync_verified") is not False
            or custody.get("candidate_admitted") is not False):
        raise ValueError("FINAL_CUSTODY_NOT_SAFE")
    database = capture / "spot_raw.sqlite3"
    if not database.is_file() or database.is_symlink() or digest(database) != custody["sqlite_raw_sha256"]:
        raise ValueError("DATASET_CUSTODY_MISMATCH")
    connection = sqlite3.connect("file:" + str(database.resolve()) + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        markets = []
        for symbol in ("BTC/USD", "ETH/USD"):
            sections = {}
            for table, event_col, label in (
                ("public_trades", "event_time", "public_trades"),
                ("microstructure_500ms", "book_time", "book_snapshots"),
            ):
                rows = connection.execute(
                    f"SELECT {event_col},received_ns FROM {table} WHERE symbol=? ORDER BY id",
                    (symbol,)
                ).fetchall()
                sections[label] = lag_statistics(rows)
            expected = next(row for row in custody["markets"] if row["symbol"] == symbol)
            if (sections["public_trades"]["rows"] != expected["public_trades"]
                    or sections["book_snapshots"]["rows"] != expected["book_samples"]):
                raise ValueError("CUSTODY_ROW_COUNT_MISMATCH")
            markets.append({"market": symbol, **sections})
    finally:
        connection.close()
    return {
        "kind": "OMEGA_STAGE03_VENUE_RECEIVE_TIME_QUALITY_V1",
        "status": "TIMING_PROXIES_RECONCILED_NTP_NOT_VERIFIED_SCIENTIFIC_ADMISSION_DENIED",
        "raw_sqlite_sha256": custody["sqlite_raw_sha256"],
        "final_custody_sha256": digest(capture / "final_custody_v1.json"),
        "markets": markets,
        "lag_interpretation": "VENUE_EVENT_TO_LOCAL_RECEIPT_DIFFERENCE_INCLUDES_CLOCK_SKEW_AND_TRANSPORT_QUEUE_DELAY",
        "absolute_clock_accuracy_independently_verified": False,
        "source_event_timestamps_independently_attested": False,
        "historical_capture_clock_ntp_verified": False,
        "data_role": "EXPLORATORY_NOT_HOLDOUT",
        "scientific_candidate_admitted": False,
        "research_execution_authorized": False,
        "backtest_executed": False,
        "search_executed": False,
        "orders_allowed": False,
        "mt5_allowed": False,
        "holdout_allowed": False,
        "auto_promotion_allowed": False,
    }


def main() -> None:
    proof = audit()
    target = CAPTURE / "venue_receive_time_quality_v1.json"
    if target.exists():
        if json.loads(target.read_text()) != proof:
            raise ValueError("IMMUTABLE_PROOF_MISMATCH")
    else:
        with target.open("x") as output:
            json.dump(proof, output, indent=2, sort_keys=True, allow_nan=False)
            output.write("\n")
    print("ALL PASS|REAL_CAPTURE_CLOCK_LAG_AUDIT|MARKETS=2|NTP_UNVERIFIED|RESEARCH=NO|ORDERS=NO")
    print("ARTIFACT_SHA256", digest(target))


if __name__ == "__main__":
    main()
