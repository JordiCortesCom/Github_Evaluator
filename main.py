"""
Main entry point for GitHub Evaluator.
Command-line interface for running evaluations.
"""

import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

import yaml

from src.evaluator import StudentEvaluator
from src.reporter import ReportGenerator
from src.classroom_scraper import ClassroomScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str, overrides: dict = None) -> dict:
    """
    Load configuration from YAML file with optional overrides.
    
    Args:
        config_path: Path to YAML config file
        overrides: Dictionary of config overrides
    
    Returns:
        Configuration dictionary
    """
    # Validate and resolve config path
    config_file = Path(config_path).resolve()
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply overrides
    if overrides:
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        config = deep_update(config, overrides)
    
    # Expand environment variables in token
    if "${GITHUB_TOKEN}" in str(config.get("github", {}).get("token", "")):
        import os
        config["github"]["token"] = os.getenv("GITHUB_TOKEN", "")
    
    return config


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate GitHub Classroom student repositories"
    )
    
    parser.add_argument(
        "--config",
        default="config/default_config.yaml",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--org",
        default=None,
        help="GitHub organization or owner name (required unless --assignment-id is used)"
    )

    parser.add_argument(
        "--assignment-id",
        type=int,
        default=None,
        help="GitHub Classroom assignment ID (use instead of --org/--pattern)"
    )

    parser.add_argument(
        "--classroom-id",
        type=int,
        default=None,
        help="GitHub Classroom ID (list assignments for this classroom and exit)"
    )
    
    parser.add_argument(
        "--pattern",
        default=None,
        help="Repository name pattern filter (e.g., 'assignment-')"
    )
    
    parser.add_argument(
        "--token",
        default=None,
        help="GitHub personal access token (overrides config)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./reports",
        help="Directory for output reports"
    )
    
    parser.add_argument(
        "--start-date",
        default=None,
        help="Evaluation start date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--end-date",
        default=None,
        help="Evaluation end date (YYYY-MM-DD)"
    )
    
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["csv", "json", "txt"],
        help="Output formats (csv, json, txt)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        logger.info(f"Loading config from {args.config}")
        config = load_config(args.config)
        
        # Apply command-line overrides
        overrides = {}
        if args.token:
            overrides["github"] = {"token": args.token}
        if args.start_date:
            if "evaluation" not in overrides:
                overrides["evaluation"] = {}
            overrides["evaluation"]["start_date"] = args.start_date
        if args.end_date:
            if "evaluation" not in overrides:
                overrides["evaluation"] = {}
            overrides["evaluation"]["end_date"] = args.end_date
        
        if overrides:
            # Apply overrides without reloading config file
            def deep_update(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = deep_update(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d
            config = deep_update(config, overrides)
        
        # Validate configuration
        if not config.get("github", {}).get("token"):
            logger.error("GitHub token not provided. Set GITHUB_TOKEN env var or use --token")
            sys.exit(1)
        
        # Validate scoring weights sum to 100
        weights = config.get("scoring", {})
        total_weight = sum(weights.values())
        if total_weight != 100:
            logger.error(f"Scoring weights must sum to 100, but got {total_weight}. Current: {weights}")
            sys.exit(1)

        token = config["github"]["token"]

        # ------------------------------------------------------------------
        # --classroom-id: list assignments and exit (no evaluation)
        # ------------------------------------------------------------------
        if args.classroom_id:
            scraper = ClassroomScraper(token)
            classroom = scraper.get_classroom(args.classroom_id)
            if not classroom:
                logger.error(f"Classroom {args.classroom_id} not found or not accessible.")
                return 1
            print(f"\nClassroom: {classroom.get('name')} (id={classroom.get('id')})")
            assignments = scraper.list_assignments(args.classroom_id)
            if not assignments:
                print("  No assignments found.")
            else:
                print(f"  Assignments ({len(assignments)}):")
                for a in assignments:
                    title = a.get('title', '(no title)')
                    a_type = a.get('type', '?')
                    accepted = a.get('accepted', '?')
                    print(f"    [{a['id']}] {title} — type={a_type} accepted={accepted}")
            return 0

        # ------------------------------------------------------------------
        # --assignment-id: evaluate a specific Classroom assignment
        # ------------------------------------------------------------------
        if args.assignment_id:
            logger.info(f"Starting Classroom evaluation for assignment ID: {args.assignment_id}")
            evaluator = StudentEvaluator(config)
            results = evaluator.evaluate_classroom_assignment(args.assignment_id)

        # ------------------------------------------------------------------
        # --org: fall back to organization-wide evaluation
        # ------------------------------------------------------------------
        elif args.org:
            logger.info(f"Starting evaluation of organization: {args.org}")
            logger.info(f"Repository pattern: {args.pattern or 'any'}")
            evaluator = StudentEvaluator(config)
            results = evaluator.evaluate_organization(args.org, args.pattern)

        else:
            logger.error(
                "You must specify either --org (for organization-wide evaluation) "
                "or --assignment-id (for a specific Classroom assignment), "
                "or --classroom-id (to list assignments)."
            )
            sys.exit(1)
        
        logger.info(f"Evaluation complete. Processed {len(results)} repositories.")
        
        # Generate reports
        logger.info(f"Generating reports in {args.output_dir}")
        reporter = ReportGenerator(args.output_dir)
        
        report_files = []
        if "csv" in args.formats:
            report_files.append(reporter.export_csv(results))
        if "json" in args.formats:
            report_files.append(reporter.export_json(results))
        if "txt" in args.formats:
            report_files.append(reporter.export_text(results))
        
        logger.info("Reports generated successfully:")
        for f in report_files:
            if f:
                logger.info(f"  - {f}")
        
        # Print summary
        if results:
            scores = [r.get("final_score", 0) for r in results]
            print("\n" + "=" * 60)
            print("EVALUATION SUMMARY")
            print("=" * 60)
            print(f"Students Evaluated: {len(results)}")
            print(f"Average Score: {sum(scores)/len(scores):.2f}/100")
            print(f"Highest Score: {max(scores):.2f}/100")
            print(f"Lowest Score: {min(scores):.2f}/100")
            print("=" * 60 + "\n")
        
        return 0
    
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
