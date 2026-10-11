from __future__ import annotations

import unittest

from hf_lab.features.microstructure import (
    SECOND_NS,
    build_feature_rows,
)


def sample(
    *,
    second: int,
    symbol: str = "BTC/USD",
    bid: float = 100.0,
    ask: float = 101.0,
    imbalance: float = 0.2,
) -> dict[str, object]:
    bucket_ns = (
        second
        * SECOND_NS
    )

    mid = (
        bid
        + ask
    ) / 2.0

    return {
        "session_id": 1,
        "bucket_ns": bucket_ns,
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "bid_qty": 2.0,
        "ask_qty": 1.0,
        "mid": mid,
        "spread_bps": (
            (
                ask
                - bid
            )
            / mid
            * 10_000.0
        ),
        "microprice": 100.7,
        "bid_depth_10": 10.0,
        "ask_depth_10": 8.0,
        "imbalance_10": imbalance,
        "ticker_bid": bid,
        "ticker_ask": ask,
        "ticker_spread_bps": 1.0,
        "book_updates": 3,
    }


class MicrostructureFeatureTests(
    unittest.TestCase,
):
    def test_trade_flow_is_causal(
        self,
    ) -> None:
        samples = [
            sample(
                second=10
            ),
            sample(
                second=11,
                bid=101.0,
                ask=102.0,
            ),
        ]

        trades = [
            {
                "symbol": "BTC/USD",
                "received_ns": (
                    10
                    * SECOND_NS
                    + 500
                ),
                "side": "buy",
                "price": 100.5,
                "qty": 2.0,
            },
            {
                "symbol": "BTC/USD",
                "received_ns": (
                    11
                    * SECOND_NS
                    + 500
                ),
                "side": "sell",
                "price": 101.5,
                "qty": 1.0,
            },
        ]

        rows = build_feature_rows(
            samples,
            trades,
        )

        self.assertEqual(
            len(rows),
            2,
        )

        self.assertEqual(
            rows[0]["trade_count"],
            1,
        )

        self.assertEqual(
            rows[0]["buy_qty"],
            2.0,
        )

        self.assertEqual(
            rows[0]["sell_qty"],
            0.0,
        )

        self.assertEqual(
            rows[0]["available_ns"],
            11 * SECOND_NS,
        )

    def test_gap_resets_rolling_windows(
        self,
    ) -> None:
        samples = [
            sample(
                second=1
            ),
            sample(
                second=2
            ),
            sample(
                second=10
            ),
        ]

        rows = build_feature_rows(
            samples,
            [],
        )

        self.assertEqual(
            rows[-1][
                "gap_before_seconds"
            ],
            7,
        )

        self.assertEqual(
            rows[-1][
                "continuous_5s"
            ],
            0,
        )

        self.assertIsNone(
            rows[-1][
                "mid_return_1s_bps"
            ]
        )

    def test_five_second_continuity(
        self,
    ) -> None:
        samples = [
            sample(
                second=second,
                bid=100.0 + second,
                ask=101.0 + second,
            )
            for second in range(
                20,
                25,
            )
        ]

        rows = build_feature_rows(
            samples,
            [],
        )

        self.assertEqual(
            rows[-1][
                "continuous_5s"
            ],
            1,
        )

        self.assertIsNotNone(
            rows[-1][
                "mid_return_5s_bps"
            ]
        )


if __name__ == "__main__":
    unittest.main()
