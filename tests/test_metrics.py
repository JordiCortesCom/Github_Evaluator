"""
Unit tests for MetricsExtractor.
"""

import unittest
from datetime import datetime

from src.metrics import MetricsExtractor


def _make_extractor(overrides=None):
    """Return a MetricsExtractor with default config, optionally updated."""
    config = {
        "commit_frequency": {
            "ideal_commits_per_person": 7,
            "max_ratio": 1.5,
        },
        "commit_quality": {
            "min_length": 10,
            "good_length": 50,
        },
        "contribution": {
            "flag_anomaly": 0.8,
            "solo_score": 30,
            "anomaly_penalty": 0.7,
        },
        "branch_strategy": {
            "base_score": 50,
            "two_branch_bonus": 30,
            "three_branch_bonus": 15,
            "four_branch_bonus": 5,
            "develop_branch_bonus": 5,
            "feature_branch_bonus": 5,
        },
        "documentation": {
            "base_score": 50,
            "readme_bonus": 30,
            "description_bonus": 20,
        },
        "commit_timestamps": {
            "min_active_days_ratio": 0.1,
            "good_active_days_ratio": 0.3,
            "last_minute_days": 3,
            "last_minute_threshold": 0.5,
        },
    }
    if overrides:
        config.update(overrides)
    return MetricsExtractor(config)


class TestCommitFrequencyScore(unittest.TestCase):
    def setUp(self):
        self.extractor = _make_extractor()

    def test_zero_commits_returns_zero(self):
        score, details = self.extractor.calculate_commit_frequency_score(0, 2)
        self.assertEqual(score, 0)

    def test_ideal_commits_returns_100(self):
        # 7 commits per person * 2 people = 14 commits → ratio 1.0 → score 100
        score, details = self.extractor.calculate_commit_frequency_score(14, 2)
        self.assertAlmostEqual(score, 100.0)

    def test_exceeding_max_ratio_caps_at_100(self):
        # 100 commits for 2 people (ratio > 1.5) should cap at 100
        score, _ = self.extractor.calculate_commit_frequency_score(100, 2)
        self.assertEqual(score, 100.0)

    def test_partial_commits_scales_linearly(self):
        # 7 commits for 2 people → 7/14 = 0.5 → score 50
        score, _ = self.extractor.calculate_commit_frequency_score(7, 2)
        self.assertAlmostEqual(score, 50.0)

    def test_config_ideal_commits_per_person_used(self):
        extractor = _make_extractor({"commit_frequency": {"ideal_commits_per_person": 10, "max_ratio": 1.5}})
        # 10 commits for 1 person → ratio 1.0 → 100
        score, _ = extractor.calculate_commit_frequency_score(10, 1)
        self.assertAlmostEqual(score, 100.0)


class TestCommitQualityScore(unittest.TestCase):
    def setUp(self):
        self.extractor = _make_extractor()

    def test_empty_messages_returns_zero(self):
        score, details = self.extractor.calculate_commit_quality_score([])
        self.assertEqual(score, 0)

    def test_all_good_messages_returns_100(self):
        # All messages >= 50 chars → good
        score, _ = self.extractor.calculate_commit_quality_score([60, 70, 80])
        self.assertAlmostEqual(score, 100.0)

    def test_all_acceptable_no_good_returns_50(self):
        # All >= 10 but none >= 50
        score, _ = self.extractor.calculate_commit_quality_score([15, 20, 25])
        self.assertAlmostEqual(score, 50.0)

    def test_some_too_short_penalises(self):
        # 1 out of 2 messages meets minimum → 50% → score 50
        score, _ = self.extractor.calculate_commit_quality_score([5, 15])
        self.assertAlmostEqual(score, 50.0)

    def test_config_min_length_respected(self):
        extractor = _make_extractor({"commit_quality": {"min_length": 20, "good_length": 50}})
        # Message of length 15 is below new min_length
        score, details = extractor.calculate_commit_quality_score([15])
        self.assertAlmostEqual(score, 0.0)
        self.assertEqual(details["acceptable_messages"], 0)


class TestIndividualContributionScore(unittest.TestCase):
    def setUp(self):
        self.extractor = _make_extractor()

    def test_empty_returns_zero(self):
        score, _ = self.extractor.calculate_individual_contribution_score({})
        self.assertEqual(score, 0)

    def test_solo_uses_config_solo_score(self):
        score, _ = self.extractor.calculate_individual_contribution_score({"alice": 10})
        self.assertEqual(score, 30)  # Default solo_score

    def test_equal_distribution_returns_100(self):
        score, _ = self.extractor.calculate_individual_contribution_score({"alice": 5, "bob": 5})
        self.assertAlmostEqual(score, 100.0)

    def test_anomaly_applies_penalty(self):
        # alice has 90% > 80% threshold → anomaly detected
        score, details = self.extractor.calculate_individual_contribution_score({"alice": 9, "bob": 1})
        self.assertTrue(details["anomaly_detected"])
        self.assertLess(score, 100.0)

    def test_config_solo_score_used(self):
        extractor = _make_extractor({
            "contribution": {"flag_anomaly": 0.8, "solo_score": 50, "anomaly_penalty": 0.7}
        })
        score, _ = extractor.calculate_individual_contribution_score({"alice": 10})
        self.assertEqual(score, 50)

    def test_config_anomaly_penalty_used(self):
        extractor = _make_extractor({
            "contribution": {"flag_anomaly": 0.8, "solo_score": 30, "anomaly_penalty": 0.5}
        })
        # Two contributors but one dominates
        score_penalised, _ = extractor.calculate_individual_contribution_score({"alice": 9, "bob": 1})
        # With default penalty 0.7 the score would be higher
        extractor_default = _make_extractor()
        score_default, _ = extractor_default.calculate_individual_contribution_score({"alice": 9, "bob": 1})
        self.assertLess(score_penalised, score_default)


class TestBranchStrategyScore(unittest.TestCase):
    def setUp(self):
        self.extractor = _make_extractor()

    def test_single_branch_returns_base_score(self):
        score, details = self.extractor.calculate_branch_strategy_score(["main"], 5)
        self.assertEqual(score, 50)

    def test_two_branches_adds_bonus(self):
        score, _ = self.extractor.calculate_branch_strategy_score(["main", "hotfix-1"], 5)
        self.assertEqual(score, 80)  # 50 + 30

    def test_develop_branch_adds_bonus(self):
        score, _ = self.extractor.calculate_branch_strategy_score(["main", "develop"], 5)
        self.assertEqual(score, 85)  # 50 + 30 + 5

    def test_feature_branch_adds_bonus(self):
        score, _ = self.extractor.calculate_branch_strategy_score(["main", "feature/login"], 5)
        self.assertEqual(score, 85)  # 50 + 30 + 5

    def test_four_branches_caps_at_100(self):
        branches = ["main", "develop", "feature/a", "feature/b"]
        score, _ = self.extractor.calculate_branch_strategy_score(branches, 10)
        # 50 + 30 + 15 + 5 + 5(develop) + 5(feature) = 110 → capped at 100
        self.assertEqual(score, 100)

    def test_config_bonuses_used(self):
        extractor = _make_extractor({
            "branch_strategy": {
                "base_score": 0,
                "two_branch_bonus": 10,
                "three_branch_bonus": 10,
                "four_branch_bonus": 10,
                "develop_branch_bonus": 10,
                "feature_branch_bonus": 10,
            }
        })
        score, _ = extractor.calculate_branch_strategy_score(["main", "develop"], 5)
        self.assertEqual(score, 20)  # 0 + 10 + 10


class TestDocumentationScore(unittest.TestCase):
    def setUp(self):
        self.extractor = _make_extractor()

    def test_no_readme_no_description_returns_base(self):
        score, _ = self.extractor.calculate_documentation_score({})
        self.assertEqual(score, 50)

    def test_readme_adds_bonus(self):
        score, _ = self.extractor.calculate_documentation_score({"has_readme": True})
        self.assertEqual(score, 80)  # 50 + 30

    def test_description_adds_bonus(self):
        score, _ = self.extractor.calculate_documentation_score({"description": "A repo"})
        self.assertEqual(score, 70)  # 50 + 20

    def test_readme_and_description_returns_100(self):
        score, _ = self.extractor.calculate_documentation_score(
            {"has_readme": True, "description": "A repo"}
        )
        self.assertEqual(score, 100)

    def test_config_bonuses_used(self):
        extractor = _make_extractor({
            "documentation": {"base_score": 0, "readme_bonus": 60, "description_bonus": 40}
        })
        score, _ = extractor.calculate_documentation_score({"has_readme": True, "description": "x"})
        self.assertEqual(score, 100)


class TestCommitTimestampsScore(unittest.TestCase):
    """Tests for the commit timestamp distribution metric."""

    START = datetime(2024, 1, 1)
    END = datetime(2024, 1, 30)  # 30-day window

    def setUp(self):
        self.extractor = _make_extractor()

    def test_empty_commits_returns_zero(self):
        score, details = self.extractor.calculate_commit_timestamps_score({}, self.START, self.END)
        self.assertEqual(score, 0)
        self.assertFalse(details["last_minute_detected"])

    def test_well_spread_commits_scores_100(self):
        # Active on 10 consecutive days (Jan 1-10) → ratio = 10/30 ≈ 0.33 >= good_ratio (0.3)
        commits = {f"2024-01-{d:02d}": 1 for d in range(1, 11)}  # 10 days out of 30
        score, details = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertEqual(score, 100.0)
        self.assertFalse(details["last_minute_detected"])

    def test_low_spread_scores_between_0_and_50(self):
        # 1 day out of 30 → ratio = 0.033, below min_ratio (0.1)
        commits = {"2024-01-01": 5}
        score, details = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertLess(score, 50.0)

    def test_last_minute_commits_penalised(self):
        # All commits on last 3 days → last_minute_ratio = 1.0 > threshold 0.5
        commits = {"2024-01-28": 2, "2024-01-29": 2, "2024-01-30": 2}
        score, details = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertTrue(details["last_minute_detected"])
        self.assertLess(score, 50.0)  # Penalised

    def test_mixed_commits_not_last_minute(self):
        # Most commits early, only a few last-minute
        commits = {f"2024-01-{d:02d}": 3 for d in range(1, 25)}  # days 1–24
        commits["2024-01-29"] = 1  # One last-minute commit
        score, details = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertFalse(details["last_minute_detected"])

    def test_score_capped_at_100(self):
        # Dense commit history should not exceed 100
        commits = {f"2024-01-{d:02d}": 10 for d in range(1, 31)}
        score, _ = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertLessEqual(score, 100.0)

    def test_config_ratios_respected(self):
        extractor = _make_extractor({
            "commit_timestamps": {
                "min_active_days_ratio": 0.5,  # Higher threshold
                "good_active_days_ratio": 0.9,
                "last_minute_days": 3,
                "last_minute_threshold": 0.5,
            }
        })
        # 10 active days out of 30 → ratio 0.33 → below new min_ratio (0.5)
        commits = {f"2024-01-{d:02d}": 1 for d in range(1, 11)}
        score, _ = extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        # Below min_ratio → score < 50
        self.assertLess(score, 50.0)

    def test_last_minute_boundary_exact_days(self):
        # With last_minute_days=3 and end_date=Jan 30, the window is Jan 28-30 (3 days).
        # A commit on Jan 27 (one day before the window) should NOT be last-minute.
        commits_before = {"2024-01-27": 10}
        _, details_before = self.extractor.calculate_commit_timestamps_score(
            commits_before, self.START, self.END
        )
        self.assertFalse(details_before["last_minute_detected"])

        # A commit on Jan 28 (first day of the window) should count as last-minute.
        commits_inside = {"2024-01-28": 10}
        _, details_inside = self.extractor.calculate_commit_timestamps_score(
            commits_inside, self.START, self.END
        )
        self.assertTrue(details_inside["last_minute_detected"])

    def test_active_days_ratio_reported(self):
        commits = {"2024-01-01": 1, "2024-01-02": 1, "2024-01-03": 1}  # 3 days out of 30
        _, details = self.extractor.calculate_commit_timestamps_score(commits, self.START, self.END)
        self.assertEqual(details["active_days"], 3)
        self.assertEqual(details["total_days"], 30)
        self.assertAlmostEqual(details["active_days_ratio"], 0.1, places=2)


if __name__ == "__main__":
    unittest.main()
