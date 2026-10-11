from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hf_lab.history_view import VisibleHistory
from hf_lab.replay import (
    Bar,
    ReplaySettings,
    run_replay,
)
from hf_lab.segments import (
    contiguous_segment_ranges,
    replayable_segment_ranges,
)


def make_bar(
    minute: int,
) -> Bar:
    timestamp = (
        datetime(
            2025,
            1,
            1,
            tzinfo=timezone.utc,
        )
        + timedelta(
            minutes=minute
        )
    )

    price = 100.0 + minute

    return Bar(
        time=timestamp,
        open=price,
        high=price + 1.0,
        low=price - 1.0,
        close=price + 0.25,
        volume=1.0,
        trades=1.0,
    )


class NoSliceSequence(
    Sequence[Bar],
):
    def __init__(
        self,
        values: list[Bar],
    ) -> None:
        self.values = values

    def __len__(self) -> int:
        return len(
            self.values
        )

    def __getitem__(
        self,
        index,
    ):
        if isinstance(
            index,
            slice,
        ):
            raise AssertionError(
                "Le moteur a tenté de copier "
                "un préfixe de la source."
            )

        return self.values[
            index
        ]


class M1EngineTests(
    unittest.TestCase,
):
    def test_visible_history_blocks_future(
        self,
    ) -> None:
        source = list(
            range(10)
        )

        history = VisibleHistory(
            source,
            5,
        )

        self.assertEqual(
            len(history),
            5,
        )

        self.assertEqual(
            history[-1],
            4,
        )

        self.assertEqual(
            history[-3:],
            (
                2,
                3,
                4,
            ),
        )

        with self.assertRaises(
            IndexError
        ):
            _ = history[5]

    def test_run_replay_avoids_prefix_slice(
        self,
    ) -> None:
        bars = NoSliceSequence(
            [
                make_bar(index)
                for index in range(30)
            ]
        )

        observed_lengths: list[int] = []

        def strategy(
            history,
        ):
            observed_lengths.append(
                len(history)
            )

            _ = history[-1]

            return None

        with TemporaryDirectory() as directory:
            report = run_replay(
                symbol="TEST",
                dataset="NO_PREFIX_SLICE",
                bars=bars,
                strategy=strategy,
                settings=ReplaySettings(),
                database_path=(
                    Path(directory)
                    / "replay.sqlite3"
                ),
            )

        self.assertEqual(
            report.bars,
            30,
        )

        self.assertEqual(
            observed_lengths[0],
            1,
        )

        self.assertEqual(
            observed_lengths[-1],
            29,
        )

    def test_segments_never_cross_gap(
        self,
    ) -> None:
        bars = [
            make_bar(0),
            make_bar(1),
            make_bar(2),
            make_bar(3),

            make_bar(10),

            make_bar(20),
            make_bar(21),
            make_bar(22),
        ]

        segments = contiguous_segment_ranges(
            bars
        )

        self.assertEqual(
            [
                segment.bars
                for segment in segments
            ],
            [
                4,
                1,
                3,
            ],
        )

        replayable = replayable_segment_ranges(
            bars
        )

        self.assertEqual(
            [
                segment.bars
                for segment in replayable
            ],
            [
                4,
                3,
            ],
        )

        self.assertEqual(
            replayable[1].gap_before_seconds,
            600,
        )


if __name__ == "__main__":
    unittest.main()
