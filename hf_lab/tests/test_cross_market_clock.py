"""Synthetic-only timing tests; NEVER read market data or run a backtest."""
from datetime import datetime, timedelta, timezone
from dataclasses import replace

import pytest

from hf_lab.replay import Bar
from hf_lab.cross_market_clock import aligned_four_minute_pairs, causal_signal_clocks, review_only_closed_bar_directions


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


def test_live_decision_clock_requires_no_future_label_bar():
    btc = bars([0, 1])
    eth = bars([0, 1])
    signals = causal_signal_clocks(btc, eth)
    assert len(signals) == 1
    first = signals[0]
    assert first.decision_time == START + timedelta(minutes=2)
    assert first.earliest_proxy_entry_time == START + timedelta(minutes=3)
    assert first.btc_signal == first.eth_signal == 1
    # Historical label coverage must NOT determine the signal decision.
    assert aligned_four_minute_pairs(btc, eth) == ()


def test_future_candles_cannot_remove_or_change_past_decisions():
    original = causal_signal_clocks(bars([0, 1, 2]), bars([0, 1, 2]))
    extended = causal_signal_clocks(
        bars([0, 1, 2, 3, 4, 5]),
        bars([0, 1, 2, 4, 5]),
    )
    assert len(original) == 2
    assert extended[:2] == original


def test_historical_label_gap_does_not_remove_past_signal():
    btc = bars([0, 1, 2, 3])
    eth = bars([0, 1, 3])
    times = [d.decision_time for d in causal_signal_clocks(btc, eth)]
    assert times == [START + timedelta(minutes=2)]
    assert aligned_four_minute_pairs(btc, eth) == ()


def test_future_price_mutation_does_not_change_decision_schedule():
    original = bars(range(6))
    changed = [replace(b, high=10**10, close=10**10) for b in original]
    assert causal_signal_clocks(original, original) == causal_signal_clocks(changed, original)


def test_invalid_timestamps_fail_closed_for_signal_clock():
    with pytest.raises(ValueError):
        causal_signal_clocks(bars([0, 0, 1]), bars([0, 1]))
    missing_tz = bars([0, 1])
    missing_tz[1] = replace(missing_tz[1], time=datetime(2026, 1, 1, 0, 1))
    with pytest.raises(ValueError):
        causal_signal_clocks(missing_tz, bars([0, 1]))


def test_synthetic_closed_bar_probe_uses_prior_btc_and_eth_control():
    btc = bars([0, 1])
    eth = bars([0, 1])
    btc[0] = replace(btc[0], close=100.)
    btc[1] = replace(btc[1], close=101.)
    eth[0] = replace(eth[0], close=100.)
    eth[1] = replace(eth[1], close=99.)
    clock = causal_signal_clocks(btc, eth)[0]
    result = review_only_closed_bar_directions(clock, btc, eth)
    assert result.btc_direction == 1
    assert result.eth_self_control_direction == -1
    assert result.decision_time == START + timedelta(minutes=2)
    assert result.earliest_proxy_entry_time == START + timedelta(minutes=3)


def test_synthetic_no_change_is_no_signal():
    btc = bars([0, 1])
    eth = bars([0, 1])
    signal = review_only_closed_bar_directions(causal_signal_clocks(btc, eth)[0], btc, eth)
    assert signal.btc_direction == 0
    assert signal.eth_self_control_direction == 0


def test_future_prices_and_labels_cannot_change_closed_probe():
    original = bars(range(5))
    clock = causal_signal_clocks(original[:2], original[:2])[0]
    expected = review_only_closed_bar_directions(clock, original, original)
    altered = list(original)
    for i in (2, 3, 4):
        altered[i] = replace(altered[i], close=1000000., open=9999., high=1000001.)
    assert review_only_closed_bar_directions(clock, altered, original) == expected
    assert review_only_closed_bar_directions(clock, original, altered) == expected


def test_bad_synthetic_prices_and_temporal_offsets_fail_closed():
    base = bars([0, 1])
    clock = causal_signal_clocks(base, base)[0]
    for value in (0., -1., float('nan'), float('inf'), -float('inf')):
        bad = [replace(base[0], close=value), base[1]]
        with pytest.raises(ValueError):
            review_only_closed_bar_directions(clock, bad, base)
    for field, value in (('decision_time', START + timedelta(minutes=1)),
                         ('earliest_proxy_entry_time', START + timedelta(minutes=2)),
                         ('btc_signal', 0), ('eth_prior', -1)):
        with pytest.raises(ValueError):
            review_only_closed_bar_directions(replace(clock, **{field:value}), base, base)
