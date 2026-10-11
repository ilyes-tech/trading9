"""Détection des segments chronologiques continus."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from hf_lab.replay import Bar


@dataclass(
    frozen=True,
    slots=True,
)
class SegmentRange:
    start: int
    stop: int
    gap_before_seconds: int

    @property
    def bars(self) -> int:
        return self.stop - self.start


def contiguous_segment_ranges(
    bars: Sequence[Bar],
    *,
    expected_interval_seconds: int = 60,
) -> tuple[SegmentRange, ...]:
    """Retourne toutes les plages continues sans franchir un trou."""

    if expected_interval_seconds <= 0:
        raise ValueError(
            "Intervalle attendu invalide."
        )

    if not bars:
        return ()

    ranges: list[SegmentRange] = []

    segment_start = 0
    gap_before = 0

    for index in range(
        1,
        len(bars),
    ):
        difference = int(
            (
                bars[index].time
                - bars[index - 1].time
            ).total_seconds()
        )

        if difference <= 0:
            raise ValueError(
                "Chronologie non strictement croissante "
                f"à l'index {index}."
            )

        if difference == expected_interval_seconds:
            continue

        ranges.append(
            SegmentRange(
                start=segment_start,
                stop=index,
                gap_before_seconds=gap_before,
            )
        )

        segment_start = index
        gap_before = difference

    ranges.append(
        SegmentRange(
            start=segment_start,
            stop=len(bars),
            gap_before_seconds=gap_before,
        )
    )

    return tuple(
        ranges
    )


def replayable_segment_ranges(
    bars: Sequence[Bar],
    *,
    expected_interval_seconds: int = 60,
    minimum_bars: int = 3,
) -> tuple[SegmentRange, ...]:
    """Écarte les micro-segments trop courts sans relier les trous."""

    if minimum_bars < 3:
        raise ValueError(
            "Un replay requiert au moins trois bougies."
        )

    return tuple(
        segment
        for segment in contiguous_segment_ranges(
            bars,
            expected_interval_seconds=(
                expected_interval_seconds
            ),
        )
        if segment.bars >= minimum_bars
    )
