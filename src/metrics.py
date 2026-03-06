"""
Metrics extraction and analysis for student repositories.
"""

from typing import Dict, List, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetricsExtractor:
    """Extract and calculate evaluation metrics from repository data."""
    
    def __init__(self, config: Dict):
        """Initialize with configuration."""
        self.config = config
        self.commit_config = config.get("commit_quality", {})
        self.contribution_config = config.get("contribution", {})
        self.commit_frequency_config = config.get("commit_frequency", {})
        self.branch_config = config.get("branch_strategy", {})
        self.doc_config = config.get("documentation", {})
        self.timestamps_config = config.get("commit_timestamps", {})
    
    def calculate_commit_frequency_score(self, total_commits: int, num_contributors: int) -> Tuple[float, Dict]:
        """
        Calculate commit frequency metric.
        
        Args:
            total_commits: Total number of commits
            num_contributors: Number of contributors
        
        Returns:
            Tuple of (score 0-100, details dict)
        """
        expected_commits_per_person = self.commit_frequency_config.get("ideal_commits_per_person", 7)
        max_ratio = self.commit_frequency_config.get("max_ratio", 1.5)
        ideal_total = expected_commits_per_person * num_contributors
        
        if total_commits == 0:
            return 0, {"total_commits": 0, "num_contributors": num_contributors}
        
        # Score: how close to ideal distribution
        frequency_ratio = min(total_commits / ideal_total, max_ratio)
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
        solo_score = self.contribution_config.get("solo_score", 30)
        anomaly_penalty = self.contribution_config.get("anomaly_penalty", 0.7)
        
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
            score = solo_score  # Solo work gets low score
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
                score *= anomaly_penalty  # Reduce score if imbalance detected
        
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
        branch_count = len(branches)

        base_score = self.branch_config.get("base_score", 50)
        two_branch_bonus = self.branch_config.get("two_branch_bonus", 30)
        three_branch_bonus = self.branch_config.get("three_branch_bonus", 15)
        four_branch_bonus = self.branch_config.get("four_branch_bonus", 5)
        develop_branch_bonus = self.branch_config.get("develop_branch_bonus", 5)
        feature_branch_bonus = self.branch_config.get("feature_branch_bonus", 5)

        score = base_score

        # Points for multiple branches
        if branch_count >= 2:
            score += two_branch_bonus
        if branch_count >= 3:
            score += three_branch_bonus
        if branch_count >= 4:
            score += four_branch_bonus

        # Check for common good practices
        branch_names_lower = [b.lower() for b in branches]
        if "develop" in branch_names_lower or "dev" in branch_names_lower:
            score += develop_branch_bonus
        if "feature" in str(branch_names_lower):
            score += feature_branch_bonus
        
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
        base_score = self.doc_config.get("base_score", 50)
        readme_bonus = self.doc_config.get("readme_bonus", 30)
        description_bonus = self.doc_config.get("description_bonus", 20)

        score = base_score

        # Check for README
        if repo_data.get("has_readme"):
            score += readme_bonus
        
        # Check for description
        if repo_data.get("description"):
            score += description_bonus
        
        return min(score, 100), {
            "has_readme": repo_data.get("has_readme", False),
            "has_description": bool(repo_data.get("description")),
            "description": repo_data.get("description", "")
        }

    def calculate_commit_timestamps_score(
        self,
        commits_by_date: Dict[str, int],
        start_date: datetime,
        end_date: datetime,
    ) -> Tuple[float, Dict]:
        """
        Evaluate commit distribution over the evaluation period.

        Rewards work spread consistently across the period and penalises
        last-minute commit spikes (all commits crammed into the final days).

        Args:
            commits_by_date: Mapping of ISO date strings (YYYY-MM-DD) to commit counts.
            start_date: Start of the evaluation window.
            end_date: End of the evaluation window.

        Returns:
            Tuple of (score 0-100, details dict)
        """
        min_ratio = self.timestamps_config.get("min_active_days_ratio", 0.1)
        good_ratio = self.timestamps_config.get("good_active_days_ratio", 0.3)
        last_minute_days = self.timestamps_config.get("last_minute_days", 3)
        last_minute_threshold = self.timestamps_config.get("last_minute_threshold", 0.5)

        if not commits_by_date:
            return 0, {
                "active_days": 0,
                "total_days": 0,
                "active_days_ratio": 0.0,
                "last_minute_ratio": 0.0,
                "last_minute_detected": False,
            }

        total_days = max((end_date.date() - start_date.date()).days + 1, 1)
        active_days = len(commits_by_date)
        active_days_ratio = active_days / total_days

        # Score based on how many distinct days had commits
        if active_days_ratio >= good_ratio:
            score = 100.0
        elif active_days_ratio >= min_ratio:
            # Linear interpolation between min_ratio (50 pts) and good_ratio (100 pts)
            progress = (active_days_ratio - min_ratio) / (good_ratio - min_ratio)
            score = 50.0 + progress * 50.0
        else:
            # Below min_ratio: scale from 0 to 50
            score = (active_days_ratio / min_ratio) * 50.0 if min_ratio > 0 else 0.0

        # Last-minute penalty
        cutoff_str = str((end_date - timedelta(days=last_minute_days - 1)).date())
        total_commits = sum(commits_by_date.values())
        last_minute_commits = sum(
            count for date_str, count in commits_by_date.items() if date_str >= cutoff_str
        )
        last_minute_ratio = last_minute_commits / total_commits if total_commits > 0 else 0.0
        last_minute_detected = last_minute_ratio > last_minute_threshold

        if last_minute_detected:
            score *= 0.7  # 30 % penalty for last-minute work

        return min(score, 100.0), {
            "active_days": active_days,
            "total_days": total_days,
            "active_days_ratio": round(active_days_ratio, 3),
            "last_minute_ratio": round(last_minute_ratio, 3),
            "last_minute_detected": last_minute_detected,
        }

