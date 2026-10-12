"""Bounded synthetic-only end-to-end replay proof. NOT strategy research/admission."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import runpy
import sqlite3
import tempfile

from hf_lab.replay import Bar, ReplaySettings, run_replay
from hf_lab.strategies.candidates import momentum_burst

ROOT = Path(__file__).resolve().parents[2]
STATE = Path("/home/trading/.local/state/tradingai/jarvis-autonomous")
OUTPUT = STATE / "stage03_engineering_smoke_v1.json"
SETTINGS = ReplaySettings(fee_bps_per_side=5.0, slippage_bps_per_side=1.0,
                          shadow_only=True, allow_real_orders=False)


def synthetic_bars() -> list[Bar]:
    """Deliberately constructed price movements, not observed market data."""
    price, rows = 100.0, []
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(160):
        move = (0.23 if index % 40 < 20 else -0.29) + (index % 7 - 3) * 0.032
        close = price + move
        rows.append(Bar(time=origin + timedelta(minutes=15 * index),
                        open=price, high=max(price, close) + 0.20,
                        low=min(price, close) - 0.20, close=close,
                        volume=float(20 + index % 7), trades=3.0))
        price = close
    return rows


def exercise(path: Path, bars: list[Bar]) -> tuple[str, int, int]:
    report = run_replay(symbol="BTCUSD", dataset="SYNTHETIC_ENGINEERING_ONLY_V1",
                        bars=bars, strategy=momentum_burst, settings=SETTINGS,
                        database_path=path)
    if report.metrics.trades < 1 or report.metrics.trades != len(report.trades):
        raise RuntimeError("NO_CLOSED_TRADES")
    rows = [asdict(trade) for trade in report.trades]
    for row in rows:
        if row["strategy"] != "MOMENTUM_BURST" or row["signal_time"] >= row["entry_time"]:
            raise RuntimeError("SIGNAL_TIMING_OR_STRATEGY")
        if not all(math.isfinite(row[k]) for k in ("gross_r", "fee_r", "slippage_r", "net_r")):
            raise RuntimeError("NONFINITE_RESULT")
    verifier = runpy.run_path(str(ROOT / "research_agent_v57_quantum_searcher/tools/v57_jarvis/autonomy/v57_independent_evidence_verifier_v2.py"))
    audit = verifier["audit_replay_costs"](rows, 5.0, 1.0)
    if audit["status"] != "COST_ARITHMETIC_VERIFIED_NOT_ADMITTED":
        raise RuntimeError("COST_AUDIT:" + str(audit.get("reason")))
    with sqlite3.connect(path) as connection:
        actual = connection.execute("select count(*) from trades where result!='OPEN'").fetchone()[0]
        signals = connection.execute("select count(*) from signals").fetchone()[0]
    if actual != len(rows) or signals < actual:
        raise RuntimeError("PERSISTENCE_MISMATCH")
    normalized = [{k: (v.isoformat() if isinstance(v, datetime) else v)
                   for k, v in row.items() if k not in ("trade_id", "signal_id")}
                  for row in rows]
    fingerprint = hashlib.sha256(json.dumps(normalized, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return fingerprint, len(rows), signals


def main() -> None:
    auth = json.loads((STATE / "search_authorization_v1.json").read_text())
    if auth.get("status") != "DENIED" or auth.get("authorized") is not False or auth.get("execution_started") is not False:
        raise RuntimeError("SCIENTIFIC_GATE_NOT_DENIED")
    if any(auth.get(key) is not False for key in ("orders_allowed", "mt5_allowed", "holdout_allowed")):
        raise RuntimeError("UNSAFE_RUNTIME")
    bars = synthetic_bars()
    bar_payload = [dict(time=x.time.isoformat(), open=x.open, high=x.high, low=x.low,
                        close=x.close, volume=x.volume, trades=x.trades) for x in bars]
    with tempfile.TemporaryDirectory(prefix="omega-stage03-synth-") as folder:
        a = exercise(Path(folder) / "a.sqlite3", bars)
        b = exercise(Path(folder) / "b.sqlite3", bars)
    if a != b:
        raise RuntimeError("NONDETERMINISTIC_REPLAY")
    proof = dict(kind="OMEGA_STAGE03_SYNTHETIC_ENGINEERING_CYCLE_V1",
                 status="ENGINEERING_PASS_SCIENTIFIC_ADMISSION_STILL_DENIED",
                 source="GENERATED_SYNTHETIC_BARS_NO_MARKET_DATA",
                 fixture_sha256=hashlib.sha256(json.dumps(bar_payload, sort_keys=True).encode()).hexdigest(),
                 script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 strategy="MOMENTUM_BURST_EXISTING_NOT_READMITTED",
                 market_label="BTCUSD_SIMULATED_NOT_OBSERVED",
                 bars=len(bars), closed_trades=a[1], signals=a[2],
                 replay_fingerprint_sha256=a[0], repeat_runs=2,
                 accounting="SYNTHETIC_CLOSED_TRADES_COST_ARITHMETIC_VERIFIED",
                 assumed_fee_bps_per_side=5.0, assumed_slippage_bps_per_side=1.0,
                 costs_empirically_calibrated=False,
                 performance_on_real_markets_claimed=False,
                 development_market_backtest_executed=False,
                 scientific_candidate_admitted=False, search_executed=False,
                 real_orders_executed=False, execution_authorized=False,
                 research_execution_authorized=False, orders_allowed=False,
                 mt5_allowed=False, holdout_allowed=False, auto_promotion_allowed=False,
                 decision="TECHNICAL_PIPELINE_VERIFIED_ONLY_SCIENTIFIC_STAGE03_NOT_COMPLETE")
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(proof, sort_keys=True, indent=2) + "\n")
    tmp.replace(OUTPUT)
    print("ALL PASS|OMEGA_STAGE03_SYNTH_ENGINEERING|BARS=" + str(len(bars)) +
          "|TRADES=" + str(a[1]) + "|REPEAT=2|COST_ARITHMETIC=PASS|SEARCH=NO|ORDERS=NO")


if __name__ == "__main__":
    main()
