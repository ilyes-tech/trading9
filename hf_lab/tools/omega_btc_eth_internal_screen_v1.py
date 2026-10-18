"""Single-shot historical TRAIN-only feasibility screen; NOT JARVIS scientific admission.

An operator must explicitly invoke the bounded opt-in command. It preserves the
existing DENIED production/search gates, consumes no final validation/holdout,
does not optimize parameters or grant trading, and refuses any repeat.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

from hf_lab.cross_market_clock import (
    aligned_four_minute_pairs, causal_signal_clocks, review_only_closed_bar_directions,
)
from hf_lab.replay import Bar
from hf_lab.tools.omega_train_scope_gate_v1 import (
    ROOT, STATE, ROWS, preflight,
)

CLAIM = STATE / "stage03_btc_eth_internal_train_screen_v1.claim"
REPORT = STATE / "stage03_btc_eth_internal_train_screen_v1.json"
COST_BPS = 122.0
SOURCE_FIELDS = ["time", "datetime", "open", "high", "low", "close", "vwap",
                 "volume", "trades", "source"]


def read_pinned_train(root: Path, market: str, expected_sha: str) -> tuple[Bar, ...]:
    """Unbuffered, EXACT declared number of lines. Never read beyond train prefix."""
    if market not in ROWS:
        raise ValueError("MARKET_NOT_ALLOWLISTED")
    path = root / "data" / "coinbase_m1_q4_2025" / (market + "_M1.csv")
    if path.is_symlink() or not path.is_file():
        raise ValueError("SOURCE_NOT_REGULAR_FILE")
    digest = hashlib.sha256()
    bars = []
    previous_time = None
    with path.open("rb", buffering=0) as source:
        header = source.readline()
        digest.update(header)
        if next(csv.reader([header.decode("utf-8")])) != SOURCE_FIELDS:
            raise ValueError("UNEXPECTED_TRAIN_SCHEMA")
        for _ in range(ROWS[market]):
            line = source.readline()
            if not line:
                raise ValueError("TRAIN_TRUNCATED")
            digest.update(line)
            fields = next(csv.reader([line.decode("utf-8")]))
            if len(fields) != len(SOURCE_FIELDS):
                raise ValueError("MALFORMED_TRAIN_ROW")
            row = dict(zip(SOURCE_FIELDS, fields))
            t = datetime.fromtimestamp(int(row["time"]), tz=timezone.utc)
            documented_time = datetime.fromisoformat(row["datetime"].replace("Z", "+00:00"))
            if (documented_time.utcoffset() is None
                    or documented_time.astimezone(timezone.utc) != t
                    or int(t.timestamp()) % 60
                    or (previous_time is not None and t <= previous_time)):
                raise ValueError("INVALID_TRAIN_TIMESTAMP")
            previous_time = t
            op, hi, lo, cl = (float(row[name]) for name in ("open", "high", "low", "close"))
            if (not all(math.isfinite(value) and value > 0 for value in (op, hi, lo, cl))
                    or lo > min(op, cl) or hi < max(op, cl)):
                raise ValueError("INVALID_TRAIN_OHLC")
            bars.append(Bar(time=t, open=op, high=hi, low=lo, close=cl))
    if digest.hexdigest() != expected_sha:
        raise ValueError("TRAIN_SHA256_MISMATCH")
    return tuple(bars)


def _stats(net_bps: list[float], wins_direction: int) -> dict:
    gains = math.fsum(v for v in net_bps if v > 0)
    losses = -math.fsum(v for v in net_bps if v < 0)
    running, maximum, dd = 0.0, 0.0, 0.0
    for value in net_bps:
        running += value
        maximum = max(maximum, running)
        dd = max(dd, maximum - running)
    return {
        "observations": len(net_bps),
        "directional_positive_gross_count": wins_direction,
        "cost_screen_roundtrip_bps": COST_BPS,
        "cost_screen_net_bps_sum": round(math.fsum(net_bps), 4),
        "cost_screen_proxy_pf": round(gains / losses, 8) if losses > 0 else None,
        "cost_screen_max_drawdown_bps": round(dd, 4),
        "venue_executable_net_pf_verified": False,
        "scientific_admission": False,
    }


def screen(btc: tuple[Bar, ...], eth: tuple[Bar, ...]) -> dict:
    """Score a single frozen direction rule and matched ETH-own-lag control."""
    decisions = causal_signal_clocks(btc, eth)
    windows = aligned_four_minute_pairs(btc, eth)
    by_time = {d.decision_time: d for d in decisions}
    if not decisions or not windows or len(by_time) != len(decisions):
        raise ValueError("INVALID_TRAIN_DECISION_CLOCK")
    pnl = {"btc_lag": [], "eth_lag_control": []}
    correct = {"btc_lag": 0, "eth_lag_control": 0}
    skipped = {"btc_lag": 0, "eth_lag_control": 0}
    for pair in windows:
        # Signal is defined independently of future label availability.
        signal = review_only_closed_bar_directions(by_time[pair.decision_time], btc, eth)
        entry = eth[pair.eth_entry]
        if entry.time != signal.earliest_proxy_entry_time:
            raise ValueError("LABEL_TIME_LEAK_OR_MISALIGNMENT")
        future_bps = 10000 * math.log(entry.close / entry.open)
        for name, direction in (("btc_lag", signal.btc_direction),
                                ("eth_lag_control", signal.eth_self_control_direction)):
            if direction == 0:
                skipped[name] += 1
                continue
            gross = direction * future_bps
            correct[name] += gross > 0
            pnl[name].append(gross - COST_BPS)
    return {
        "past_only_decisions": len(decisions),
        "retrospective_labeled_windows": len(windows),
        "unlabeled_or_missing_future_decisions": len(decisions) - len(windows),
        "zero_signal_windows": skipped,
        "btc_lag": _stats(pnl["btc_lag"], correct["btc_lag"]),
        "eth_lag_control": _stats(pnl["eth_lag_control"], correct["eth_lag_control"]),
        "spot_short_executable": False,
        "actual_broker_costs_verified": False,
        "result_is_train_only_posthoc": True,
    }


def run_once(root: Path = ROOT, state: Path = STATE) -> dict:
    scope = preflight(root, state, inspect_train_bytes=True)
    claim = state / CLAIM.name
    result_file = state / REPORT.name
    if claim.exists() or claim.is_symlink() or result_file.exists() or result_file.is_symlink():
        raise ValueError("SINGLE_USE_ALREADY_CONSUMED")
    # Atomic claim BEFORE reading any OHLC; never silently replay after a crash.
    fd = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps({"kind": "INTERNAL_TRAIN_ONLY_USER_APPROVED_ONE_SHOT",
                                 "scientific_admission": False, "orders_allowed": False,
                                 "holdout_allowed": False}) + "\n")
    btc = read_pinned_train(root, "BTCUSD", scope["verified_train_prefix_sha256"]["BTCUSD"])
    eth = read_pinned_train(root, "ETHUSD", scope["verified_train_prefix_sha256"]["ETHUSD"])
    values = screen(btc, eth)
    report = {
        "kind": "OMEGA_BTC_ETH_INTERNAL_TRAIN_SCREEN_V1",
        "status": "TRAIN_EXPLORATION_ONLY_NOT_SCIENTIFIC_ADMISSION",
        "candidate": "BTC_TO_ETH_ONE_MINUTE_DELAY_DIRECTION_BASELINE_V1",
        "candidate_budget": 1, "parameter_variants": 1,
        "train_prefix_sha256": scope["verified_train_prefix_sha256"],
        "data_source": "Coinbase Exchange BTC-USD ETH-USD 2025-Q4 60pct training prefix",
        "cost_note": "122bps indicative taker fees+slippage, excludes variable spread, market impact, venue mapping; shorts not executable on unleveraged spot",
        "performance_claim": "Retrospective exploratory cost screen, NOT out-of-sample PF or tradable net PF",
        "scientific_admission": False, "new_candidate_admitted": False,
        "searcher_executed": False, "orders_allowed": False, "mt5_allowed": False,
        "holdout_read": False, "holdout_allowed": False,
        "auto_promotion_allowed": False, "diagnostics": values,
    }
    tmp = state / (REPORT.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    tmp.replace(result_file)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorize-one-internal-train-screen", action="store_true")
    args = parser.parse_args()
    if not args.authorize_one_internal_train_screen:
        raise SystemExit("DENIED|EXPLICIT_INTERNAL_TRAIN_SCREEN_INTENT_REQUIRED")
    report = run_once()
    print("PASS|ONE_TRAIN_EXPLORATION|BTC_PF_COST_SCREEN="
          + str(report["diagnostics"]["btc_lag"]["cost_screen_proxy_pf"])
          + "|NO_ADMISSION|NO_SEARCHER|NO_ORDERS|NO_HOLDOUT")


if __name__ == "__main__":
    main()
