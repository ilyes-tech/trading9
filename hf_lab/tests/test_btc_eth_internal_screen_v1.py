"""Synthetic-only verification of the isolated one-shot internal screen."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

import pytest

from hf_lab.replay import Bar
from hf_lab.tools import omega_btc_eth_internal_screen_v1 as internal

T = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bars(prices: list[tuple[float, float]]) -> tuple[Bar, ...]:
    return tuple(
        Bar(time=T + timedelta(minutes=i), open=op, high=max(op, cl),
            low=min(op, cl), close=cl)
        for i, (op, cl) in enumerate(prices)
    )


def test_fixed_direction_and_control_are_scored_without_fitting():
    btc = bars([(100, 100), (100, 101), (101, 100),
                (100, 100), (100, 100), (100, 100)])
    eth = bars([(100, 100), (100, 99), (99, 99),
                (99, 101), (101, 100), (100, 100)])
    report = internal.screen(btc, eth)
    assert report["past_only_decisions"] == 5
    assert report["retrospective_labeled_windows"] == 3
    assert report["unlabeled_or_missing_future_decisions"] == 2
    assert report["btc_lag"]["observations"] >= 1
    assert report["eth_lag_control"]["observations"] >= 1
    assert report["spot_short_executable"] is False
    assert report["actual_broker_costs_verified"] is False
    assert report["result_is_train_only_posthoc"] is True


def test_no_score_when_future_label_is_missing():
    btc = bars([(100, 100), (100, 101)])
    eth = bars([(100, 100), (100, 99)])
    with pytest.raises(ValueError, match="INVALID_TRAIN_DECISION_CLOCK"):
        internal.screen(btc, eth)


def test_gap_does_not_create_fake_label():
    btc = bars([(100, 100), (100, 101), (100, 102),
                (100, 100), (100, 100)])
    eth = tuple(bar for i, bar in enumerate(btc) if i != 3)
    with pytest.raises(ValueError, match="INVALID_TRAIN_DECISION_CLOCK"):
        internal.screen(btc, eth)


def test_unapproved_market_name_denied_before_file_open(tmp_path):
    with pytest.raises(ValueError, match="MARKET_NOT_ALLOWLISTED"):
        internal.read_pinned_train(tmp_path, "XAUUSD", "irrelevant")


def test_symlinked_source_denied(tmp_path):
    parent = tmp_path / "data" / "coinbase_m1_q4_2025"
    parent.mkdir(parents=True)
    real = parent / "original.csv"
    real.write_text("irrelevant")
    (parent / "BTCUSD_M1.csv").symlink_to(real)
    with pytest.raises(ValueError, match="SOURCE_NOT_REGULAR_FILE"):
        internal.read_pinned_train(tmp_path, "BTCUSD", "x")


def test_existing_claim_refuses_repeat_before_any_price_read(tmp_path, monkeypatch):
    monkeypatch.setattr(internal, "preflight", lambda *args, **kwargs: {
        "verified_train_prefix_sha256": {"BTCUSD": "a", "ETHUSD": "b"}
    })
    (tmp_path / internal.CLAIM.name).write_text("claimed")
    monkeypatch.setattr(internal, "read_pinned_train", lambda *args: pytest.fail("price read"))
    with pytest.raises(ValueError, match="SINGLE_USE_ALREADY_CONSUMED"):
        internal.run_once(tmp_path, tmp_path)


def test_existing_result_refuses_repeat_before_any_price_read(tmp_path, monkeypatch):
    monkeypatch.setattr(internal, "preflight", lambda *args, **kwargs: {
        "verified_train_prefix_sha256": {"BTCUSD": "a", "ETHUSD": "b"}
    })
    (tmp_path / internal.REPORT.name).write_text("already resulted")
    monkeypatch.setattr(internal, "read_pinned_train", lambda *args: pytest.fail("price read"))
    with pytest.raises(ValueError, match="SINGLE_USE_ALREADY_CONSUMED"):
        internal.run_once(tmp_path, tmp_path)


def test_one_shot_result_remains_non_admitted(tmp_path, monkeypatch):
    monkeypatch.setattr(internal, "preflight", lambda *args, **kwargs: {
        "verified_train_prefix_sha256": {"BTCUSD": "a", "ETHUSD": "b"}
    })
    synthetic = bars([(100, 100), (100, 101), (100, 100),
                      (100, 102), (100, 101)])
    monkeypatch.setattr(internal, "read_pinned_train", lambda *args: synthetic)
    report = internal.run_once(tmp_path, tmp_path)
    saved = json.loads((tmp_path / internal.REPORT.name).read_text())
    assert report == saved
    assert saved["scientific_admission"] is False
    assert saved["new_candidate_admitted"] is False
    assert saved["searcher_executed"] is False
    assert saved["orders_allowed"] is False
    assert saved["holdout_read"] is False
    assert (tmp_path / internal.CLAIM.name).exists()
    with pytest.raises(ValueError, match="SINGLE_USE_ALREADY_CONSUMED"):
        internal.run_once(tmp_path, tmp_path)
