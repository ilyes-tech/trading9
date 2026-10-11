from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hf_lab.replay import (
    Bar,
    ReplaySettings,
    ReplaySignal,
)
from hf_lab.segmented_replay import (
    run_segmented_replay,
)


def bar(
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

    price = (
        100.0
        + minute * 0.01
    )

    return Bar(
        time=timestamp,
        open=price,
        high=price + 0.10,
        low=price - 0.10,
        close=price + 0.01,
        volume=1.0,
        trades=1.0,
    )


class SegmentedReplayTests(
    unittest.TestCase,
):
    def test_trade_never_crosses_gap(
        self,
    ) -> None:
        bars = [
            bar(0),
            bar(1),
            bar(2),
            bar(3),

            bar(20),
            bar(21),
            bar(22),
            bar(23),
        ]

        def strategy(
            history,
        ):
            if len(history) == 2:
                return ReplaySignal(
                    strategy="SEGMENT_TEST",
                    side="BUY",
                    stop_distance=100.0,
                    target_distance=100.0,
                )

            return None

        with TemporaryDirectory() as directory:
            report = run_segmented_replay(
                symbol="TEST",
                dataset="SEGMENT_TEST",
                bars=bars,
                strategy=strategy,
                settings=ReplaySettings(
                    maximum_holding_bars=100,
                ),
                database_path=(
                    Path(directory)
                    / "segmented.sqlite3"
                ),
            )

        self.assertEqual(
            report.segments_total,
            2,
        )

        self.assertEqual(
            report.segments_replayed,
            2,
        )

        self.assertEqual(
            len(report.trades),
            2,
        )

        first_trade = report.trades[0]
        second_trade = report.trades[1]

        self.assertLess(
            first_trade.exit_time,
            second_trade.entry_time,
        )

        self.assertEqual(
            first_trade.result,
            "END_OF_DATA",
        )

        self.assertEqual(
            second_trade.result,
            "END_OF_DATA",
        )

    def test_micro_segment_is_skipped(
        self,
    ) -> None:
        bars = [
            bar(0),
            bar(1),
            bar(2),

            bar(10),

            bar(20),
            bar(21),
            bar(22),
        ]

        with TemporaryDirectory() as directory:
            report = run_segmented_replay(
                symbol="TEST",
                dataset="MICRO_SEGMENT",
                bars=bars,
                strategy=lambda history: None,
                database_path=(
                    Path(directory)
                    / "segmented.sqlite3"
                ),
            )

        self.assertEqual(
            report.segments_total,
            3,
        )

        self.assertEqual(
            report.segments_replayed,
            2,
        )

        self.assertEqual(
            report.segments_skipped,
            1,
        )

        self.assertEqual(
            report.skipped_bars,
            1,
        )


if __name__ == "__main__":
    unittest.main()
