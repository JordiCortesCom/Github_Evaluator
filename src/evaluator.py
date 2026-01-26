"""
Main evaluation orchestrator.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.github_client import GitHubClient
from src.metrics import MetricsExtractor
from src.grader import GradingEngine

logger = logging.getLogger(__name__)


class StudentEvaluator:
    """Main evaluator orchestrating the grading process."""
    
    def __init__(self, config: Dict):
        """Initialize evaluator with configuration."""
        self.config = config
        self.github = GitHubClient(config["github"]["token"])
        self.metrics = MetricsExtractor(config)
        self.grader = GradingEngine(config)
        self.results = []
    
    def evaluate_organization(self, org: str, pattern: str = None) -> List[Dict]:
        """
        Evaluate all repositories in an organization.
        
        Args:
            org: Organization name
            pattern: Optional repository name pattern filter
        
        Returns:
            List of evaluation results
        """
        repos = self.github.get_organization_repos(org, pattern)
        
        for repo in repos:
            logger.info(f"Evaluating {repo.name}...")
            result = self.evaluate_repository(repo)
            self.results.append(result)
        
        return self.results
    
    def evaluate_repository(self, repo) -> Dict:
        """
        Evaluate a single repository.
        
        Args:
            repo: GitHub Repository object
        
        Returns:
            Evaluation result dictionary
        """
        # Extract configuration
        eval_config = self.config.get("evaluation", {})
        try:
            start_date = datetime.fromisoformat(eval_config.get("start_date", "2024-01-01"))
            end_date = datetime.fromisoformat(eval_config.get("end_date", "2024-12-31"))
        except ValueError as e:
            logger.error(f"Invalid date format in config: {e}. Use YYYY-MM-DD format.")
            raise ValueError(f"Invalid date format: {e}")
        
        # Fetch repository data
        commits = self.github.get_repo_commits(repo, start_date, end_date)
        branches = self.github.get_repo_branches(repo)
        prs = self.github.get_pull_requests(repo)
        
        # Analyze commits
        commit_analysis = self.github.analyze_commits(commits)
        
        # Calculate metrics
        freq_score, freq_details = self.metrics.calculate_commit_frequency_score(
            commit_analysis["total_commits"],
            len(commit_analysis["commits_by_author"])
        )
        
        qual_score, qual_details = self.metrics.calculate_commit_quality_score(
            commit_analysis["message_lengths"]
        )
        
        contrib_score, contrib_details = self.metrics.calculate_individual_contribution_score(
            commit_analysis["commits_by_author"]
        )
        
        branch_score, branch_details = self.metrics.calculate_branch_strategy_score(
            branches,
            commit_analysis["total_commits"]
        )
        
        repo_data = {
            "has_readme": self._check_readme(repo),
            "description": repo.description
        }
        doc_score, doc_details = self.metrics.calculate_documentation_score(repo_data)
        
        # Compile metrics
        all_metrics = {
            "commit_frequency": (freq_score, freq_details),
            "commit_quality": (qual_score, qual_details),
            "individual_contribution": (contrib_score, contrib_details),
            "branch_strategy": (branch_score, branch_details),
            "documentation": (doc_score, doc_details)
        }
        
        # Calculate final score
        final_score, breakdown = self.grader.calculate_final_score(all_metrics)
        
        # Extract student name from repo name
        student_name = self._extract_student_name(repo.name)
        
        # Generate report
        report = self.grader.generate_student_report(
            student_name,
            repo.name,
            breakdown,
            final_score
        )
        
        return report
    
    def _check_readme(self, repo) -> bool:
        """Check if repository has README file."""
        try:
            repo.get_contents("README.md")
            return True
        except Exception as e:
            logger.debug(f"Could not check README in {repo.name}: {e}")
            return False
    
    def _extract_student_name(self, repo_name: str) -> str:
        """Extract student name from repository name."""
        # Assuming format: assignment-username or similar
        parts = repo_name.split("-")
        if len(parts) > 1:
            return "-".join(parts[1:])
        return repo_name
