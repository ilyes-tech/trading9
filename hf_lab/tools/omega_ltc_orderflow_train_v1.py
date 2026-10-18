"""One bounded LTCUSD Kraken spot order-flow LONG-only historical screening.

Internal exploratory TRAIN (March 2026) only, one frozen hypothesis, one run.
NOT scientific admission, tradeable net PF, Searcher, demo, real orders, or
permission to use reserved Apr-Jun data.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path

from hf_lab.signed_volume import closed_m1_imbalance
from hf_lab.tools.omega_train_scope_gate_v1 import ROOT, STATE, preflight

FILE = ROOT / "historical/kraken_micro_m1/extracted/LTCUSD_MICRO_2026_03_M1.csv"
SOURCE_SHA = "98572df467cef708d57592a5454a2225f9f0f647f236c194976e8216d4ebee0a"
SOURCE_ROWS = 44640
START = 1772323200  # March 1 2026, 00:00:00 UTC
END = 1775001600  # April 1 2026, 00:00:00 UTC -- never open this date or later
HOLD_BARS = 15
ENTRY_DELAY_MINUTES = 2
COST_BPS = 162.0  # illustrative Oct 2026 Kraken Pro tier1 80bps each side +1bps slip each
CANDIDATE = "LTCUSD_KRAKEN_CLOSED_M1_TAKER_BUY_DOMINANCE_LONG_15M_V1"
CLAIM = STATE / "stage03_ltc_flow_train_v1.claim"
REPORT = STATE / "stage03_ltc_flow_train_v1.json"
HEADERS = ["time","open","high","low","close","volume","trades","buy_volume",
           "sell_volume","buy_trades","sell_trades","market_volume",
           "limit_volume","market_trades","limit_trades"]


def validate_scope(root: Path, state: Path) -> None:
    # Existing global scientific/search gates remain DENIED; this is independent
    # and may never set an AUTHORIZED flag in those gates.
    preflight(root, state, inspect_train_bytes=False)
    previous = state / "stage03_btc_eth_internal_train_screen_decision_v1.json"
    if not previous.is_file() or previous.is_symlink():
        raise ValueError("PRIOR_TRAIN_DECISION_MISSING")
    d = json.loads(previous.read_bytes())
    if (d.get("decision") != "REJECT_CANDIDATE_AT_INDICATIVE_122BPS_COST_SCREEN"
            or d.get("scientific_admission") is not False
            or d.get("candidate") == CANDIDATE):
        raise ValueError("PREVIOUS_REJECT_NOT_RECORDED")
    if HOLD_BARS != 15 or ENTRY_DELAY_MINUTES != 2 or COST_BPS != 162.0:
        raise ValueError("FROZEN_DESIGN_CHANGED")


def read_march(root: Path) -> tuple[dict, ...]:
    p = root / "historical/kraken_micro_m1/extracted/LTCUSD_MICRO_2026_03_M1.csv"
    state = Path(str(p) + ".state.json")
    if p.is_symlink() or state.is_symlink() or not p.is_file() or not state.is_file():
        raise ValueError("TRAIN_SOURCE_NOT_REGULAR")
    metadata = json.loads(state.read_bytes())
    if (metadata.get("sha256") != SOURCE_SHA or metadata.get("bars") != SOURCE_ROWS
            or metadata.get("pair") != "LTCUSD"
            or metadata.get("start") != "2026-03-01T00:00:00+00:00"
            or metadata.get("end_exclusive") != "2026-04-01T00:00:00+00:00"):
        raise ValueError("TRAIN_SOURCE_MANIFEST_CHANGED")
    raw = p.read_bytes()  # TRAIN March only; no other file is ever opened.
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("TRAIN_SOURCE_SHA256_CHANGED")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    if reader.fieldnames != HEADERS:
        raise ValueError("TRAIN_SOURCE_SCHEMA_CHANGED")
    rows = []
    for index, rec in enumerate(reader):
        if index >= SOURCE_ROWS:
            raise ValueError("TRAIN_SOURCE_TOO_MANY_ROWS")
        try:
            t = int(rec["time"])
            o,h,l,c = (float(rec[k]) for k in ("open","high","low","close"))
            v, buy, sell = (float(rec[k]) for k in ("volume","buy_volume","sell_volume"))
            trades = int(rec["trades"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("TRAIN_SOURCE_INVALID_ROW") from exc
        if (t != START + index*60 or not START <= t < END
                or not all(math.isfinite(x) for x in (o,h,l,c,v,buy,sell))
                or min(o,h,l,c) <= 0 or h < max(o,c) or l > min(o,c)
                or v < 0 or buy < 0 or sell < 0 or trades < 0):
            raise ValueError("TRAIN_SOURCE_TIME_OR_VALUE_FAILURE")
        rows.append({"time":t, "open":o, "close":c, "volume":v,
                     "buy":buy, "sell":sell, "trades":trades})
    if len(rows) != SOURCE_ROWS:
        raise ValueError("TRAIN_SOURCE_TRUNCATED")
    return tuple(rows)


def summarize(pnl: list[float], count: int, missing: int) -> dict:
    gains = math.fsum(v for v in pnl if v > 0)
    losses = -math.fsum(v for v in pnl if v < 0)
    # These samples exclude entry/exit periods based on FUTURE trade activity;
    # they are post-hoc *label coverage*, not ex-ante executable positions.
    # No subsequent system may promote this conditional proxy into a live PF.
    gross_sum = math.fsum(pnl) + len(pnl) * COST_BPS
    return {
        "signal_or_baseline_schedules": count,
        "scored_roundtrips": len(pnl),
        "unscorable_zero_trade_entry_or_exit": missing,
        "selection_conditioned_on_future_entry_exit_trade_activity": missing > 0,
        "sample_not_valid_for_ex_ante_execution_pf": True,
        "assumed_roundtrip_cost_bps": COST_BPS,
        "gross_log_return_bps_sum_in_scored_subset": round(gross_sum, 4),
        "mean_gross_bps_in_scored_subset": round(gross_sum / len(pnl), 6) if pnl else None,
        "mean_net_bps_in_scored_subset": round(math.fsum(pnl) / len(pnl), 6) if pnl else None,
        "net_log_return_bps_sum": round(math.fsum(pnl), 4),
        "proxy_net_pf": round(gains / losses, 8) if losses > 0 else None,
        "actual_executable_net_pf_verified": False,
    }


def screen(rows: tuple[dict, ...]) -> dict:
    if len(rows) < 17:
        raise ValueError("TRAIN_INSUFFICIENT")
    actual, baseline = [], []
    signals = baseline_schedules = actual_missing = baseline_missing = 0
    # Signal at M1 close (t+60s); wait one full additional minute;
    # enter on bar t+120s open, exit after 15 M1 bars at t+1020s.
    # A trade consumes future holding time; no overlapping trade decisions.
    i = 0
    last_signal = len(rows) - (ENTRY_DELAY_MINUTES + HOLD_BARS - 1)
    while i < last_signal:
        r = rows[i]
        imbalance = closed_m1_imbalance(
            bar_start=r["time"], as_of=r["time"] + 60,
            buy_volume=r["buy"], sell_volume=r["sell"]
        )
        if r["trades"] <= 0 or imbalance is None or imbalance <= 0:
            i += 1
            continue
        signals += 1
        entry_i = i + ENTRY_DELAY_MINUTES
        exit_i = entry_i + HOLD_BARS - 1
        entry, exit = rows[entry_i], rows[exit_i]
        if (entry["time"] != r["time"] + ENTRY_DELAY_MINUTES*60
                or exit["time"] != entry["time"] + (HOLD_BARS-1)*60):
            raise ValueError("NO_CAUSAL_ENTRY_EXIT_CLOCK")
        if entry["trades"] <= 0 or exit["trades"] <= 0:
            actual_missing += 1
        else:
            actual.append(10000 * math.log(exit["close"]/entry["open"]) - COST_BPS)
        i = exit_i + 1
    for j in range(0, last_signal, ENTRY_DELAY_MINUTES + HOLD_BARS):
        baseline_schedules += 1
        entry, exit = rows[j + ENTRY_DELAY_MINUTES], rows[j + ENTRY_DELAY_MINUTES + HOLD_BARS - 1]
        if entry["trades"] <= 0 or exit["trades"] <= 0:
            baseline_missing += 1
        else:
            baseline.append(10000 * math.log(exit["close"]/entry["open"]) - COST_BPS)
    return {
        "candidate": summarize(actual, signals, actual_missing),
        "fixed_cadence_unconditional_long_control": summarize(
            baseline, baseline_schedules, baseline_missing),
        "train_rows": len(rows),
        "rule": "closed M1 buy_volume > sell_volume and trades>0; LONG-only",
        "entry": "minute t+120s open; after fully closed t bar plus 60s buffer",
        "exit": "close of 15th bar (t+960s start), nonoverlapping",
        "holdout_or_future_months_read": False,
        "fees_broker_verified": False,
        "source_market_is_spot": True,
    }


def run_once(root: Path = ROOT, state: Path = STATE) -> dict:
    validate_scope(root, state)
    claim, output = state / CLAIM.name, state / REPORT.name
    if claim.exists() or claim.is_symlink() or output.exists() or output.is_symlink():
        raise ValueError("SINGLE_SHOT_ALREADY_CONSUMED")
    # Write atomic claim BEFORE opening March prices; an interrupted attempt
    # cannot silently repeat the same hypothesis.
    fd = os.open(claim, os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(json.dumps({
            "candidate":CANDIDATE, "source_sha256":SOURCE_SHA,
            "status":"CONSUMED_ONCE", "orders_allowed":False, "holdout_allowed":False}) + "\n")
    diagnostics = screen(read_march(root))
    report = {
        "kind":"OMEGA_LTC_M1_INTERNAL_TRAIN_ONLY_SCREEN_V1",
        "status":"RETROSPECTIVE_TRAIN_SCREEN_ONLY_NO_SCIENTIFIC_ADMISSION",
        "candidate":CANDIDATE, "candidate_budget":1, "parameter_variants":1,
        "market":"LTCUSD", "venue":"Kraken spot",
        "train_scope":"March 2026 alone; April-June never opened",
        "train_source_sha256":SOURCE_SHA,
        "costs":"Illustrative Oct 2026 public tier1 taker 80bps/side + 1bps/side slippage =162bps; no account fee/2026-March spread calibration",
        "cost_source":"https://www.kraken.com/features/fee-schedule",
        "execution_mapping_verified":False, "scientific_admission":False,
        "new_candidate_admitted":False, "searcher_executed":False,
        "orders_allowed":False, "mt5_allowed":False, "holdout_read":False,
        "holdout_allowed":False, "auto_promotion_allowed":False,
        "diagnostics":diagnostics,
    }
    temp=state/(REPORT.name+".tmp")
    temp.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    temp.replace(output)
    return report


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-one-internal-train-only",action="store_true")
    args=parser.parse_args()
    if not args.run_one_internal_train_only:
        raise SystemExit("DENIED|EXPLICIT_SINGLE_SHOT_INTERNAL_PERMISSION_REQUIRED")
    report=run_once()
    print("PASS|LTC_MARCH_ONE_TRAIN_SCREEN|PF="+str(report["diagnostics"]["candidate"]["proxy_net_pf"])+"|SEARCHER=NO|ORDERS=NO|HOLDOUT=NO")


if __name__ == "__main__":
    main()
