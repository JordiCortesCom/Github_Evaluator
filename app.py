"""
Flask web application for the GitHub Evaluator frontend.

Provides a control panel for selecting repositories, running evaluations,
and visualising the results with statistics and charts.
"""

import json
import logging
import os
from datetime import datetime, date, timezone
from pathlib import Path

import yaml
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

app = Flask(__name__)
# Secret key for session signing – override via SECRET_KEY env var in production.
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config" / "default_config.yaml"


def _load_base_config() -> dict:
    """Load the YAML configuration file."""
    with open(CONFIG_PATH) as fh:
        return yaml.safe_load(fh)


def _resolve_token(config: dict, form_token: str) -> str:
    """Return the GitHub token from the form, env-var, or config (in that order)."""
    if form_token:
        return form_token.strip()
    env_token = os.environ.get("GITHUB_TOKEN", "")
    if env_token:
        return env_token
    raw = config.get("github", {}).get("token", "")
    if "${GITHUB_TOKEN}" in str(raw):
        return env_token
    return raw


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    """Control panel – entry page."""
    config = _load_base_config()
    today = date.today().isoformat()
    default_start = config.get("evaluation", {}).get("start_date", "2024-01-01")
    default_end = config.get("evaluation", {}).get("end_date", today)
    default_org = config.get("github", {}).get("organization", "")
    scoring = config.get("scoring", {})
    return render_template(
        "index.html",
        default_start=default_start,
        default_end=default_end,
        default_org=default_org,
        scoring=scoring,
    )


@app.route("/evaluate", methods=["POST"])
def evaluate():
    """Run the evaluation and redirect to the results page."""
    config = _load_base_config()

    # --- form values ---------------------------------------------------
    token = _resolve_token(config, request.form.get("token", ""))
    org = request.form.get("org", "").strip()
    pattern = request.form.get("pattern", "").strip() or None
    assignment_id_raw = request.form.get("assignment_id", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()

    # --- scoring weight overrides --------------------------------------
    scoring_keys = [
        "commit_frequency",
        "commit_quality",
        "individual_contribution",
        "branch_strategy",
        "documentation",
    ]
    scoring = {}
    for key in scoring_keys:
        raw = request.form.get(f"scoring_{key}", "")
        try:
            scoring[key] = int(raw)
        except (ValueError, TypeError):
            scoring[key] = config.get("scoring", {}).get(key, 20)

    # --- validation (before any heavy imports) -------------------------
    if not token:
        flash("GitHub token is required.", "danger")
        return redirect(url_for("index"))

    if not org and not assignment_id_raw:
        flash("Provide either a GitHub organization name or an assignment ID.", "danger")
        return redirect(url_for("index"))

    total_weight = sum(scoring.values())
    if total_weight != 100:
        flash(
            f"Scoring weights must sum to 100 (currently {total_weight}). "
            "Please adjust the weights and try again.",
            "danger",
        )
        return redirect(url_for("index"))

    # Avoid importing heavy dependencies at module level so the app can start
    # even when PyGithub / network access is unavailable.
    from src.evaluator import StudentEvaluator  # noqa: PLC0415

    # --- build config --------------------------------------------------
    config["github"]["token"] = token
    config["scoring"] = scoring
    if start_date:
        config.setdefault("evaluation", {})["start_date"] = start_date
    if end_date:
        config.setdefault("evaluation", {})["end_date"] = end_date

    # --- run evaluation ------------------------------------------------
    try:
        evaluator = StudentEvaluator(config)

        if assignment_id_raw:
            results = evaluator.evaluate_classroom_assignment(int(assignment_id_raw))
        else:
            results = evaluator.evaluate_organization(org, pattern)

    except Exception as exc:
        logger.exception("Evaluation failed")
        flash(f"Evaluation failed: {exc}", "danger")
        return redirect(url_for("index"))

    if not results:
        flash("No repositories were found or none matched the given criteria.", "warning")
        return redirect(url_for("index"))

    # Store results in the session (JSON-serialisable – scores are floats/strings)
    session["results"] = results
    session["evaluated_at"] = datetime.now(tz=timezone.utc).isoformat()
    session["org"] = org or f"assignment {assignment_id_raw}"
    return redirect(url_for("results"))


@app.route("/results")
def results():
    """Display the evaluation results with statistics and charts."""
    raw_results = session.get("results")
    if not raw_results:
        flash("No evaluation results found. Please run an evaluation first.", "info")
        return redirect(url_for("index"))

    evaluated_at = session.get("evaluated_at", "")
    org_label = session.get("org", "")

    # --- aggregate statistics -----------------------------------------
    scores = [r.get("final_score", 0) for r in raw_results]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    max_score = round(max(scores), 2) if scores else 0
    min_score = round(min(scores), 2) if scores else 0

    grade_distribution: dict[str, int] = {}
    for r in raw_results:
        grade = r.get("letter_grade", "N/A")
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

    # --- chart data ---------------------------------------------------
    # Bar chart: score per student
    student_labels = [r.get("student", r.get("repository", "?")) for r in raw_results]
    student_scores = [r.get("final_score", 0) for r in raw_results]

    # Radar / bar chart: average per metric
    metric_keys = [
        "commit_frequency",
        "commit_quality",
        "individual_contribution",
        "branch_strategy",
        "documentation",
    ]
    metric_labels = [k.replace("_", " ").title() for k in metric_keys]
    metric_averages = []
    for key in metric_keys:
        vals = [
            r.get("metrics", {}).get(key, {}).get("score", 0)
            for r in raw_results
        ]
        metric_averages.append(round(sum(vals) / len(vals), 2) if vals else 0)

    chart_data = {
        "students": student_labels,
        "scores": student_scores,
        "metric_labels": metric_labels,
        "metric_averages": metric_averages,
        "grade_labels": list(grade_distribution.keys()),
        "grade_counts": list(grade_distribution.values()),
    }

    return render_template(
        "results.html",
        results=raw_results,
        avg_score=avg_score,
        max_score=max_score,
        min_score=min_score,
        grade_distribution=grade_distribution,
        chart_data=json.dumps(chart_data),
        evaluated_at=evaluated_at,
        org_label=org_label,
        total=len(raw_results),
    )


@app.route("/clear")
def clear():
    """Clear the session and return to the control panel."""
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
