"""Pure BTC/ETH M1 clock alignment for a REVIEW-ONLY research protocol.

No market data loading, return calculation, strategy scoring, or orders.
A scientific execution gate is still required before using a window in a backtest.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from hf_lab.replay import Bar


@dataclass(frozen=True, slots=True)
class FourMinutePair:
    decision_time: datetime
    btc_prior: int
    btc_signal: int
    eth_prior: int
    eth_signal: int
    eth_entry: int
    eth_exit: int


def _minute_indices(bars: Sequence[Bar]) -> dict[int, int]:
    positions: dict[int, int] = {}
    previous: int | None = None
    for index, bar in enumerate(bars):
        stamp = bar.time
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("Bar timestamps must carry a timezone")
        utc = stamp.astimezone(timezone.utc)
        epoch = utc.timestamp()
        if not epoch.is_integer() or int(epoch) % 60:
            raise ValueError("Bar timestamps must be UTC-minute aligned")
        minute = int(epoch)
        if previous is not None and minute <= previous:
            raise ValueError("Bars must have unique increasing minute timestamps")
        positions[minute] = index
        previous = minute
    return positions


@dataclass(frozen=True, slots=True)
class CausalSignalClock:
    """Signal decision using only two *already closed* bars on each market."""

    decision_time: datetime
    earliest_proxy_entry_time: datetime
    btc_prior: int
    btc_signal: int
    eth_prior: int
    eth_signal: int


def causal_signal_clocks(
    btc_bars: Sequence[Bar], eth_bars: Sequence[Bar]
) -> tuple[CausalSignalClock, ...]:
    """Return decision clocks, independent of all future label availability.

    For a bar starting at t, both markets' t and t-60s bars must exist.
    Signals become available only after the t bar closes at t+60s.
    The earliest conservative proxy entry is scheduled at t+120s.
    No future timestamp, price, outcome or target bar is consulted.
    This function computes NO market signal and grants NO execution rights.
    """
    btc = _minute_indices(btc_bars)
    eth = _minute_indices(eth_bars)
    common = btc.keys() & eth.keys()
    decisions: list[CausalSignalClock] = []
    for t in sorted(common):
        if t - 60 not in common:
            continue
        decisions.append(CausalSignalClock(
            decision_time=datetime.fromtimestamp(t + 60, tz=timezone.utc),
            earliest_proxy_entry_time=datetime.fromtimestamp(t + 120, tz=timezone.utc),
            btc_prior=btc[t - 60],
            btc_signal=btc[t],
            eth_prior=eth[t - 60],
            eth_signal=eth[t],
        ))
    return tuple(decisions)


def aligned_four_minute_pairs(
    btc_bars: Sequence[Bar], eth_bars: Sequence[Bar]
) -> tuple[FourMinutePair, ...]:
    """Align four *existing* consecutive minute starts across both markets.

    For anchor t: BTC signal closes at t+60s, decision at t+60s,
    proxy ETH entry at t+120s, proxy ETH exit at t+180s.
    Only returns indices; never reads bar prices or scores outcomes.

    IMPORTANT: availability of the t+120 label bar is future information.
    Therefore this function is ONLY an offline label-coverage alignment;
    using the presence/absence of a returned window as a live entry filter
    would be lookahead leakage. Never reuse it to authorize a real signal.
    """
    btc = _minute_indices(btc_bars)
    eth = _minute_indices(eth_bars)
    common = btc.keys() & eth.keys()
    result: list[FourMinutePair] = []
    for t in sorted(common):
        if not all(t + dt in common for dt in (-60, 0, 60, 120)):
            continue
        result.append(FourMinutePair(
            decision_time=datetime.fromtimestamp(t + 60, tz=timezone.utc),
            btc_prior=btc[t - 60],
            btc_signal=btc[t],
            eth_prior=eth[t - 60],
            eth_signal=eth[t],
            eth_entry=eth[t + 120],
            eth_exit=eth[t + 120],
        ))
    return tuple(result)
