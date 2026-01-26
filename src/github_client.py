"""
GitHub API client for fetching student repository data.
"""

import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import logging

from github import Github, GithubException
from github.Repository import Repository
from github.Commit import Commit

logger = logging.getLogger(__name__)
# Suppress overly verbose GitHub library logs
logging.getLogger("github").setLevel(logging.WARNING)


class GitHubClient:
    """Client for interacting with GitHub API."""
    
    def __init__(self, token: str):
        """Initialize GitHub client with authentication token."""
        if not token:
            raise ValueError("GitHub token is required")
        self.github = Github(token)
        try:
            self.user = self.github.get_user()
            logger.info(f"Authenticated as: {self.user.login}")
        except GithubException as e:
            raise ValueError(f"Failed to authenticate with GitHub: {e}")
    
    def get_organization_repos(self, org: str, repo_pattern: str = None) -> List[Repository]:
        """
        Fetch all repositories in an organization.
        
        Args:
            org: Organization name
            repo_pattern: Optional filter pattern (e.g., 'assignment-')
        
        Returns:
            List of Repository objects
        """
        try:
            organization = self.github.get_organization(org)
            repos = list(organization.get_repos())
            
            if repo_pattern:
                repos = [r for r in repos if repo_pattern in r.name]
            
            logger.info(f"Found {len(repos)} repositories in {org}")
            return repos
        except GithubException as e:
            logger.error(f"Error fetching repositories: {e}")
            return []
    
    def get_repo_commits(
        self,
        repo: Repository,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Commit]:
        """
        Fetch all commits from a repository within a date range.
        
        Args:
            repo: Repository object
            since: Start date (optional)
            until: End date (optional)
        
        Returns:
            List of Commit objects
        """
        try:
            commits = list(repo.get_commits(since=since, until=until))
            logger.info(f"Found {len(commits)} commits in {repo.name}")
            return commits
        except GithubException as e:
            logger.error(f"Error fetching commits from {repo.name}: {e}")
            return []
    
    def analyze_commits(self, commits: List[Commit]) -> Dict:
        """
        Analyze commits for frequency and patterns.
        
        Args:
            commits: List of commits to analyze
        
        Returns:
            Dictionary with commit analytics
        """
        if not commits:
            return {
                "total_commits": 0,
                "commits_by_author": {},
                "average_message_length": 0,
                "commits_by_date": {}
            }
        
        commits_by_author = {}
        message_lengths = []
        commits_by_date = {}
        
        for commit in commits:
            author = commit.author.login if commit.author else "unknown"
            message = commit.commit.message
            commit_date = commit.commit.author.date.date()
            
            # Count by author
            commits_by_author[author] = commits_by_author.get(author, 0) + 1
            
            # Message quality
            message_lengths.append(len(message))
            
            # Commits by date
            date_str = str(commit_date)
            commits_by_date[date_str] = commits_by_date.get(date_str, 0) + 1
        
        avg_message_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
        
        return {
            "total_commits": len(commits),
            "commits_by_author": commits_by_author,
            "average_message_length": avg_message_length,
            "commits_by_date": commits_by_date,
            "message_lengths": message_lengths
        }
    
    def get_repo_branches(self, repo: Repository) -> List[str]:
        """
        Get all branches from a repository.
        
        Args:
            repo: Repository object
        
        Returns:
            List of branch names
        """
        try:
            branches = [branch.name for branch in repo.get_branches()]
            return branches
        except GithubException as e:
            logger.error(f"Error fetching branches from {repo.name}: {e}")
            return []
    
    def get_pull_requests(self, repo: Repository) -> List:
        """
        Get all pull requests (closed and open).
        
        Args:
            repo: Repository object
        
        Returns:
            List of pull request objects
        """
        try:
            prs = list(repo.get_pulls(state="all"))
            return prs
        except GithubException as e:
            logger.error(f"Error fetching PRs from {repo.name}: {e}")
            return []
