from __future__ import annotations

import unittest

from hf_lab.labels.microstructure_dynamic import (
    DynamicCompositeParameters,
    LiquidityShiftParameters,
    OFIImpulseParameters,
    signal_side_dynamic,
)


def base_row() -> dict[str, object]:
    return {
        "dynamic_ready_1s": 1,
        "dynamic_continuous_5s": 1,
        "source_spread_bps": 0.5,

        "ofi_normalized_1s": 0.8,
        "imbalance_delta_1s": 0.2,
        "microprice_edge_delta_1s_bps": 0.02,

        "liquidity_skew_delta_1s": 0.3,
        "bid_depth_log_change_1s": 0.2,
        "ask_depth_log_change_1s": -0.2,
        "source_imbalance_10": 0.4,

        "trade_pressure_5s": 0.01,
    }


class DynamicSignalTests(
    unittest.TestCase,
):
    def test_ofi_long_signal(
        self,
    ) -> None:
        self.assertEqual(
            signal_side_dynamic(
                base_row(),
                "OFI_IMPULSE",
                OFIImpulseParameters(),
            ),
            "LONG",
        )

    def test_liquidity_long_signal(
        self,
    ) -> None:
        self.assertEqual(
            signal_side_dynamic(
                base_row(),
                "LIQUIDITY_SHIFT",
                LiquidityShiftParameters(),
            ),
            "LONG",
        )

    def test_composite_long_signal(
        self,
    ) -> None:
        self.assertEqual(
            signal_side_dynamic(
                base_row(),
                "DYNAMIC_COMPOSITE",
                DynamicCompositeParameters(),
            ),
            "LONG",
        )

    def test_strict_threshold_filters(
        self,
    ) -> None:
        self.assertIsNone(
            signal_side_dynamic(
                base_row(),
                "OFI_IMPULSE",
                OFIImpulseParameters(
                    minimum_abs_ofi_normalized=2.0,
                ),
            )
        )

    def test_gap_blocks_signal(
        self,
    ) -> None:
        row = base_row()
        row[
            "dynamic_continuous_5s"
        ] = 0

        self.assertIsNone(
            signal_side_dynamic(
                row,
                "DYNAMIC_COMPOSITE",
                DynamicCompositeParameters(),
            )
        )


if __name__ == "__main__":
    unittest.main()
