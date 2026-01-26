"""
Initialization file for src package.
"""

from src.github_client import GitHubClient
from src.metrics import MetricsExtractor
from src.grader import GradingEngine
from src.evaluator import StudentEvaluator
from src.reporter import ReportGenerator

__all__ = [
    "GitHubClient",
    "MetricsExtractor",
    "GradingEngine",
    "StudentEvaluator",
    "ReportGenerator"
]
