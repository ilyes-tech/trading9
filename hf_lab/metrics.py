from __future__ import annotations

from dataclasses import dataclass
from math import inf
from typing import Iterable


@dataclass(frozen=True)
class Metrics:
    trades: int
    wins: int
    losses: int

    win_rate: float
    net_r: float
    average_r: float

    profit_factor: float
    max_drawdown_r: float

    best_trade_r: float
    worst_trade_r: float


def calculate(
    net_returns: Iterable[float],
) -> Metrics:
    values = [
        float(value)
        for value in net_returns
    ]

    wins = sum(
        value > 0
        for value in values
    )

    losses = sum(
        value <= 0
        for value in values
    )

    count = len(values)

    gross_profit = sum(
        value
        for value in values
        if value > 0
    )

    gross_loss = abs(
        sum(
            value
            for value in values
            if value < 0
        )
    )

    if gross_loss > 0:
        profit_factor = (
            gross_profit
            / gross_loss
        )

    elif gross_profit > 0:
        profit_factor = inf

    else:
        profit_factor = 0.0

    equity = 0.0
    peak = 0.0
    maximum_drawdown = 0.0

    for value in values:
        equity += value
        peak = max(
            peak,
            equity,
        )

        maximum_drawdown = max(
            maximum_drawdown,
            peak - equity,
        )

    return Metrics(
        trades=count,
        wins=wins,
        losses=losses,

        win_rate=(
            wins / count
            if count
            else 0.0
        ),

        net_r=sum(values),

        average_r=(
            sum(values) / count
            if count
            else 0.0
        ),

        profit_factor=profit_factor,
        max_drawdown_r=maximum_drawdown,

        best_trade_r=(
            max(values)
            if values
            else 0.0
        ),

        worst_trade_r=(
            min(values)
            if values
            else 0.0
        ),
    )
