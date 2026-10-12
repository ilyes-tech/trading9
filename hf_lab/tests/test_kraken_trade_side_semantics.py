"""Kraken Trades -> M1: side and taker-order-type invariants (no network)."""

import unittest
from unittest.mock import patch

from hf_lab.tools import kraken_trades_to_micro_m1_resume as collector


START = 1772323200


class KrakenTradeSideSemanticsTests(unittest.TestCase):
    def test_buy_sell_and_order_type_are_independent(self):
        trades = [
            [100, 2.0, START + 5, "b", "m", ""],
            [101, 3.0, START + 15, "s", "l", ""],
            [102, 4.0, START + 25, "s", "m", ""],
            [103, 1.0, START + 35, "b", "l", ""],
        ]
        with patch.object(collector, "BAR_SECONDS", 60):
            bars, used, ended = collector.aggregate_page(
                trades, START, START + 120
            )
        self.assertEqual((used, ended), (4, False))
        row = bars[START]
        self.assertEqual(row[4:14], [10.0, 4, 3.0, 7.0, 2, 2, 6.0, 4.0, 2, 2])
        self.assertEqual(row[0:4], [100.0, 103.0, 100.0, 103.0])

    def test_m1_bucketing_and_half_open_range(self):
        trades = [
            [90, 1.0, START - 2, "b", "m", ""],
            [100, 1.0, START + 59, "b", "l", ""],
            [101, 2.0, START + 60, "s", "m", ""],
            [102, 3.0, START + 120, "b", "m", ""],
        ]
        with patch.object(collector, "BAR_SECONDS", 60):
            bars, used, ended = collector.aggregate_page(
                trades, START, START + 120
            )
        self.assertEqual((used, ended), (2, True))
        self.assertEqual(sorted(bars), [START, START + 60])
        self.assertEqual(bars[START][6:8], [1.0, 0.0])
        self.assertEqual(bars[START + 60][6:8], [0.0, 2.0])

    def test_unknown_side_or_order_type_fails_closed(self):
        for index, value in ((3, "unknown"), (4, "unknown")):
            with self.subTest(index=index):
                trade = [100, 1.0, START + 2, "b", "m", ""]
                trade[index] = value
                with patch.object(collector, "BAR_SECONDS", 60):
                    with self.assertRaisesRegex(RuntimeError, "UNKNOWN_"):
                        collector.aggregate_page([trade], START, START + 60)


if __name__ == "__main__":
    unittest.main()
