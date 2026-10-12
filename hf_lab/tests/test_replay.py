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


class DirectReplayBarIntegrityTests(unittest.TestCase):
    def test_direct_replay_rejects_invalid_bars_before_database_creation(self) -> None:
        from dataclasses import replace
        baseline = [make_bar(i) for i in range(3)]
        cases = (
            (1, {"close": float("nan")}),
            (1, {"volume": -1.0}),
            (1, {"trades": float("inf")}),
            (1, {"time": baseline[0].time}),
            (1, {"time": datetime(2026, 1, 1)}),
        )
        for index, changes in cases:
            with self.subTest(changes=changes):
                bars = list(baseline)
                bars[index] = replace(bars[index], **changes)
                with tempfile.TemporaryDirectory() as folder:
                    db = Path(folder) / "replay.sqlite3"
                    with self.assertRaises(ValueError):
                        run_replay(symbol="BTCUSD", dataset="INVALID", bars=bars, strategy=lambda _: None, database_path=db)
                    self.assertFalse(db.exists())


class ReplaySignalFiniteConfidenceTests(unittest.TestCase):
    def test_nonfinite_confidence_fails_closed(self) -> None:
        for value in (float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ReplaySignal(strategy="TEST", side="BUY", stop_distance=1.0, target_distance=1.0, confidence=value).validate()


class ReplaySettingsFiniteCostTests(unittest.TestCase):
    def test_nonfinite_costs_fail_closed(self) -> None:
        for field in ("fee_bps_per_side", "slippage_bps_per_side"):
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        ReplaySettings(**{field: value}).validate()


class CsvVolumeIntegrityTests(unittest.TestCase):
    def test_negative_or_nonfinite_volume_and_trades_rejected(self) -> None:
        for field in ("volume", "trades"):
            for value in ("-1", "nan", "inf", "-inf"):
                with self.subTest(field=field, value=value):
                    with tempfile.TemporaryDirectory() as folder:
                        path = Path(folder) / "bars.csv"
                        rows = ["2026-01-01T00:00:00Z,100,101,99,100,1,1","2026-01-01T00:01:00Z,100,101,99,100,1,1","2026-01-01T00:02:00Z,100,101,99,100,1,1"]
                        fields = rows[1].split(",")
                        fields[5 if field == "volume" else 6] = value
                        rows[1] = ",".join(fields)
                        path.write_text("time,open,high,low,close,volume,trades\n" + "\n".join(rows) + "\n")
                        with self.assertRaisesRegex(ValueError, "volume ou transactions invalides"):
                            load_bars(path)


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

    def test_zero_trade_entry_bar_expires_signal(self) -> None:
        bars = [make_bar(0), make_bar(1), make_bar(2)]
        bars[1] = Bar(time=bars[1].time, open=100.0, high=100.0,
                      low=100.0, close=100.0, volume=0.0, trades=0.0)
        def strategy(history):
            return ReplaySignal(strategy="ZERO_ENTRY", side="BUY",
                                stop_distance=1.0, target_distance=1.0) if len(history) == 1 else None
        with tempfile.TemporaryDirectory() as folder:
            report = run_replay(symbol="BTCUSD", dataset="SYNTHETIC_ZERO_ENTRY",
                                bars=bars, strategy=strategy,
                                database_path=Path(folder) / "test.sqlite3")
        self.assertEqual(len(report.trades), 0)

    def test_zero_trade_signal_bar_is_ignored(self) -> None:
        bars = [make_bar(0), make_bar(1), make_bar(2)]
        bars[0] = Bar(time=bars[0].time, open=100.0, high=100.0,
                      low=100.0, close=100.0, volume=0.0, trades=0.0)
        def strategy(history):
            return ReplaySignal(strategy="ZERO_SIGNAL", side="BUY",
                                stop_distance=1.0, target_distance=1.0) if len(history) == 1 else None
        with tempfile.TemporaryDirectory() as folder:
            report = run_replay(symbol="BTCUSD", dataset="SYNTHETIC_ZERO_SIGNAL",
                                bars=bars, strategy=strategy,
                                database_path=Path(folder) / "test.sqlite3")
        self.assertEqual(len(report.trades), 0)

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


class ZeroTradeExitTests(unittest.TestCase):
    def test_max_hold_waits_for_traded_bar(self) -> None:
        bars = [make_bar(i) for i in range(4)]
        bars[2] = Bar(time=bars[2].time, open=100, high=100,
                      low=100, close=100, volume=0, trades=0)

        def strategy(history):
            if len(history) == 1:
                return ReplaySignal(strategy="ZERO_EXIT_GUARD", side="BUY",
                                    stop_distance=100, target_distance=100)
            return None

        with tempfile.TemporaryDirectory() as folder:
            report = run_replay(
                symbol="BTCUSD", dataset="SYNTHETIC_ZERO_EXIT",
                bars=bars, strategy=strategy,
                settings=ReplaySettings(maximum_holding_bars=2,
                                        fee_bps_per_side=0,
                                        slippage_bps_per_side=0),
                database_path=Path(folder) / "test.sqlite3",
            )
        self.assertEqual(len(report.trades), 1)
        self.assertEqual(report.trades[0].result, "MAX_HOLD")
        self.assertEqual(report.trades[0].exit_time, bars[3].time)

    def test_end_of_data_zero_trade_bar_fails_closed(self) -> None:
        bars = [make_bar(i) for i in range(3)]
        bars[2] = Bar(time=bars[2].time, open=100, high=100,
                      low=100, close=100, volume=0, trades=0)

        def strategy(history):
            if len(history) == 1:
                return ReplaySignal(strategy="ZERO_FINAL", side="BUY",
                                    stop_distance=100, target_distance=100)
            return None

        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "derniere bougie sans transaction"):
                run_replay(
                    symbol="BTCUSD", dataset="SYNTHETIC_ZERO_FINAL",
                    bars=bars, strategy=strategy,
                    settings=ReplaySettings(maximum_holding_bars=48),
                    database_path=Path(folder) / "test.sqlite3",
                )
