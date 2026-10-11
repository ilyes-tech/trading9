from __future__ import annotations

import unittest

from hf_lab.labels.microstructure import (
    SECOND_NS,
    build_shadow_trades,
)


def row(
    *,
    second: int,
    bid: float,
    ask: float,
    imbalance: float = 0.5,
    edge: float = 0.02,
    top_imbalance: float = 0.4,
    trade_imbalance: float = 0.5,
) -> dict[str, object]:
    return {
        "bucket_ns": (
            second
            * SECOND_NS
        ),
        "available_ns": (
            (
                second
                + 1
            )
            * SECOND_NS
        ),
        "symbol": "BTC/USD",
        "bid": bid,
        "ask": ask,
        "spread_bps": 0.5,
        "spread_mean_5s": 0.5,
        "top_imbalance": top_imbalance,
        "imbalance_mean_5s": imbalance,
        "imbalance_mean_15s": imbalance,
        "microprice_edge_mean_5s": edge,
        "microprice_edge_mean_15s": edge,
        "trade_imbalance_5s": (
            trade_imbalance
        ),
        "trade_count_5s": 3,
        "continuous_5s": 1,
        "continuous_15s": 1,
    }


class MicrostructureLabelTests(
    unittest.TestCase,
):
    def test_long_execution_uses_ask_then_bid(
        self,
    ) -> None:
        rows = [
            row(
                second=second,
                bid=100.0 + second,
                ask=101.0 + second,
            )
            for second in range(
                0,
                8,
            )
        ]

        trades = build_shadow_trades(
            rows,
            candidate="BOOK_PRESSURE",
            horizon_seconds=5,
        )

        self.assertEqual(
            len(trades),
            1,
        )

        trade = trades[0]

        self.assertEqual(
            trade["side"],
            "LONG",
        )

        self.assertEqual(
            trade["entry_price"],
            102.0,
        )

        self.assertEqual(
            trade["exit_price"],
            106.0,
        )

        self.assertLess(
            trade[
                "signal_available_ns"
            ],
            trade[
                "entry_available_ns"
            ],
        )

        self.assertLess(
            trade[
                "entry_available_ns"
            ],
            trade[
                "exit_available_ns"
            ],
        )

    def test_gap_blocks_trade(
        self,
    ) -> None:
        rows = [
            row(
                second=0,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=1,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=3,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=4,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=5,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=6,
                bid=100.0,
                ask=101.0,
            ),
            row(
                second=7,
                bid=100.0,
                ask=101.0,
            ),
        ]

        trades = build_shadow_trades(
            rows,
            candidate="BOOK_PRESSURE",
            horizon_seconds=5,
        )

        self.assertEqual(
            trades,
            [],
        )

    def test_short_execution_uses_bid_then_ask(
        self,
    ) -> None:
        rows = [
            row(
                second=second,
                bid=110.0 - second,
                ask=111.0 - second,
                imbalance=-0.5,
                edge=-0.02,
                top_imbalance=-0.4,
                trade_imbalance=-0.5,
            )
            for second in range(
                0,
                8,
            )
        ]

        trades = build_shadow_trades(
            rows,
            candidate="BOOK_PRESSURE",
            horizon_seconds=5,
        )

        self.assertEqual(
            len(trades),
            1,
        )

        trade = trades[0]

        self.assertEqual(
            trade["side"],
            "SHORT",
        )

        self.assertEqual(
            trade["entry_price"],
            109.0,
        )

        self.assertEqual(
            trade["exit_price"],
            105.0,
        )


if __name__ == "__main__":
    unittest.main()
