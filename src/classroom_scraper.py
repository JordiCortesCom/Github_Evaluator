"""
GitHub Classroom API client for loading assignment repositories.

Uses the GitHub Classroom REST API to list classrooms, assignments,
and accepted student repositories for a given assignment.
"""

import logging
from typing import Any, List, Dict, Optional

import requests

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class ClassroomScraper:
    """Scrape student repository data from GitHub Classroom assignments."""

    def __init__(self, token: str):
        """
        Initialize the scraper with a GitHub personal access token.

        The token must have the ``manage_classrooms`` scope (or the legacy
        ``classroom`` scope) to access Classroom API endpoints.

        Args:
            token: GitHub personal access token.
        """
        if not token:
            raise ValueError("GitHub token is required")
        self._token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    # ------------------------------------------------------------------
    # Classroom helpers
    # ------------------------------------------------------------------

    def list_classrooms(self) -> List[Dict]:
        """
        Return all classrooms accessible with the current token.

        Returns:
            List of classroom dicts as returned by the GitHub API.
        """
        classrooms = []
        page = 1
        while True:
            resp = self._get(
                "/classrooms", params={"per_page": 100, "page": page}
            )
            if not resp:
                break
            classrooms.extend(resp)
            if len(resp) < 100:
                break
            page += 1
        logger.info("Found %d classroom(s)", len(classrooms))
        return classrooms

    def get_classroom(self, classroom_id: int) -> Optional[Dict]:
        """
        Return details for a single classroom.

        Args:
            classroom_id: Numeric classroom identifier.

        Returns:
            Classroom dict, or *None* if not found.
        """
        return self._get(f"/classrooms/{classroom_id}")

    # ------------------------------------------------------------------
    # Assignment helpers
    # ------------------------------------------------------------------

    def list_assignments(self, classroom_id: int) -> List[Dict]:
        """
        Return all assignments for a classroom.

        Args:
            classroom_id: Numeric classroom identifier.

        Returns:
            List of assignment dicts.
        """
        assignments = []
        page = 1
        while True:
            resp = self._get(
                f"/classrooms/{classroom_id}/assignments",
                params={"per_page": 100, "page": page},
            )
            if not resp:
                break
            assignments.extend(resp)
            if len(resp) < 100:
                break
            page += 1
        logger.info(
            "Found %d assignment(s) for classroom %d",
            len(assignments),
            classroom_id,
        )
        return assignments

    def get_assignment(self, assignment_id: int) -> Optional[Dict]:
        """
        Return details for a single assignment.

        Args:
            assignment_id: Numeric assignment identifier.

        Returns:
            Assignment dict, or *None* if not found.
        """
        return self._get(f"/assignments/{assignment_id}")

    # ------------------------------------------------------------------
    # Accepted-assignment (student repo) helpers
    # ------------------------------------------------------------------

    def list_accepted_assignments(self, assignment_id: int) -> List[Dict]:
        """
        Return all accepted assignments (student submissions) for an assignment.

        Each entry contains:
        - ``repository``: repository metadata dict (name, full_name, html_url, …)
        - ``students``: list of student account dicts
        - ``submitted``, ``passing``, ``commit_count``, ``grade`` fields

        Args:
            assignment_id: Numeric assignment identifier.

        Returns:
            List of accepted-assignment dicts.
        """
        accepted = []
        page = 1
        while True:
            resp = self._get(
                f"/assignments/{assignment_id}/accepted_assignments",
                params={"per_page": 100, "page": page},
            )
            if not resp:
                break
            accepted.extend(resp)
            if len(resp) < 100:
                break
            page += 1
        logger.info(
            "Found %d accepted assignment(s) for assignment %d",
            len(accepted),
            assignment_id,
        )
        return accepted

    def get_student_repositories(self, assignment_id: int) -> List[Dict]:
        """
        Return a list of student repository info dicts for an assignment.

        Each dict contains:
        - ``repo_name``: short repository name
        - ``full_name``: ``owner/repo`` string
        - ``html_url``: URL to the repository on GitHub
        - ``student_login``: primary student GitHub login
        - ``students``: list of all students on the submission
        - ``submitted``: whether the student submitted work
        - ``commit_count``: total commits reported by Classroom API
        - ``grade``: grade string (may be empty until graded)

        Args:
            assignment_id: Numeric assignment identifier.

        Returns:
            List of repository info dicts.
        """
        accepted = self.list_accepted_assignments(assignment_id)
        repos = []
        for entry in accepted:
            repo = entry.get("repository", {})
            students = entry.get("students", [])
            primary_login = students[0]["login"] if students else "unknown"
            repos.append(
                {
                    "repo_name": repo.get("name", ""),
                    "full_name": repo.get("full_name", ""),
                    "html_url": repo.get("html_url", ""),
                    "student_login": primary_login,
                    "students": [s.get("login") for s in students],
                    "submitted": entry.get("submitted", False),
                    "commit_count": entry.get("commit_count", 0),
                    "grade": entry.get("grade", ""),
                }
            )
        return repos

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
        params: Optional[Dict] = None,
    ) -> Optional[Any]:
        """
        Perform a GET request against the GitHub API.

        Args:
            path: API path (without base URL).
            params: Optional query parameters.

        Returns:
            Parsed JSON response, or *None* on error.
        """
        url = f"{GITHUB_API_BASE}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                logger.warning("Resource not found: %s", url)
            elif resp.status_code == 401:
                logger.error(
                    "Authentication failed for %s. Ensure the token has the "
                    "'manage_classrooms' scope.",
                    url,
                )
            else:
                logger.error(
                    "GitHub API error %d for %s: %s",
                    resp.status_code,
                    url,
                    resp.text[:200],
                )
            return None
        except requests.RequestException as exc:
            logger.error("Request failed for %s: %s", url, exc)
            return None
