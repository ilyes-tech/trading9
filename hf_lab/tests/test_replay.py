from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path
import sqlite3
import tempfile
import unittest

from hf_lab.replay import (
    Bar,
    ReplaySettings,
    ReplaySignal,
    load_bars,
    run_replay,
)


def make_bar(
    index: int,
    *,
    open_price: float = 100.0,
    high: float = 100.5,
    low: float = 99.5,
    close: float = 100.0,
) -> Bar:
    return Bar(
        time=(
            datetime(
                2026,
                1,
                1,
                tzinfo=timezone.utc,
            )
            + timedelta(
                minutes=15 * index
            )
        ),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1.0,
        trades=1.0,
    )


class CsvIntegrityTests(unittest.TestCase):
    def test_identical_timestamp_duplicate_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            header = "time,open,high,low,close\n"
            rows = [f"2026-01-01T00:{i:02d}:00Z,100,101,99,100\n" for i in (0, 5, 10)]
            path.write_text(header + "".join(rows) + rows[1])
            bars = load_bars(path)
            self.assertEqual(len(bars), 3)
            self.assertEqual([bar.time.minute for bar in bars], [0, 5, 10])

    def test_conflicting_timestamp_duplicate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bars.csv"
            path.write_text("time,open,high,low,close\n"
                "2026-01-01T00:00:00Z,100,101,99,100\n"
                "2026-01-01T00:05:00Z,100,101,99,100\n"
                "2026-01-01T00:10:00Z,100,101,99,100\n"
                "2026-01-01T00:05:00Z,100,105,99,104\n")
            with self.assertRaisesRegex(ValueError, "contradictoire"):
                load_bars(path)


class ReplayEngineTests(
    unittest.TestCase
):
    def test_strategy_never_receives_future_bars(
        self,
    ) -> None:
        bars = [
            make_bar(index)
            for index in range(8)
        ]

        observed_lengths: list[int] = []
        observed_last_times = []

        def observer(history):
            observed_lengths.append(
                len(history)
            )

            observed_last_times.append(
                history[-1].time
            )

            return None

        with tempfile.TemporaryDirectory() as folder:
            run_replay(
                symbol="BTCUSD",
                dataset="NO_LOOKAHEAD",
                bars=bars,
                strategy=observer,
                settings=ReplaySettings(
                    fee_bps_per_side=0,
                    slippage_bps_per_side=0,
                ),
                database_path=(
                    Path(folder)
                    / "test.sqlite3"
                ),
            )

        self.assertEqual(
            observed_lengths,
            list(
                range(
                    1,
                    len(bars),
                )
            ),
        )

        self.assertEqual(
            observed_last_times,
            [
                bars[index].time
                for index in range(
                    len(bars) - 1
                )
            ],
        )

    def test_entry_is_on_next_bar_and_sl_is_first(
        self,
    ) -> None:
        bars = [
            make_bar(
                0,
                close=100.0,
            ),
            make_bar(
                1,
                open_price=100.0,
                high=102.0,
                low=98.0,
                close=100.5,
            ),
            make_bar(
                2,
                close=100.0,
            ),
        ]

        def strategy(history):
            if len(history) == 1:
                return ReplaySignal(
                    strategy="TEST_BOTH_LEVELS",
                    side="BUY",
                    stop_distance=1.0,
                    target_distance=1.0,
                    confidence=1.0,
                )

            return None

        with tempfile.TemporaryDirectory() as folder:
            report = run_replay(
                symbol="BTCUSD",
                dataset="BOTH_LEVELS",
                bars=bars,
                strategy=strategy,
                settings=ReplaySettings(
                    fee_bps_per_side=0,
                    slippage_bps_per_side=0,
                ),
                database_path=(
                    Path(folder)
                    / "test.sqlite3"
                ),
            )

        self.assertEqual(
            report.metrics.trades,
            1,
        )

        trade = report.trades[0]

        self.assertEqual(
            trade.signal_time,
            bars[0].time,
        )

        self.assertEqual(
            trade.entry_time,
            bars[1].time,
        )

        self.assertEqual(
            trade.result,
            "SL",
        )

        self.assertAlmostEqual(
            trade.gross_r,
            -1.0,
        )

        self.assertAlmostEqual(
            trade.net_r,
            -1.0,
        )

    def test_costs_reduce_net_result(
        self,
    ) -> None:
        bars = [
            make_bar(
                0,
                close=100.0,
            ),
            make_bar(
                1,
                open_price=100.0,
                high=101.5,
                low=99.5,
                close=101.0,
            ),
            make_bar(
                2,
                close=101.0,
            ),
        ]

        def strategy(history):
            if len(history) == 1:
                return ReplaySignal(
                    strategy="TEST_COSTS",
                    side="BUY",
                    stop_distance=1.0,
                    target_distance=1.0,
                )

            return None

        with tempfile.TemporaryDirectory() as folder:
            report = run_replay(
                symbol="BTCUSD",
                dataset="COSTS",
                bars=bars,
                strategy=strategy,
                settings=ReplaySettings(
                    fee_bps_per_side=5.0,
                    slippage_bps_per_side=1.0,
                ),
                database_path=(
                    Path(folder)
                    / "test.sqlite3"
                ),
            )

        trade = report.trades[0]

        self.assertEqual(
            trade.result,
            "TP",
        )

        self.assertAlmostEqual(
            trade.gross_r,
            1.0,
        )

        self.assertGreater(
            trade.fee_r,
            0.0,
        )

        self.assertGreater(
            trade.slippage_r,
            0.0,
        )

        self.assertLess(
            trade.net_r,
            trade.gross_r,
        )

    def test_sqlite_records_run_signal_and_trade(
        self,
    ) -> None:
        bars = [
            make_bar(
                0,
                close=100.0,
            ),
            make_bar(
                1,
                open_price=100.0,
                high=101.5,
                low=99.5,
                close=101.0,
            ),
            make_bar(
                2,
                close=101.0,
            ),
        ]

        def strategy(history):
            if len(history) == 1:
                return ReplaySignal(
                    strategy="TEST_DATABASE",
                    side="BUY",
                    stop_distance=1.0,
                    target_distance=1.0,
                )

            return None

        with tempfile.TemporaryDirectory() as folder:
            database = (
                Path(folder)
                / "test.sqlite3"
            )

            run_replay(
                symbol="BTCUSD",
                dataset="DATABASE",
                bars=bars,
                strategy=strategy,
                settings=ReplaySettings(
                    fee_bps_per_side=0,
                    slippage_bps_per_side=0,
                ),
                database_path=database,
            )

            with sqlite3.connect(
                database
            ) as connection:
                runs = connection.execute(
                    "SELECT COUNT(*) FROM runs"
                ).fetchone()[0]

                signals = connection.execute(
                    "SELECT COUNT(*) FROM signals"
                ).fetchone()[0]

                trades = connection.execute(
                    "SELECT COUNT(*) FROM trades"
                ).fetchone()[0]

                integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]

        self.assertEqual(
            runs,
            1,
        )

        self.assertEqual(
            signals,
            1,
        )

        self.assertEqual(
            trades,
            1,
        )

        self.assertEqual(
            integrity,
            "ok",
        )


if __name__ == "__main__":
    unittest.main()
