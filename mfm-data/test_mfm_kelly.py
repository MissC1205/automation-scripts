"""Offline regression checks for MFM Kelly shadow/EV gate."""
import unittest
from mfm_kelly import (bookmaker_indices, kelly_stake, market_snapshot_shadow,
                       no_vig_market_probabilities)

class KellyTests(unittest.TestCase):
    def test_probabilities(self):
        p = no_vig_market_probabilities({"home": 2.0, "draw": 3.5, "away": 4.0})
        self.assertAlmostEqual(sum(p.values()), 1)
        self.assertAlmostEqual(p["home"], .5 / (.5 + 1/3.5 + .25))
    def test_bad_odds(self):
        with self.assertRaises(ValueError):
            no_vig_market_probabilities({"home": 0, "draw": 3, "away": 4})
    def test_one_bookmaker_not_enough(self):
        result = bookmaker_indices({"one": {"home": 2, "draw": 3, "away": 4}},
                                   distinct_bookmakers_verified=True)
        self.assertEqual(result["status"], "UNAVAILABLE_NEEDS_TWO_DISTINCT_BOOKMAKERS")
    def test_two_bookmakers_shadow(self):
        odds = {"one": {"home": 2, "draw": 3.2, "away": 4},
                "two": {"home": 2.2, "draw": 3.1, "away": 3.8}}
        result = bookmaker_indices(odds, distinct_bookmakers_verified=True)
        self.assertEqual(result["status"], "SHADOW_MARKET_ONLY")
        self.assertGreaterEqual(result["dispersion"]["home"], 0)
    def test_stake_missing_gate(self):
        result = kelly_stake(.6, 1.9, calibrated=True, official_sp_verified=True)
        self.assertIsNone(result["suggested_fraction"])
    def test_fractional_kelly_capped(self):
        result = kelly_stake(.6, 1.9, calibrated=True,
                             official_sp_verified=True, forecast_frozen_before_market=True)
        self.assertAlmostEqual(result["full_kelly"], (.6 * 1.9 - 1) / .9)
        self.assertEqual(result["suggested_fraction"], .01)
    def test_negative_ev_no_bet(self):
        result = kelly_stake(.3, 2, calibrated=True, official_sp_verified=True,
                             forecast_frozen_before_market=True)
        self.assertEqual(result["status"], "NON_POSITIVE_EV_NO_BET")
        self.assertEqual(result["suggested_fraction"], 0)
    def test_caidao_does_not_create_stake(self):
        payload = {"sale_date_bj": "2026-10-16", "matches": [{
            "match_id": "F20261016001", "jc_number": "周五001",
            "market": {"spf": {"home": 2.17, "draw": 3.40, "away": 2.67}}}]}
        row = market_snapshot_shadow(payload)["matches"][0]
        self.assertEqual(row["bookmaker_kelly_status"],
                         "UNAVAILABLE_NEEDS_VERIFIED_MULTI_BOOKMAKER_QUOTES")
        self.assertEqual(row["stake_kelly_status"],
                         "BLOCKED_REQUIRES_FROZEN_CALIBRATED_MODEL_AND_OFFICIAL_SP")

if __name__ == "__main__":
    unittest.main()
