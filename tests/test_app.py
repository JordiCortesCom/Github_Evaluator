"""
Tests for the Flask web application (app.py).
"""

import json
import unittest
from unittest.mock import MagicMock, patch

# Make sure the app module can be imported in test context.
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app


class FlaskAppTestCase(unittest.TestCase):
    """Base test case that sets up the Flask test client."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        app.secret_key = "test-secret-key"
        self.client = app.test_client()

    # ── Index / control panel ──────────────────────────────────────────

    def test_index_returns_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_index_contains_form_elements(self):
        resp = self.client.get("/")
        html = resp.data.decode()
        self.assertIn("token", html)
        self.assertIn("org", html)
        self.assertIn("start_date", html)
        self.assertIn("end_date", html)
        self.assertIn("scoring_commit_frequency", html)

    def test_index_contains_scoring_weights(self):
        resp = self.client.get("/")
        html = resp.data.decode()
        for key in [
            "commit_frequency",
            "commit_quality",
            "individual_contribution",
            "branch_strategy",
            "documentation",
        ]:
            self.assertIn(key, html)

    # ── /evaluate validation ───────────────────────────────────────────

    def test_evaluate_missing_token_redirects(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": ""}, clear=False):
            resp = self.client.post(
                "/evaluate",
                data={"org": "my-org", "scoring_commit_frequency": "25",
                      "scoring_commit_quality": "25",
                      "scoring_individual_contribution": "30",
                      "scoring_branch_strategy": "10",
                      "scoring_documentation": "10"},
                follow_redirects=True,
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"token is required", resp.data.lower())

    def test_evaluate_missing_org_and_assignment_redirects(self):
        resp = self.client.post(
            "/evaluate",
            data={"token": "ghp_fake",
                  "scoring_commit_frequency": "25",
                  "scoring_commit_quality": "25",
                  "scoring_individual_contribution": "30",
                  "scoring_branch_strategy": "10",
                  "scoring_documentation": "10"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"organization", resp.data.lower())

    def test_evaluate_bad_weights_redirects(self):
        resp = self.client.post(
            "/evaluate",
            data={"token": "ghp_fake", "org": "my-org",
                  "scoring_commit_frequency": "10",
                  "scoring_commit_quality": "10",
                  "scoring_individual_contribution": "10",
                  "scoring_branch_strategy": "10",
                  "scoring_documentation": "10"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"100", resp.data)

    # ── /results without session data ─────────────────────────────────

    def test_results_without_session_redirects(self):
        resp = self.client.get("/results", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"evaluation", resp.data.lower())

    # ── /results with injected session data ───────────────────────────

    def _inject_results(self, results):
        """Inject evaluation results directly into the Flask session."""
        with self.client.session_transaction() as sess:
            sess["results"] = results
            sess["evaluated_at"] = "2024-06-01T12:00:00"
            sess["org"] = "test-org"

    def _make_result(self, student="alice", score=85.0, grade="B"):
        return {
            "student": student,
            "repository": f"repo-{student}",
            "final_score": score,
            "letter_grade": grade,
            "feedback": "Good job",
            "metrics": {
                "commit_frequency": {"score": 80.0, "weight": 25, "weighted_contribution": 20.0, "details": {}},
                "commit_quality": {"score": 85.0, "weight": 25, "weighted_contribution": 21.25, "details": {}},
                "individual_contribution": {"score": 90.0, "weight": 30, "weighted_contribution": 27.0, "details": {}},
                "branch_strategy": {"score": 75.0, "weight": 10, "weighted_contribution": 7.5, "details": {}},
                "documentation": {"score": 100.0, "weight": 10, "weighted_contribution": 10.0, "details": {}},
            },
        }

    def test_results_page_renders_with_data(self):
        results = [
            self._make_result("alice", 85.0, "B"),
            self._make_result("bob", 72.0, "C"),
        ]
        self._inject_results(results)
        resp = self.client.get("/results")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode()
        self.assertIn("alice", html)
        self.assertIn("bob", html)
        self.assertIn("85.0", html)
        self.assertIn("72.0", html)

    def test_results_page_contains_chart_data(self):
        results = [self._make_result("carol", 91.0, "A")]
        self._inject_results(results)
        resp = self.client.get("/results")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode()
        self.assertIn("scoreChart", html)
        self.assertIn("gradeChart", html)
        self.assertIn("radarChart", html)
        self.assertIn("metricBarChart", html)

    def test_results_page_shows_statistics(self):
        results = [
            self._make_result("dave", 90.0, "A"),
            self._make_result("eve", 60.0, "D"),
        ]
        self._inject_results(results)
        resp = self.client.get("/results")
        html = resp.data.decode()
        # Average of 90 and 60 is 75
        self.assertIn("75.0", html)
        self.assertIn("90.0", html)
        self.assertIn("60.0", html)

    # ── /clear ─────────────────────────────────────────────────────────

    def test_clear_removes_session_and_redirects(self):
        self._inject_results([self._make_result()])
        resp = self.client.get("/clear", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertNotIn("results", sess)

    # ── /evaluate with mocked evaluator ───────────────────────────────

    @patch("src.evaluator.StudentEvaluator")
    def test_evaluate_org_calls_evaluator(self, MockEvaluator):
        fake_result = [self._make_result("frank", 88.0, "B")]
        instance = MockEvaluator.return_value
        instance.evaluate_organization.return_value = fake_result

        resp = self.client.post(
            "/evaluate",
            data={
                "token": "ghp_fake",
                "org": "my-org",
                "pattern": "",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "scoring_commit_frequency": "25",
                "scoring_commit_quality": "25",
                "scoring_individual_contribution": "30",
                "scoring_branch_strategy": "10",
                "scoring_documentation": "10",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        instance.evaluate_organization.assert_called_once_with("my-org", None)
        self.assertIn(b"frank", resp.data)

    @patch("src.evaluator.StudentEvaluator")
    def test_evaluate_assignment_id_calls_evaluator(self, MockEvaluator):
        fake_result = [self._make_result("grace", 95.0, "A")]
        instance = MockEvaluator.return_value
        instance.evaluate_classroom_assignment.return_value = fake_result

        resp = self.client.post(
            "/evaluate",
            data={
                "token": "ghp_fake",
                "assignment_id": "9999",
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "scoring_commit_frequency": "25",
                "scoring_commit_quality": "25",
                "scoring_individual_contribution": "30",
                "scoring_branch_strategy": "10",
                "scoring_documentation": "10",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        instance.evaluate_classroom_assignment.assert_called_once_with(9999)
        self.assertIn(b"grace", resp.data)

    @patch("src.evaluator.StudentEvaluator")
    def test_evaluate_empty_results_flashes_warning(self, MockEvaluator):
        instance = MockEvaluator.return_value
        instance.evaluate_organization.return_value = []

        resp = self.client.post(
            "/evaluate",
            data={
                "token": "ghp_fake",
                "org": "empty-org",
                "scoring_commit_frequency": "25",
                "scoring_commit_quality": "25",
                "scoring_individual_contribution": "30",
                "scoring_branch_strategy": "10",
                "scoring_documentation": "10",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"No repositories", resp.data)

    @patch("src.evaluator.StudentEvaluator")
    def test_evaluate_exception_flashes_error(self, MockEvaluator):
        instance = MockEvaluator.return_value
        instance.evaluate_organization.side_effect = RuntimeError("API error")

        resp = self.client.post(
            "/evaluate",
            data={
                "token": "ghp_fake",
                "org": "broken-org",
                "scoring_commit_frequency": "25",
                "scoring_commit_quality": "25",
                "scoring_individual_contribution": "30",
                "scoring_branch_strategy": "10",
                "scoring_documentation": "10",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Evaluation failed", resp.data)


if __name__ == "__main__":
    unittest.main()
