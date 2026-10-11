from __future__ import annotations

import unittest

from hf_lab.labels.microstructure_parametric import (
    BookPressureParameters,
    CompositePressureParameters,
    FlowPressureParameters,
    default_parameters,
    signal_side_parametric,
)


def base_row() -> dict[str, object]:
    return {
        "spread_mean_5s": 0.5,
        "continuous_5s": 1,
        "continuous_15s": 1,
        "imbalance_mean_5s": 0.30,
        "imbalance_mean_15s": 0.30,
        "microprice_edge_mean_5s": 0.02,
        "microprice_edge_mean_15s": 0.02,
        "top_imbalance": 0.20,
        "trade_count_5s": 3,
        "trade_imbalance_5s": 0.40,
    }


class MicrostructureParametricTests(
    unittest.TestCase,
):
    def test_defaults_are_valid(
        self,
    ) -> None:
        self.assertIsInstance(
            default_parameters(
                "BOOK_PRESSURE"
            ),
            BookPressureParameters,
        )

        self.assertIsInstance(
            default_parameters(
                "FLOW_PRESSURE"
            ),
            FlowPressureParameters,
        )

        self.assertIsInstance(
            default_parameters(
                "COMPOSITE_PRESSURE"
            ),
            CompositePressureParameters,
        )

    def test_invalid_threshold_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            BookPressureParameters(
                minimum_imbalance_5s=1.1
            )

        with self.assertRaises(
            ValueError
        ):
            FlowPressureParameters(
                maximum_spread_bps=-1
            )

    def test_default_long_signals(
        self,
    ) -> None:
        row = base_row()

        for candidate in (
            "BOOK_PRESSURE",
            "FLOW_PRESSURE",
            "COMPOSITE_PRESSURE",
        ):
            self.assertEqual(
                signal_side_parametric(
                    row,
                    candidate,
                ),
                "LONG",
            )

    def test_zero_edge_is_not_book_signal(
        self,
    ) -> None:
        row = base_row()

        row[
            "microprice_edge_mean_5s"
        ] = 0.0

        self.assertIsNone(
            signal_side_parametric(
                row,
                "BOOK_PRESSURE",
            )
        )

    def test_custom_threshold_filters_signal(
        self,
    ) -> None:
        row = base_row()

        parameters = (
            BookPressureParameters(
                minimum_imbalance_5s=0.80
            )
        )

        self.assertIsNone(
            signal_side_parametric(
                row,
                "BOOK_PRESSURE",
                parameters,
            )
        )


if __name__ == "__main__":
    unittest.main()
