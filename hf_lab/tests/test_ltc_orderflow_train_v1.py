"""Synthetic-only contract tests: no actual Kraken price reads."""
from copy import deepcopy
from pathlib import Path
import json

import pytest

from hf_lab.tools import omega_ltc_orderflow_train_v1 as m


def synth(n=38):
    base=m.START
    return tuple({
        "time":base+i*60, "open":100.0,
        "close":102.0 if i % 5 == 1 else 100.0,
        "volume":3.0, "buy":2.0, "sell":1.0, "trades":2,
    } for i in range(n))


def test_frozen_long_only_and_nonoverlapping():
    report=m.screen(synth(40))
    assert report["rule"].endswith("LONG-only")
    assert report["candidate"]["signal_or_baseline_schedules"] == 2
    assert report["candidate"]["scored_roundtrips"] == 2
    assert report["train_rows"]==40
    assert report["holdout_or_future_months_read"] is False
    assert report["source_market_is_spot"] is True
    assert report["candidate"]["actual_executable_net_pf_verified"] is False
    assert report["candidate"]["sample_not_valid_for_ex_ante_execution_pf"] is True
    candidate = report["candidate"]
    assert abs(candidate["mean_net_bps_in_scored_subset"]
               - (candidate["mean_gross_bps_in_scored_subset"] - m.COST_BPS)) < 0.000002


def test_future_price_cannot_change_past_signal_scheduling():
    original=synth(40)
    changed=list(deepcopy(original))
    for j in range(2, 40):
        changed[j]["close"]=changed[j]["close"]*1.01
        changed[j]["open"]=changed[j]["open"]*1.01
    a=m.screen(original)
    b=m.screen(tuple(changed))
    assert a["candidate"]["signal_or_baseline_schedules"]==b["candidate"]["signal_or_baseline_schedules"]
    assert a["candidate"]["scored_roundtrips"]==b["candidate"]["scored_roundtrips"]


def test_no_buy_imbalance_gives_no_trades():
    rows=[dict(r, buy=0, sell=2) for r in synth()]
    report=m.screen(tuple(rows))
    assert report["candidate"]["signal_or_baseline_schedules"]==0
    assert report["candidate"]["scored_roundtrips"]==0


def test_zero_volume_is_not_trading_signal():
    rows=list(synth(17))
    rows[0]=dict(rows[0],buy=0,sell=0,trades=0)
    assert m.screen(tuple(rows))["candidate"]["signal_or_baseline_schedules"] == 0
    assert m.screen(synth(17))["candidate"]["signal_or_baseline_schedules"] == 1


def test_future_nontrade_data_not_used_to_choose_signal():
    rows=list(synth(38))
    rows[2]=dict(rows[2],trades=0)
    a=m.screen(synth(38))
    b=m.screen(tuple(rows))
    assert a["candidate"]["signal_or_baseline_schedules"]==b["candidate"]["signal_or_baseline_schedules"]
    assert b["candidate"]["unscorable_zero_trade_entry_or_exit"]>=1
    assert b["candidate"]["selection_conditioned_on_future_entry_exit_trade_activity"] is True
    assert b["candidate"]["sample_not_valid_for_ex_ante_execution_pf"] is True


def test_reject_short_source_and_missing_prior_review(tmp_path, monkeypatch):
    monkeypatch.setattr(m,"preflight",lambda *a,**kw: None)
    with pytest.raises(ValueError,match="PRIOR_TRAIN_DECISION_MISSING"):
        m.validate_scope(tmp_path,tmp_path)


def test_single_use_and_no_auto_promotion(tmp_path,monkeypatch):
    monkeypatch.setattr(m,"validate_scope",lambda *a,**kw:None)
    monkeypatch.setattr(m,"read_march",lambda *a,**kw:synth(38))
    a=m.run_once(tmp_path,tmp_path)
    p=tmp_path/m.REPORT.name
    assert p.exists()
    assert json.loads(p.read_text())==a
    assert a["candidate_budget"]==1 and a["parameter_variants"]==1
    assert a["scientific_admission"] is False
    assert a["auto_promotion_allowed"] is False
    assert a["orders_allowed"] is False and a["mt5_allowed"] is False
    assert a["holdout_read"] is False and a["searcher_executed"] is False
    assert (tmp_path/m.CLAIM.name).exists()
    with pytest.raises(ValueError,match="SINGLE_SHOT_ALREADY_CONSUMED"):
        m.run_once(tmp_path,tmp_path)


def test_bad_row_count_fail_closed():
    with pytest.raises(ValueError,match="TRAIN_INSUFFICIENT"):
        m.screen(synth(16))
