"""Synthetic-only timing tests; NEVER read market data or run a backtest."""
from datetime import datetime, timedelta, timezone
from dataclasses import replace

import pytest

from hf_lab.replay import Bar
from hf_lab.cross_market_clock import aligned_four_minute_pairs


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def bars(minutes):
    return [Bar(time=START + timedelta(minutes=m), open=100.0,
                high=101.0, low=99.0, close=100.5)
            for m in minutes]


def test_four_minute_clock_and_one_minute_processing_delay():
    windows = aligned_four_minute_pairs(bars(range(6)), bars(range(6)))
    assert len(windows) == 3
    first = windows[0]
    assert first.decision_time == START + timedelta(minutes=2)
    assert (first.btc_prior, first.btc_signal) == (0, 1)
    assert (first.eth_prior, first.eth_signal) == (0, 1)
    assert (first.eth_entry, first.eth_exit) == (3, 3)
    assert START + timedelta(minutes=3) >= first.decision_time
    assert windows[-1].eth_entry == 5


def test_no_cross_market_gap_leakage():
    left = bars([0, 1, 2, 3, 4, 5, 6, 7])
    right = bars([0, 1, 2, 4, 5, 6, 7])
    windows = aligned_four_minute_pairs(left, right)
    assert [x.decision_time for x in windows] == [
        START + timedelta(minutes=6)
    ]


@pytest.mark.parametrize("series", ([0, 1, 1, 2, 3], [0, 2, 1, 3], [3, 2, 1, 0]))
def test_duplicate_and_unsorted_times_fail_closed(series):
    with pytest.raises(ValueError):
        aligned_four_minute_pairs(bars(series), bars(range(6)))


def test_naive_and_subminute_times_fail_closed():
    for bad_time in (datetime(2026, 1, 1),
                     START + timedelta(seconds=1)):
        bad = bars(range(6))
        bad[0] = replace(bad[0], time=bad_time)
        with pytest.raises(ValueError):
            aligned_four_minute_pairs(bad, bars(range(6)))


def test_price_mutations_cannot_change_alignment():
    source = bars(range(6))
    changed = [replace(b, close=999999.0) for b in source]
    assert aligned_four_minute_pairs(source, source) == aligned_four_minute_pairs(changed, source)
