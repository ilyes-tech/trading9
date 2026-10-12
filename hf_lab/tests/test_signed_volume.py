"""Feature contract tests on synthetic inputs only; no research execution."""

import unittest
from hf_lab.signed_volume import closed_m1_imbalance


class SignedVolumeTests(unittest.TestCase):
    def feature(self, buy=3.0, sell=7.0, start=120, now=180):
        return closed_m1_imbalance(bar_start=start, as_of=now,
                                   buy_volume=buy, sell_volume=sell)

    def test_closed_bar_boundary_prevents_early_availability(self):
        self.assertIsNone(self.feature(now=179.999))
        self.assertAlmostEqual(self.feature(now=180), -0.4)

    def test_zero_volume_is_missing_not_neutral(self):
        self.assertIsNone(self.feature(0, 0))
        self.assertEqual(self.feature(2, 2), 0)

    def test_side_direction_and_endpoints(self):
        self.assertEqual(self.feature(4, 0), 1)
        self.assertEqual(self.feature(0, 4), -1)
        self.assertAlmostEqual(self.feature(3, 7), -self.feature(7, 3))

    def test_scale_invariance_and_finite_extremes(self):
        self.assertAlmostEqual(self.feature(3, 7), self.feature(30, 70))
        self.assertEqual(self.feature(1e308, 1e308), 0)
        self.assertEqual(self.feature(1e-308, 0), 1)

    def test_invalid_values_fail_closed(self):
        for bad in (-1, float('nan'), float('inf'), -float('inf'), True, '2', 10**400):
            for key in ('buy', 'sell'):
                with self.subTest(value=repr(bad), key=key):
                    with self.assertRaises(ValueError):
                        self.feature(**{key: bad})

    def test_timestamp_contract(self):
        for kwargs in ({'start': 121}, {'start': -60}, {'now': -1},
                       {'start': float('nan')}, {'now': float('inf')},
                       {'start': True}, {'now': '180'}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    self.feature(**kwargs)


if __name__ == '__main__':
    unittest.main()
