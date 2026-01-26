"""
Metrics extraction and analysis for student repositories.
"""

from typing import Dict, List, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsExtractor:
    """Extract and calculate evaluation metrics from repository data."""
    
    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.commit_config = config.get("commit_quality", {})
        self.contribution_config = config.get("contribution", {})
    
    def calculate_commit_frequency_score(self, total_commits: int, num_contributors: int) -> Tuple[float, Dict]:
        """
        Calculate commit frequency metric.
        
        Args:
            total_commits: Total number of commits
            num_contributors: Number of contributors
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        # Expectation: ~5-10 commits per contributor is ideal
        expected_commits_per_person = 7
        ideal_total = expected_commits_per_person * num_contributors
        
        if total_commits == 0:
            return 0, {"total_commits": 0, "num_contributors": num_contributors}
        
        # Score: how close to ideal distribution
        frequency_ratio = min(total_commits / ideal_total, 1.5)  # Cap at 1.5x
        score = frequency_ratio * 100
        score = min(score, 100)
        
        return score, {
            "total_commits": total_commits,
            "num_contributors": num_contributors,
            "avg_commits_per_person": total_commits / num_contributors if num_contributors > 0 else 0
        }
    
    def calculate_commit_quality_score(self, message_lengths: List[int]) -> Tuple[float, Dict]:
        """
        Calculate commit message quality.
        
        Args:
            message_lengths: List of commit message lengths in characters
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        if not message_lengths:
            return 0, {"average_length": 0, "quality_percentage": 0}
        
        min_length = self.commit_config.get("min_length", 10)
        good_length = self.commit_config.get("good_length", 50)
        
        # Count messages meeting quality thresholds
        good_messages = sum(1 for m in message_lengths if m >= good_length)
        acceptable_messages = sum(1 for m in message_lengths if m >= min_length)
        
        avg_length = sum(message_lengths) / len(message_lengths)
        
        # Scoring logic
        if acceptable_messages == len(message_lengths):
            # All messages meet minimum
            score = 50 + (good_messages / len(message_lengths)) * 50
        else:
            # Some messages too short
            score = (acceptable_messages / len(message_lengths)) * 100
        
        return min(score, 100), {
            "average_length": round(avg_length, 2),
            "good_messages": good_messages,
            "acceptable_messages": acceptable_messages,
            "total_messages": len(message_lengths),
            "quality_percentage": round((good_messages / len(message_lengths)) * 100, 2) if message_lengths else 0
        }
    
    def calculate_individual_contribution_score(self, commits_by_author: Dict[str, int]) -> Tuple[float, Dict]:
        """
        Calculate individual contribution balance.
        Penalizes if one person did too much work.
        
        Args:
            commits_by_author: Dict of {author: commit_count}
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        if not commits_by_author:
            return 0, {"distribution": {}, "anomaly_detected": False}
        
        total_commits = sum(commits_by_author.values())
        anomaly_threshold = self.contribution_config.get("flag_anomaly", 0.8)
        
        # Calculate percentage per person
        distribution = {
            author: (count / total_commits) * 100
            for author, count in commits_by_author.items()
        }
        
        # Check for imbalance
        max_percentage = max(distribution.values())
        min_percentage = min(distribution.values())
        
        anomaly_detected = max_percentage > (anomaly_threshold * 100)
        
        # Ideal: equal distribution
        # Score based on how balanced the distribution is
        if len(commits_by_author) == 1:
            score = 30  # Solo work gets low score
        else:
            # Gini coefficient-like approach
            # Closer to equal = higher score
            avg_percentage = 100 / len(commits_by_author)
            variance = sum((pct - avg_percentage) ** 2 for pct in distribution.values()) / len(distribution)
            
            # Max variance when one person has 100%
            max_variance = (avg_percentage ** 2) * len(commits_by_author)
            
            if max_variance == 0:
                score = 100
            else:
                score = (1 - (variance / max_variance)) * 100
            
            if anomaly_detected:
                score *= 0.7  # Reduce score if imbalance detected
        
        return min(score, 100), {
            "distribution": {k: round(v, 2) for k, v in distribution.items()},
            "max_percentage": round(max_percentage, 2),
            "min_percentage": round(min_percentage, 2),
            "num_contributors": len(commits_by_author),
            "anomaly_detected": anomaly_detected
        }
    
    def calculate_branch_strategy_score(self, branches: List[str], total_commits: int) -> Tuple[float, Dict]:
        """
        Calculate branch strategy usage.
        
        Args:
            branches: List of branch names
            total_commits: Total commits in repo
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        # Good practices: multiple branches, feature branches, main/master clean
        branch_count = len(branches)
        
        # Ideal: 3-5 branches (main + dev + 2-3 feature branches)
        ideal_branches = 4
        
        score = 50  # Base score
        
        # Points for multiple branches
        if branch_count >= 2:
            score += 30
        if branch_count >= 3:
            score += 15
        if branch_count >= 4:
            score += 5
        
        # Check for common good practices
        branch_names_lower = [b.lower() for b in branches]
        if "develop" in branch_names_lower or "dev" in branch_names_lower:
            score += 5
        if "feature" in str(branch_names_lower):
            score += 5
        
        return min(score, 100), {
            "branch_count": branch_count,
            "branches": branches,
            "has_main": "main" in branch_names_lower or "master" in branch_names_lower
        }
    
    def calculate_documentation_score(self, repo_data: Dict) -> Tuple[float, Dict]:
        """
        Calculate documentation presence.
        
        Args:
            repo_data: Repository metadata
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        score = 50  # Base score
        
        # Check for README
        if repo_data.get("has_readme"):
            score += 30
        
        # Check for description
        if repo_data.get("description"):
            score += 20
        
        return min(score, 100), {
            "has_readme": repo_data.get("has_readme", False),
            "has_description": bool(repo_data.get("description")),
            "description": repo_data.get("description", "")
        }
