from __future__ import annotations

import unittest

from hf_lab.strategies.m1_parametric import (
    BreakoutParameters,
    MomentumParameters,
    RiskParameters,
    TrendPullbackParameters,
    _build_signal,
)


class ParametricM1Tests(
    unittest.TestCase,
):
    def test_original_risk_without_bps_floor(
        self,
    ) -> None:
        signal = _build_signal(
            strategy_name="TEST",
            side="BUY",
            atr_value=10.0,
            reference_price=100_000.0,
            risk=RiskParameters(
                stop_atr_multiplier=1.10,
                target_atr_multiplier=0.75,
            ),
            confidence=0.5,
            metadata={},
        )

        self.assertAlmostEqual(
            signal.stop_distance,
            11.0,
        )

        self.assertAlmostEqual(
            signal.target_distance,
            7.5,
        )

    def test_bps_floor_can_dominate_atr(
        self,
    ) -> None:
        signal = _build_signal(
            strategy_name="TEST",
            side="BUY",
            atr_value=1.0,
            reference_price=100_000.0,
            risk=RiskParameters(
                stop_atr_multiplier=1.0,
                target_atr_multiplier=1.0,
                min_stop_bps=20.0,
                min_target_bps=40.0,
            ),
            confidence=0.5,
            metadata={},
        )

        self.assertAlmostEqual(
            signal.stop_distance,
            200.0,
        )

        self.assertAlmostEqual(
            signal.target_distance,
            400.0,
        )

    def test_invalid_risk_is_rejected(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            RiskParameters(
                stop_atr_multiplier=0.0,
                target_atr_multiplier=1.0,
            ).validate()

    def test_invalid_breakout_body_ratio(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            BreakoutParameters(
                min_body_ratio=1.1
            ).validate()

    def test_invalid_trend_periods(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            TrendPullbackParameters(
                fast_bars=24,
                slow_bars=6,
            ).validate()

    def test_default_parameter_sets_are_valid(
        self,
    ) -> None:
        MomentumParameters().validate()
        BreakoutParameters().validate()
        TrendPullbackParameters().validate()


if __name__ == "__main__":
    unittest.main()
