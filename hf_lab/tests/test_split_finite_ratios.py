import unittest

from hf_lab.splits import chronological_split


class ChronologicalSplitFiniteRatioTests(unittest.TestCase):
    def test_nonfinite_ratios_fail_closed(self):
        for field in ("train_ratio", "validation_ratio", "test_ratio"):
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=field, value=value):
                    with self.assertRaises(ValueError):
                        chronological_split(tuple(range(30)), **{field: value})

    def test_valid_chronological_split(self):
        split = chronological_split(tuple(range(30)))
        self.assertEqual((len(split.train), len(split.validation), len(split.test)), (18, 6, 6))
        self.assertLess(split.train[-1], split.validation[0])
        self.assertLess(split.validation[-1], split.test[0])
