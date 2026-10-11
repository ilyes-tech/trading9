from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
import unittest

from hf_lab.replay import Bar
from hf_lab.splits import (
    chronological_split,
)
from hf_lab.strategies.candidates import (
    candidate_specs,
)


def synthetic_bars(
    count: int = 150,
) -> list[Bar]:
    bars: list[Bar] = []

    price = 100.0

    for index in range(
        count
    ):
        cycle = (
            index % 20
        )

        drift = (
            0.18
            if cycle < 10
            else -0.12
        )

        shock = (
            1.20
            if index % 31 == 0
            else 0.0
        )

        open_price = price
        close_price = max(
            1.0,
            open_price
            + drift
            + shock,
        )

        high = max(
            open_price,
            close_price,
        ) + 0.35

        low = min(
            open_price,
            close_price,
        ) - 0.35

        bars.append(
            Bar(
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
                close=close_price,
                volume=(
                    100.0
                    + (
                        index % 9
                    )
                    * 10.0
                ),
                trades=(
                    50.0
                    + index % 7
                ),
            )
        )

        price = close_price

    return bars


class CandidateTests(
    unittest.TestCase
):
    def test_chronological_split(
        self,
    ) -> None:
        values = list(
            range(100)
        )

        split = chronological_split(
            values
        )

        self.assertEqual(
            len(split.train),
            60,
        )

        self.assertEqual(
            len(split.validation),
            20,
        )

        self.assertEqual(
            len(split.test),
            20,
        )

        self.assertLess(
            split.train[-1],
            split.validation[0],
        )

        self.assertLess(
            split.validation[-1],
            split.test[0],
        )

    def test_candidates_are_valid(
        self,
    ) -> None:
        bars = synthetic_bars()

        generated = 0

        for spec in candidate_specs():
            for end in range(
                1,
                len(bars) + 1,
            ):
                signal = spec.strategy(
                    tuple(
                        bars[:end]
                    )
                )

                if signal is None:
                    continue

                signal.validate()

                self.assertEqual(
                    signal.strategy,
                    spec.name,
                )

                self.assertGreater(
                    signal.stop_distance,
                    0,
                )

                self.assertGreater(
                    signal.target_distance,
                    0,
                )

                generated += 1

        self.assertGreater(
            generated,
            0,
        )

    def test_insufficient_history_is_safe(
        self,
    ) -> None:
        bars = synthetic_bars(
            10
        )

        for spec in candidate_specs():
            signal = spec.strategy(
                tuple(bars)
            )

            self.assertIsNone(
                signal
            )


if __name__ == "__main__":
    unittest.main()
