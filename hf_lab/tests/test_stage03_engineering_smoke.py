"""Safety and reproducibility checks for the synthetic-only engineering cycle."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hf_lab.tools import omega_stage03_engineering_smoke_v1 as smoke


class Stage03SyntheticEngineeringTests(unittest.TestCase):
    def test_fixture_is_fixed_and_has_no_market_input(self):
        left, right = smoke.synthetic_bars(), smoke.synthetic_bars()
        self.assertEqual(left, right)
        self.assertEqual(len(left), 160)
        self.assertTrue(all(x.trades > 0 and x.low <= x.open <= x.high for x in left))
        self.assertTrue(all(a.time < b.time for a, b in zip(left, left[1:])))

    def test_fails_closed_without_approved_safety_state(self):
        safe = dict(status="DENIED", authorized=False, execution_started=False,
                    orders_allowed=False, mt5_allowed=False, holdout_allowed=False)
        for field, value in (("status", "AUTHORIZED"), ("authorized", True),
                             ("execution_started", True), ("orders_allowed", True),
                             ("mt5_allowed", True), ("holdout_allowed", True)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)
                (folder / "search_authorization_v1.json").write_text(
                    json.dumps(dict(safe, **{field: value})))
                with patch.object(smoke, "STATE", folder), patch.object(
                    smoke, "OUTPUT", folder / "report.json"
                ), patch.object(smoke, "run_replay", side_effect=AssertionError("REPLAY MUST NOT RUN")):
                    with self.assertRaisesRegex(RuntimeError, "SCIENTIFIC_GATE_NOT_DENIED|UNSAFE_RUNTIME"):
                        smoke.main()
                self.assertFalse((folder / "report.json").exists())

    def test_safe_run_is_repeated_deterministic_and_not_admission(self):
        safe = dict(status="DENIED", authorized=False, execution_started=False,
                    orders_allowed=False, mt5_allowed=False, holdout_allowed=False)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            (folder / "search_authorization_v1.json").write_text(json.dumps(safe))
            with patch.object(smoke, "STATE", folder), patch.object(smoke, "OUTPUT", folder / "report.json"):
                smoke.main()
                proof = json.loads((folder / "report.json").read_text())
                smoke.main()
                repeated = json.loads((folder / "report.json").read_text())
            self.assertEqual(proof, repeated)
            self.assertEqual(proof["closed_trades"], 83)
            self.assertEqual(proof["repeat_runs"], 2)
            self.assertEqual(proof["status"], "ENGINEERING_PASS_SCIENTIFIC_ADMISSION_STILL_DENIED")
            self.assertEqual(proof["scientific_decision"], "REJECT_ADMISSION_NO_REAL_MARKET_EVIDENCE")
            self.assertEqual(proof["source"], "GENERATED_SYNTHETIC_BARS_NO_MARKET_DATA")
            self.assertIs(proof["costs_empirically_calibrated"], False)
            diagnostic = proof["synthetic_diagnostic_only_not_market_performance"]
            self.assertEqual(diagnostic["trades"], proof["closed_trades"])
            self.assertEqual(diagnostic["wins"] + diagnostic["losses"], 83)
            self.assertGreaterEqual(diagnostic["max_drawdown_r"], 0.0)
            self.assertTrue(all(isinstance(value, (int, float)) for value in diagnostic.values()))
            for key in ("scientific_candidate_admitted", "search_executed",
                        "real_orders_executed", "performance_on_real_markets_claimed",
                        "research_execution_authorized", "orders_allowed", "mt5_allowed",
                        "holdout_allowed", "auto_promotion_allowed"):
                self.assertIs(proof[key], False)


if __name__ == "__main__":
    unittest.main()
