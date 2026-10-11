"""Indicateurs simples du HF Lab.

Toutes les fonctions travaillent uniquement avec l'historique visible
transmis par le moteur de replay.
"""

from __future__ import annotations

from math import sqrt
from typing import Sequence

from hf_lab.replay import Bar


def mean(
    values: Sequence[float],
) -> float:
    if not values:
        raise ValueError(
            "Impossible de calculer une moyenne vide."
        )

    return sum(values) / len(values)


def standard_deviation(
    values: Sequence[float],
) -> float:
    if not values:
        raise ValueError(
            "Impossible de calculer un écart-type vide."
        )

    average = mean(values)

    variance = mean(
        [
            (value - average) ** 2
            for value in values
        ]
    )

    return sqrt(variance)


def atr(
    history: Sequence[Bar],
    period: int = 14,
) -> float | None:
    if period <= 0:
        raise ValueError(
            "La période ATR doit être positive."
        )

    if len(history) < period + 1:
        return None

    true_ranges: list[float] = []

    start = len(history) - period

    for index in range(
        start,
        len(history),
    ):
        current = history[index]
        previous = history[index - 1]

        true_range = max(
            current.high - current.low,
            abs(
                current.high
                - previous.close
            ),
            abs(
                current.low
                - previous.close
            ),
        )

        true_ranges.append(
            true_range
        )

    value = mean(
        true_ranges
    )

    if value <= 0:
        return None

    return value


def close_zscore(
    history: Sequence[Bar],
    period: int = 20,
) -> float | None:
    if len(history) < period + 1:
        return None

    reference = [
        bar.close
        for bar in history[
            -period - 1 : -1
        ]
    ]

    deviation = standard_deviation(
        reference
    )

    if deviation <= 0:
        return None

    return (
        history[-1].close
        - mean(reference)
    ) / deviation


def average_volume(
    history: Sequence[Bar],
    period: int = 20,
) -> float | None:
    if len(history) < period + 1:
        return None

    volumes = [
        bar.volume
        for bar in history[
            -period - 1 : -1
        ]
    ]

    value = mean(
        volumes
    )

    if value <= 0:
        return None

    return value


def candle_body_ratio(
    bar: Bar,
) -> float:
    candle_range = (
        bar.high
        - bar.low
    )

    if candle_range <= 0:
        return 0.0

    return abs(
        bar.close
        - bar.open
    ) / candle_range
