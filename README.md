# GitHub Evaluator

A Python-based tool for evaluating student GitHub repositories based on Git best practices and individual contributions.

## Features

✅ **Automated Analysis**
- Commit frequency and quality evaluation
- Individual contribution tracking
- Branch strategy analysis
- Code documentation assessment

✅ **Configurable Scoring**
- Weighted metrics (customizable percentages)
- Multiple evaluation thresholds
- Per-student feedback generation

✅ **Multi-Format Reports**
- CSV for grade book integration
- JSON for programmatic access
- Human-readable text reports

✅ **GitHub Classroom Integration**
- Batch process all student repositories
- Filter by organization and naming pattern
- Support for both public and private repos

## Installation

```bash
# Clone repository
git clone <repo-url>
cd Github_Evaluator

# Install dependencies
pip install -r requirements.txt

# Set GitHub token
export GITHUB_TOKEN=your_github_personal_access_token
```

## Configuration

Edit `config/default_config.yaml` to customize:

- **Scoring weights**: Adjust importance of each metric
- **Evaluation period**: Set start and end dates
- **Grading thresholds**: Define letter grade cutoffs
- **Commit quality**: Set minimum message length
- **Contribution detection**: Configure anomaly thresholds

### Example Configuration

```yaml
github:
  token: "${GITHUB_TOKEN}"
  organization: "my-classroom"
  classroom_prefix: "assignment-"

scoring:
  commit_frequency: 25      # How often they commit
  commit_quality: 25        # Message quality
  individual_contribution: 30  # Balanced teamwork
  branch_strategy: 10       # Proper branching
  documentation: 10         # README, comments

grading:
  excellent: 90
  good: 80
  satisfactory: 70
  passing: 60
```

## Usage

### Basic Evaluation (Organization-wide)

```bash
python main.py --org classroom-org --pattern assignment-
```

### GitHub Classroom Assignment Evaluation

Evaluate all student repos for a specific assignment using the Classroom API:

```bash
python main.py --assignment-id 12345
```

### List Assignments in a Classroom

```bash
python main.py --classroom-id 9876
```

### Advanced Options

```bash
python main.py \
  --org my-classroom \
  --pattern "assignment-" \
  --token $GITHUB_TOKEN \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output-dir ./reports \
  --formats csv json txt
```

### Command-Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--config` | Config YAML file path | `config/default_config.yaml` |
| `--org` | GitHub organization name | Required unless `--assignment-id` used |
| `--assignment-id` | GitHub Classroom assignment ID | None |
| `--classroom-id` | GitHub Classroom ID (lists assignments and exits) | None |
| `--pattern` | Repository name filter | None (all repos) |
| `--token` | GitHub personal access token | Uses GITHUB_TOKEN env var |
| `--output-dir` | Report output directory | `./reports` |
| `--start-date` | Evaluation period start (YYYY-MM-DD) | From config |
| `--end-date` | Evaluation period end (YYYY-MM-DD) | From config |
| `--formats` | Output formats (csv json txt) | All formats |

> **Note:** The `--assignment-id` and `--classroom-id` flags require a GitHub token
> with the **`manage_classrooms`** scope (available in classic personal access tokens).

## Evaluation Metrics

### 1. Commit Frequency (25%)
- Evaluates total commits and distribution
- Ideal: 5-10 commits per contributor
- Flag: Too few commits = less collaboration

### 2. Commit Message Quality (25%)
- Analyzes message length and clarity
- Minimum: 10 characters
- Good: 50+ characters
- Penalizes vague messages like "fix" or "update"

### 3. Individual Contribution (30%)
- Detects contribution balance within teams
- Flags anomalies (one person >80% commits)
- Encourages equal participation
- Solo work gets lower score

### 4. Branch Strategy (10%)
- Rewards multiple branches (feature branches, dev branch)
- Checks for common patterns (develop, feature/*)
- Encourages proper git workflow

### 5. Documentation (10%)
- Checks for README file presence
- Validates repository description
- Rewards project documentation

## Output Reports

### CSV Report (`evaluation_results.csv`)
Compatible with most grade management systems. Contains:
- Student name, repository, final score, grade
- Individual metric scores and weights

### JSON Report (`evaluation_results.json`)
Full detailed output with all metrics and details. Useful for:
- Data processing and visualization
- Integration with other tools
- Detailed analysis

### Text Report (`evaluation_report.txt`)
Human-readable summary including:
- Class statistics (average, min, max scores)
- Grade distribution (A, B, C, D, F counts)
- Per-student feedback and metric breakdown

## Examples

### Run Full Evaluation
```bash
python main.py --org "my-classroom" --pattern "assignment-" --formats csv txt
```

Reports will be generated in `./reports/`

### Check Single Assignment
```bash
python main.py \
  --org "my-classroom" \
  --pattern "lab-01-" \
  --start-date 2024-09-01 \
  --end-date 2024-09-15
```

### Export to Specific Directory
```bash
python main.py \
  --org "my-classroom" \
  --output-dir ~/grades_semester_2024 \
  --formats csv
```

## GitHub Token Setup

1. Go to https://github.com/settings/tokens
2. Create a Personal Access Token
3. Grant `repo:public_repo` and `read:org` permissions
4. For Classroom API features (`--assignment-id`, `--classroom-id`), also grant `manage_classrooms`
5. Set environment variable: `export GITHUB_TOKEN=ghp_xxxxx`

## Project Structure

```
Github_Evaluator/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── config/
│   └── default_config.yaml # Configuration file
├── src/
│   ├── __init__.py
│   ├── classroom_scraper.py # GitHub Classroom API client
│   ├── github_client.py   # GitHub API wrapper
│   ├── metrics.py         # Metric calculation
│   ├── grader.py          # Scoring engine
│   ├── evaluator.py       # Main orchestrator
│   └── reporter.py        # Report generation
├── tests/
│   └── test_classroom_scraper.py  # Unit tests
├── reports/               # Generated reports (created on run)
└── README.md
```

## Future Enhancements

- [ ] Web dashboard for visualizing results
- [ ] Plagiarism detection between students
- [ ] Integration with Canvas/Blackboard
- [ ] Continuous evaluation mode
- [ ] Code quality metrics (linting, testing)
- [ ] Pull request analysis
- [ ] Code review tracking

## License

MIT License

## Support

For issues or questions, please open a GitHub issue.