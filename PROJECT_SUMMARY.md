# GitHub Evaluator - Project Summary

## Overview
A complete Python system for evaluating 30+ students' GitHub repositories based on:
- ✅ Commit frequency and patterns
- ✅ Commit message quality
- ✅ Individual contribution balance
- ✅ Branch strategy usage
- ✅ Code documentation

## Key Features

### 🎯 Automated Evaluation
- Fetches all student repos from GitHub Classroom
- Analyzes commit history, branches, and contributors
- Calculates 5 independent metrics
- Generates weighted final scores

### ⚙️ Fully Parametrized
- YAML configuration system
- Adjustable scoring weights
- Customizable thresholds and grading scales
- Command-line parameter overrides

### 📊 Multi-Format Reports
- **CSV**: For importing into gradebooks
- **JSON**: Full detailed data for analysis
- **Text**: Human-readable summaries and feedback

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `github_client.py` | GitHub API wrapper, data fetching |
| `metrics.py` | Extract and calculate all 5 metrics |
| `grader.py` | Weighted scoring and final grades |
| `evaluator.py` | Main orchestration logic |
| `reporter.py` | Generate CSV, JSON, TXT reports |
| `main.py` | CLI interface with argument parsing |

### Scoring System (0-100)

```
Final Score = (Freq×25% + Quality×25% + Contribution×30% + Branch×10% + Doc×10%)

Letter Grades:
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: <60
```

### Metric Details

#### 1. Commit Frequency (25%)
- **Evaluates:** How often students commit
- **Ideal:** 5-10 commits per contributor
- **Flags:** Solo work or very few commits

#### 2. Commit Message Quality (25%)
- **Evaluates:** Clarity and detail of commit messages
- **Scoring:** 
  - Minimum: 10 characters
  - Good: 50+ characters
- **Penalizes:** Vague messages like "fix" or "update"

#### 3. Individual Contribution (30%)
- **Evaluates:** Fair distribution of work
- **Scoring:** Gini-coefficient-like approach
- **Flags:** >80% commits by one person (configurable)
- **Penalizes:** Solo work (30 points base)

#### 4. Branch Strategy (10%)
- **Evaluates:** Proper use of branching
- **Rewards:**
  - Multiple branches (2+ branches = 30 pts)
  - Develop/Dev branch = 5 pts
  - Feature branches = 5 pts

#### 5. Documentation (10%)
- **Evaluates:** README and project description
- **Scoring:**
  - Has README: 30 pts
  - Has description: 20 pts
- **Base score:** 50 pts

## Configuration Example

```yaml
github:
  token: "${GITHUB_TOKEN}"
  organization: "my-classroom"
  classroom_prefix: "assignment-"

evaluation:
  start_date: "2024-01-01"
  end_date: "2024-12-31"

scoring:
  commit_frequency: 25
  commit_quality: 25
  individual_contribution: 30
  branch_strategy: 10
  documentation: 10

commit_quality:
  min_length: 10
  good_length: 50

contribution:
  flag_anomaly: 0.8

grading:
  excellent: 90
  good: 80
  satisfactory: 70
  passing: 60
```

## Usage Examples

### Basic Run
```bash
python main.py --org classroom-org --pattern assignment-
```

### Custom Period
```bash
python main.py \
  --org classroom-org \
  --pattern "assignment-" \
  --start-date 2024-09-01 \
  --end-date 2024-09-30
```

### Custom Config
```bash
python main.py \
  --config config/custom.yaml \
  --org classroom-org \
  --output-dir ~/grades
```

## Output Files

### evaluation_results.csv
```
student,repository,final_score,letter_grade,...
alice,assignment-alice,85.5,B,...
bob,assignment-bob,72.0,C,...
```

### evaluation_results.json
```json
[{
  "student": "alice",
  "final_score": 85.5,
  "letter_grade": "B",
  "metrics": {
    "commit_frequency": {
      "score": 88,
      "details": {...}
    },
    ...
  }
}]
```

### evaluation_report.txt
```
SUMMARY STATISTICS
Total Students: 30
Average Score: 78.5
Grade Distribution:
  A: 8 students (26.7%)
  B: 9 students (30.0%)
  C: 8 students (26.7%)
  D: 3 students (10.0%)
  F: 2 students (6.7%)

INDIVIDUAL STUDENT RESULTS
Student: alice
Repository: assignment-alice
Final Score: 85.50/100
Grade: B
Feedback: ✓ Good commit frequency | ✓ Excellent commit message quality | ✓ Balanced team contributions
```

## Development Notes

### Technologies Used
- **PyGithub**: GitHub API client
- **pandas**: Data processing
- **PyYAML**: Configuration management
- **Click**: CLI framework

### Design Decisions

1. **Modular Architecture**: Each metric independently calculated
2. **Configuration-Driven**: All thresholds easily adjustable
3. **Multiple Outputs**: CSV for integration, JSON for analysis, TXT for review
4. **Anomaly Detection**: Flags imbalanced contributions automatically
5. **Feedback Generation**: Automatic, actionable feedback per student

### Extensibility

Easy to add new metrics:
1. Implement calculation method in `metrics.py`
2. Add to config weights in `default_config.yaml`
3. Add to final score calculation in `grader.py`
4. Reports automatically include new metric

## Future Enhancements

- [ ] Code complexity analysis
- [ ] Test coverage detection
- [ ] Code review tracking
- [ ] Plagiarism detection
- [ ] Web dashboard
- [ ] LMS integration (Canvas, Blackboard)
- [ ] Continuous evaluation mode
- [ ] Performance trending over assignments

## Files in Project

```
.
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── setup.sh                   # Setup script
├── QUICKSTART.md              # 5-minute quickstart
├── PROJECT_SUMMARY.md         # This file
├── examples.py                # Usage examples
├── README.md                  # Full documentation
├── config/
│   └── default_config.yaml    # Default configuration
├── src/
│   ├── __init__.py
│   ├── github_client.py       # GitHub API integration
│   ├── metrics.py             # Metric calculations
│   ├── grader.py              # Scoring system
│   ├── evaluator.py           # Main orchestrator
│   └── reporter.py            # Report generation
└── reports/                   # Output directory (created on run)
    ├── evaluation_results.csv
    ├── evaluation_results.json
    └── evaluation_report.txt
```

---

**Status:** ✅ Complete and Ready to Use
**Languages:** Python 3.8+
**License:** MIT
