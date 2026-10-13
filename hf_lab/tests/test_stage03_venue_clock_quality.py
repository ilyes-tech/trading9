"""Fail-closed unit tests for public feed clock-quality audit."""
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest

from hf_lab.tools import omega_stage03_venue_clock_quality_v1 as q


class VenueClockQualityTests(unittest.TestCase):
    def test_lags_are_venue_receive_differences_not_clock_certificates(self):
        stamp = dt.datetime(2026, 10, 13, tzinfo=dt.timezone.utc).timestamp()
        rows = [("2026-10-13T00:00:00Z", int((stamp + lag) * 1e9))
                for lag in (0.5, 0.9, 1.0, 6.0)]
        result = q.lag_statistics(rows)
        self.assertEqual(result["rows"], 4)
        self.assertEqual(result["lag_over_five_seconds_rows"], 1)
        self.assertEqual(result["negative_lag_rows"], 0)

    def test_invalid_event_time_is_rejected(self):
        for timestamp, received_ns in (("2026-10-13T00:00:00", 10),
                                       ("bad timestamp", 10),
                                       ("2026-10-13T00:00:00Z", "wrong")):
            with self.subTest(timestamp=timestamp, received_ns=received_ns):
                with self.assertRaises(ValueError):
                    q.lag_statistics([(timestamp, received_ns)])
        with self.assertRaises(ValueError):
            q.lag_statistics([])

    def test_live_gate_is_refused_without_touching_dataset(self):
        denied = {"status": "DENIED", "authorized": False,
                  "orders_allowed": False, "mt5_allowed": False,
                  "holdout_allowed": False}
        for changed in ({"authorized": True}, {"orders_allowed": True},
                        {"holdout_allowed": True}, {"status": "AUTHORIZED"}):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as td:
                state = Path(td)
                (state / "search_authorization_v1.json").write_text(
                    json.dumps({**denied, **changed}))
                with self.assertRaisesRegex(ValueError, "RESEARCH_GATE_NOT_DENIED"):
                    q.audit(state / "missing_capture", state)

    def test_report_never_claims_admission(self):
        report = q.audit()
        self.assertEqual(report["status"],
                         "TIMING_PROXIES_RECONCILED_NTP_NOT_VERIFIED_SCIENTIFIC_ADMISSION_DENIED")
        for flag in ("absolute_clock_accuracy_independently_verified",
                     "source_event_timestamps_independently_attested",
                     "scientific_candidate_admitted",
                     "research_execution_authorized", "search_executed",
                     "backtest_executed", "orders_allowed", "mt5_allowed",
                     "holdout_allowed", "auto_promotion_allowed"):
            self.assertIs(report[flag], False)


if __name__ == "__main__":
    unittest.main()
