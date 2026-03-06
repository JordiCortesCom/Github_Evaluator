"""
Unit tests for ClassroomScraper.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.classroom_scraper import ClassroomScraper, GITHUB_API_BASE


class TestClassroomScraperInit(unittest.TestCase):
    def test_requires_token(self):
        with self.assertRaises(ValueError):
            ClassroomScraper("")

    def test_accepts_token(self):
        scraper = ClassroomScraper("ghp_test_token")
        self.assertIsNotNone(scraper)


class TestClassroomScraperListClassrooms(unittest.TestCase):
    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def _mock_get(self, responses):
        """Patch _get to return successive values from *responses*."""
        self.scraper._get = MagicMock(side_effect=responses)

    def test_returns_all_classrooms_single_page(self):
        classrooms = [{"id": 1, "name": "CS101"}, {"id": 2, "name": "CS202"}]
        self._mock_get([classrooms])
        result = self.scraper.list_classrooms()
        self.assertEqual(result, classrooms)

    def test_returns_empty_list_on_error(self):
        self._mock_get([None])
        result = self.scraper.list_classrooms()
        self.assertEqual(result, [])

    def test_paginates_when_full_page_returned(self):
        page1 = [{"id": i} for i in range(100)]
        page2 = [{"id": 100}]
        self._mock_get([page1, page2])
        result = self.scraper.list_classrooms()
        self.assertEqual(len(result), 101)


class TestClassroomScraperGetClassroom(unittest.TestCase):
    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def test_returns_classroom_dict(self):
        expected = {"id": 42, "name": "CS101"}
        self.scraper._get = MagicMock(return_value=expected)
        result = self.scraper.get_classroom(42)
        self.assertEqual(result, expected)
        self.scraper._get.assert_called_once_with("/classrooms/42")

    def test_returns_none_when_not_found(self):
        self.scraper._get = MagicMock(return_value=None)
        result = self.scraper.get_classroom(99)
        self.assertIsNone(result)


class TestClassroomScraperListAssignments(unittest.TestCase):
    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def test_returns_assignments(self):
        assignments = [{"id": 10, "title": "Lab 1"}, {"id": 11, "title": "Lab 2"}]
        self.scraper._get = MagicMock(side_effect=[assignments])
        result = self.scraper.list_assignments(1)
        self.assertEqual(result, assignments)

    def test_empty_when_none_returned(self):
        self.scraper._get = MagicMock(return_value=None)
        result = self.scraper.list_assignments(1)
        self.assertEqual(result, [])


class TestClassroomScraperListAcceptedAssignments(unittest.TestCase):
    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def test_returns_accepted_assignments(self):
        accepted = [
            {
                "id": 1,
                "submitted": True,
                "commit_count": 5,
                "grade": "",
                "students": [{"login": "alice"}],
                "repository": {
                    "name": "lab-1-alice",
                    "full_name": "org/lab-1-alice",
                    "html_url": "https://github.com/org/lab-1-alice",
                },
            }
        ]
        self.scraper._get = MagicMock(side_effect=[accepted])
        result = self.scraper.list_accepted_assignments(10)
        self.assertEqual(result, accepted)

    def test_returns_empty_list_on_none(self):
        self.scraper._get = MagicMock(return_value=None)
        result = self.scraper.list_accepted_assignments(10)
        self.assertEqual(result, [])


class TestClassroomScraperGetStudentRepositories(unittest.TestCase):
    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def _make_accepted(self, login, repo_name, submitted=True, commit_count=3, grade=""):
        return {
            "submitted": submitted,
            "commit_count": commit_count,
            "grade": grade,
            "students": [{"login": login}],
            "repository": {
                "name": repo_name,
                "full_name": f"org/{repo_name}",
                "html_url": f"https://github.com/org/{repo_name}",
            },
        }

    def test_maps_accepted_to_repo_dicts(self):
        accepted = [
            self._make_accepted("alice", "lab-1-alice"),
            self._make_accepted("bob", "lab-1-bob", submitted=False, commit_count=0),
        ]
        self.scraper._get = MagicMock(return_value=accepted)
        result = self.scraper.get_student_repositories(10)

        self.assertEqual(len(result), 2)

        alice_repo = result[0]
        self.assertEqual(alice_repo["student_login"], "alice")
        self.assertEqual(alice_repo["repo_name"], "lab-1-alice")
        self.assertEqual(alice_repo["full_name"], "org/lab-1-alice")
        self.assertTrue(alice_repo["submitted"])
        self.assertEqual(alice_repo["commit_count"], 3)
        self.assertEqual(alice_repo["students"], ["alice"])

        bob_repo = result[1]
        self.assertEqual(bob_repo["student_login"], "bob")
        self.assertFalse(bob_repo["submitted"])

    def test_unknown_student_when_no_students_list(self):
        entry = {
            "submitted": True,
            "commit_count": 1,
            "grade": "",
            "students": [],
            "repository": {
                "name": "lab-1-anon",
                "full_name": "org/lab-1-anon",
                "html_url": "https://github.com/org/lab-1-anon",
            },
        }
        self.scraper._get = MagicMock(return_value=[entry])
        result = self.scraper.get_student_repositories(10)
        self.assertEqual(result[0]["student_login"], "unknown")
        self.assertEqual(result[0]["students"], [])

    def test_returns_empty_list_when_no_accepted(self):
        self.scraper._get = MagicMock(return_value=None)
        result = self.scraper.get_student_repositories(10)
        self.assertEqual(result, [])


class TestClassroomScraperHTTP(unittest.TestCase):
    """Test the internal _get method with a real requests.Session mock."""

    def setUp(self):
        self.scraper = ClassroomScraper("ghp_token")

    def _mock_response(self, status_code, json_body=None):
        resp = MagicMock()
        resp.status_code = status_code
        resp.json.return_value = json_body or {}
        resp.text = ""
        return resp

    def test_get_returns_json_on_200(self):
        with patch.object(self.scraper._session, "get") as mock_get:
            mock_get.return_value = self._mock_response(200, {"id": 1})
            result = self.scraper._get("/classrooms/1")
            self.assertEqual(result, {"id": 1})

    def test_get_returns_none_on_404(self):
        with patch.object(self.scraper._session, "get") as mock_get:
            mock_get.return_value = self._mock_response(404)
            result = self.scraper._get("/classrooms/999")
            self.assertIsNone(result)

    def test_get_returns_none_on_401(self):
        with patch.object(self.scraper._session, "get") as mock_get:
            mock_get.return_value = self._mock_response(401)
            result = self.scraper._get("/classrooms")
            self.assertIsNone(result)

    def test_get_returns_none_on_request_exception(self):
        import requests as _requests
        with patch.object(
            self.scraper._session, "get", side_effect=_requests.RequestException("timeout")
        ):
            result = self.scraper._get("/classrooms")
            self.assertIsNone(result)

    def test_get_uses_correct_url(self):
        with patch.object(self.scraper._session, "get") as mock_get:
            mock_get.return_value = self._mock_response(200, [])
            self.scraper._get("/assignments/5/accepted_assignments", params={"per_page": 100})
            mock_get.assert_called_once_with(
                f"{GITHUB_API_BASE}/assignments/5/accepted_assignments",
                params={"per_page": 100},
                timeout=30,
            )


if __name__ == "__main__":
    unittest.main()
