"""Replay indépendant de chaque segment temporel continu."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import overload

from hf_lab.replay import (
    Bar,
    Metrics,
    ReplayReport,
    ReplaySettings,
    ReplaySignal,
    TradeResult,
    calculate,
    run_replay,
)
from hf_lab.segments import (
    contiguous_segment_ranges,
)


StrategyFunction = Callable[
    [Sequence[Bar]],
    ReplaySignal | None,
]


class SegmentView(
    Sequence[Bar],
):
    """Vue bornée d'un segment sans recopier la liste des bougies."""

    __slots__ = (
        "_source",
        "_start",
        "_stop",
    )

    def __init__(
        self,
        source: Sequence[Bar],
        start: int,
        stop: int,
    ) -> None:
        if not 0 <= start <= stop <= len(source):
            raise ValueError(
                "Bornes SegmentView invalides : "
                f"{start}:{stop}/{len(source)}"
            )

        self._source = source
        self._start = start
        self._stop = stop

    def __len__(self) -> int:
        return (
            self._stop
            - self._start
        )

    @overload
    def __getitem__(
        self,
        index: int,
    ) -> Bar:
        ...

    @overload
    def __getitem__(
        self,
        index: slice,
    ) -> tuple[Bar, ...]:
        ...

    def __getitem__(
        self,
        index: int | slice,
    ) -> Bar | tuple[Bar, ...]:
        length = len(self)

        if isinstance(index, slice):
            start, stop, step = index.indices(
                length
            )

            return tuple(
                self._source[
                    self._start + position
                ]
                for position in range(
                    start,
                    stop,
                    step,
                )
            )

        normalized = index

        if normalized < 0:
            normalized += length

        if (
            normalized < 0
            or normalized >= length
        ):
            raise IndexError(
                "SegmentView index hors limite"
            )

        return self._source[
            self._start
            + normalized
        ]


@dataclass(
    frozen=True,
    slots=True,
)
class SegmentedReplayReport:
    symbol: str
    dataset: str

    source_bars: int
    replayed_bars: int
    skipped_bars: int

    segments_total: int
    segments_replayed: int
    segments_skipped: int

    reports: tuple[ReplayReport, ...]
    trades: tuple[TradeResult, ...]
    metrics: Metrics


def run_segmented_replay(
    *,
    symbol: str,
    dataset: str,
    bars: Sequence[Bar],
    strategy: StrategyFunction,
    settings: ReplaySettings | None = None,
    database_path: str | Path,
    expected_interval_seconds: int = 60,
    minimum_segment_bars: int = 3,
) -> SegmentedReplayReport:
    selected_settings = (
        settings
        or ReplaySettings()
    )

    selected_settings.validate()

    if not selected_settings.force_close_at_end:
        raise ValueError(
            "La clôture de fin de segment est obligatoire."
        )

    if minimum_segment_bars < 3:
        raise ValueError(
            "minimum_segment_bars doit être >= 3."
        )

    segments = contiguous_segment_ranges(
        bars,
        expected_interval_seconds=(
            expected_interval_seconds
        ),
    )

    reports: list[ReplayReport] = []

    skipped_bars = 0
    skipped_segments = 0

    for segment_number, segment in enumerate(
        segments,
        start=1,
    ):
        if segment.bars < minimum_segment_bars:
            skipped_bars += segment.bars
            skipped_segments += 1
            continue

        segment_bars = SegmentView(
            bars,
            segment.start,
            segment.stop,
        )

        segment_dataset = (
            f"{dataset}"
            f"::SEGMENT_{segment_number:03d}"
            f"_OF_{len(segments):03d}"
        )

        report = run_replay(
            symbol=symbol,
            dataset=segment_dataset,
            bars=segment_bars,
            strategy=strategy,
            settings=selected_settings,
            database_path=database_path,
        )

        reports.append(
            report
        )

    trades = tuple(
        trade
        for report in reports
        for trade in report.trades
    )

    replayed_bars = sum(
        report.bars
        for report in reports
    )

    if (
        replayed_bars
        + skipped_bars
        != len(bars)
    ):
        raise RuntimeError(
            "Comptage des bougies segmentées incohérent."
        )

    metrics = calculate(
        trade.net_r
        for trade in trades
    )

    return SegmentedReplayReport(
        symbol=str(symbol).upper().strip(),
        dataset=dataset,

        source_bars=len(bars),
        replayed_bars=replayed_bars,
        skipped_bars=skipped_bars,

        segments_total=len(segments),
        segments_replayed=len(reports),
        segments_skipped=skipped_segments,

        reports=tuple(reports),
        trades=trades,
        metrics=metrics,
    )
