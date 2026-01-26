"""
Grading engine for calculating final scores.
"""

from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class GradingEngine:
    """Calculate final grades based on weighted metrics."""
    
    def __init__(self, config: Dict):
        """Initialize grading engine with configuration."""
        self.config = config
        self.scoring_weights = config.get("scoring", {})
        self.grading_thresholds = config.get("grading", {})
    
    def calculate_final_score(self, metrics: Dict) -> Tuple[float, Dict]:
        """
        Calculate weighted final score from all metrics.
        
        Args:
            metrics: Dictionary with all calculated metrics
                {
                    "commit_frequency": (score, details),
                    "commit_quality": (score, details),
                    "individual_contribution": (score, details),
                    "branch_strategy": (score, details),
                    "documentation": (score, details)
                }
        
        Returns:
            Tuple of (final_score, component_breakdown)
        """
        weighted_sum = 0
        total_weight = 0
        breakdown = {}
        
        for metric_name, weight in self.scoring_weights.items():
            if metric_name in metrics:
                score, details = metrics[metric_name]
                weighted_contribution = (score * weight) / 100
                weighted_sum += weighted_contribution
                total_weight += weight
                breakdown[metric_name] = {
                    "score": round(score, 2),
                    "weight": weight,
                    "weighted_contribution": round(weighted_contribution, 2),
                    "details": details
                }
        
        if total_weight == 0:
            final_score = 0
        else:
            final_score = weighted_sum  # Already normalized by weights
        
        return final_score, breakdown
    
    def get_letter_grade(self, score: float) -> str:
        """
        Convert numeric score to letter grade.
        
        Args:
            score: Numeric score (0-100)
        
        Returns:
            Letter grade (A, B, C, D, F)
        """
        thresholds = self.grading_thresholds
        
        if score >= thresholds.get("excellent", 90):
            return "A"
        elif score >= thresholds.get("good", 80):
            return "B"
        elif score >= thresholds.get("satisfactory", 70):
            return "C"
        elif score >= thresholds.get("passing", 60):
            return "D"
        else:
            return "F"
    
    def generate_student_report(self, student_name: str, repo_name: str, metrics: Dict, final_score: float) -> Dict:
        """
        Generate comprehensive report for a single student.
        
        Args:
            student_name: Student identifier
            repo_name: Repository name
            metrics: All calculated metrics
            final_score: Final numeric score
        
        Returns:
            Student report dictionary
        """
        letter_grade = self.get_letter_grade(final_score)
        
        report = {
            "student": student_name,
            "repository": repo_name,
            "final_score": round(final_score, 2),
            "letter_grade": letter_grade,
            "metrics": metrics,
            "feedback": self._generate_feedback(metrics, final_score)
        }
        
        return report
    
    def _generate_feedback(self, metrics: Dict, score: float) -> str:
        """Generate textual feedback based on score and metrics."""
        feedback = []
        
        # Check commit frequency
        freq_score, freq_details = metrics.get("commit_frequency", (0, {}))
        if freq_score < 60:
            feedback.append("❌ Need more commits - shows less consistent development")
        elif freq_score >= 80:
            feedback.append("✓ Good commit frequency")
        
        # Check commit quality
        qual_score, qual_details = metrics.get("commit_quality", (0, {}))
        if qual_score < 60:
            feedback.append("❌ Commit messages are too short or unclear")
        elif qual_score >= 80:
            feedback.append("✓ Excellent commit message quality")
        
        # Check individual contribution
        contrib_score, contrib_details = metrics.get("individual_contribution", (0, {}))
        if contrib_details.get("anomaly_detected"):
            feedback.append(f"⚠️  Unbalanced contributions: {contrib_details['distribution']}")
        elif contrib_score >= 80:
            feedback.append("✓ Balanced team contributions")
        
        # Check branch strategy
        branch_score, branch_details = metrics.get("branch_strategy", (0, {}))
        if branch_details.get("branch_count", 0) < 2:
            feedback.append("⚠️  Use multiple branches for better workflow")
        
        if score >= 90:
            feedback.append("🎉 Excellent overall performance!")
        elif score < 60:
            feedback.append("⚠️  Significant improvement needed")
        
        return " | ".join(feedback) if feedback else "No specific feedback"
