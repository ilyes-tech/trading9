from __future__ import annotations

import unittest

from hf_lab.features.microstructure_dynamics import (
    SECOND_NS,
    build_dynamic_rows,
    calculate_ofi,
)


def row(
    *,
    second: int,
    bid: float = 100.0,
    ask: float = 101.0,
    bid_qty: float = 2.0,
    ask_qty: float = 1.0,
    signed_qty: float = 0.0,
) -> dict[str, object]:
    return {
        "bucket_ns": second * SECOND_NS,
        "available_ns": (
            second + 1
        ) * SECOND_NS,
        "symbol": "BTC/USD",
        "session_id": 1,

        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,

        "bid_depth_10": 10.0,
        "ask_depth_10": 8.0,
        "depth_total_10": 18.0,
        "depth_log_ratio": 0.2,

        "imbalance_10": 0.1,
        "top_imbalance": 0.2,
        "microprice_edge_bps": 0.01,
        "spread_bps": 0.5,

        "book_updates_5s": 10,
        "trade_count_5s": 2,
        "signed_qty": signed_qty,

        "mid_return_1s_bps": 0.0,
        "mid_return_5s_bps": 0.0,
    }


class DynamicFeatureTests(
    unittest.TestCase,
):
    def test_ofi_when_bid_and_ask_move_up(
        self,
    ) -> None:
        previous = row(
            second=1,
            bid=100.0,
            ask=101.0,
            bid_qty=2.0,
            ask_qty=1.0,
        )

        current = row(
            second=2,
            bid=101.0,
            ask=102.0,
            bid_qty=3.0,
            ask_qty=2.0,
        )

        self.assertEqual(
            calculate_ofi(
                previous,
                current,
            ),
            4.0,
        )

    def test_first_row_is_not_ready(
        self,
    ) -> None:
        rows = build_dynamic_rows(
            [
                row(
                    second=1
                )
            ]
        )

        self.assertEqual(
            rows[0][
                "dynamic_ready_1s"
            ],
            0,
        )

        self.assertEqual(
            rows[0][
                "ofi_1s"
            ],
            0.0,
        )

    def test_gap_resets_dynamic_state(
        self,
    ) -> None:
        rows = build_dynamic_rows(
            [
                row(
                    second=1
                ),
                row(
                    second=2
                ),
                row(
                    second=8
                ),
            ]
        )

        self.assertEqual(
            rows[1][
                "dynamic_ready_1s"
            ],
            1,
        )

        self.assertEqual(
            rows[2][
                "dynamic_ready_1s"
            ],
            0,
        )

        self.assertEqual(
            rows[2][
                "dynamic_continuous_5s"
            ],
            0,
        )

    def test_signed_quantity_window_is_past_only(
        self,
    ) -> None:
        rows = build_dynamic_rows(
            [
                row(
                    second=second,
                    signed_qty=float(second),
                )
                for second in range(
                    1,
                    7,
                )
            ]
        )

        self.assertEqual(
            rows[-1][
                "signed_qty_5s"
            ],
            2.0
            + 3.0
            + 4.0
            + 5.0
            + 6.0,
        )

        self.assertEqual(
            rows[-1][
                "dynamic_continuous_5s"
            ],
            1,
        )


if __name__ == "__main__":
    unittest.main()
