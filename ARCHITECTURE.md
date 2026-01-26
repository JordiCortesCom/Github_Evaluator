# GitHub Evaluator - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLI Interface (main.py)                     │
│  Argument parsing, config loading, orchestration                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────────┐  ┌─────────────┐  ┌──────────────┐
    │   Config    │  │   GitHub    │  │  Evaluator   │
    │  Manager    │  │   Client    │  │  Orchestrator│
    └─────────────┘  └──────┬──────┘  └──────┬───────┘
                            │                 │
                ┌───────────┴─────────────────┘
                │
    ┌───────────▼──────────────────┐
    │    Repository Data Flow       │
    │  (Commits, Branches, PRs)     │
    └───────────┬──────────────────┘
                │
    ┌───────────▼──────────────────────────────────┐
    │         Metrics Extraction Engine             │
    │  ┌──────────────────────────────────────────┐ │
    │  │ 1. Commit Frequency Calculator           │ │
    │  │ 2. Commit Quality Analyzer               │ │
    │  │ 3. Contribution Balance Calculator       │ │
    │  │ 4. Branch Strategy Evaluator             │ │
    │  │ 5. Documentation Scorer                  │ │
    │  └──────────────────────────────────────────┘ │
    └───────────┬──────────────────────────────────┘
                │
    ┌───────────▼──────────────────┐
    │    Grading Engine             │
    │  - Weight Aggregation         │
    │  - Final Score Calculation    │
    │  - Grade Assignment           │
    │  - Feedback Generation        │
    └───────────┬──────────────────┘
                │
    ┌───────────▼──────────────────────────────────┐
    │       Report Generation                       │
    │  ┌──────────────┐  ┌──────────────┐         │
    │  │   CSV Export │  │  JSON Export │         │
    │  └──────────────┘  └──────────────┘         │
    │  ┌──────────────┐                           │
    │  │  Text Export │                           │
    │  └──────────────┘                           │
    └───────────┬──────────────────────────────────┘
                │
    ┌───────────▼──────────────────┐
    │    Output Files               │
    │  - evaluation_results.csv     │
    │  - evaluation_results.json    │
    │  - evaluation_report.txt      │
    └───────────────────────────────┘
```

## Module Dependency Graph

```
main.py
├── config/default_config.yaml
├── src/evaluator.py
│   ├── src/github_client.py
│   │   └── PyGithub (external)
│   ├── src/metrics.py
│   └── src/grader.py
└── src/reporter.py
    ├── csv (stdlib)
    ├── json (stdlib)
    └── pathlib (stdlib)
```

## Data Flow

### 1. Input Phase
```
User Command
    ↓
Parse Arguments
    ↓
Load YAML Configuration
    ↓
Override with CLI Parameters
    ↓
Validate Configuration
```

### 2. Extraction Phase
```
GitHub Organization
    ↓
List Repositories (by pattern)
    ↓
For each repository:
    ├── Fetch Commits (with date range)
    ├── Fetch Branches
    ├── Fetch Pull Requests
    └── Extract Contributor List
```

### 3. Analysis Phase
```
Repository Data
    ↓
┌───────────────────────────────────────┐
│  Five Parallel Metric Calculations    │
├───────────────────────────────────────┤
│ 1. Commit Frequency                   │
│    - Total commits                    │
│    - Commits per contributor          │
│    - Comparison to ideal (5-10)        │
│                                       │
│ 2. Commit Message Quality             │
│    - Message length analysis          │
│    - Minimum threshold check (10)     │
│    - Good threshold check (50)        │
│                                       │
│ 3. Individual Contribution            │
│    - Commits by author                │
│    - Calculate percentages            │
│    - Check for anomalies (>80%)       │
│    - Balance scoring (Gini-like)      │
│                                       │
│ 4. Branch Strategy                    │
│    - Count branches                   │
│    - Check branch naming patterns     │
│    - Reward multiple/feature branches │
│                                       │
│ 5. Documentation                      │
│    - Check README.md existence        │
│    - Check repository description     │
│    - Presence scoring                 │
└───────────────────────────────────────┘
    ↓
Store metrics for grading
```

### 4. Grading Phase
```
Five Metric Scores (0-100 each)
    ↓
Apply Weights:
    - Commit Frequency × 25%
    - Commit Quality × 25%
    - Individual Contribution × 30%
    - Branch Strategy × 10%
    - Documentation × 10%
    ↓
Calculate Weighted Sum
    ↓
Assign Letter Grade:
    - 90-100: A
    - 80-89:  B
    - 70-79:  C
    - 60-69:  D
    - <60:    F
    ↓
Generate Feedback
```

### 5. Output Phase
```
Final Scores & Feedback
    ↓
┌──────────────────────────────┐
│  Generate Multiple Formats   │
├──────────────────────────────┤
│ CSV Export                   │
│ ├── student                  │
│ ├── repository               │
│ ├── final_score              │
│ ├── letter_grade             │
│ └── metric scores            │
│                              │
│ JSON Export                  │
│ ├── Full metrics detail      │
│ ├── All calculations         │
│ └── Feedback strings         │
│                              │
│ Text Report                  │
│ ├── Summary statistics       │
│ ├── Grade distribution       │
│ ├── Per-student details      │
│ └── Actionable feedback      │
└──────────────────────────────┘
    ↓
Write to reports/ directory
```

## Class & Function Structure

### github_client.py
```
GitHubClient
├── __init__(token)
├── get_organization_repos(org, pattern)
├── get_repo_commits(repo, since, until)
├── analyze_commits(commits)
├── get_repo_branches(repo)
└── get_pull_requests(repo)
```

### metrics.py
```
MetricsExtractor
├── __init__(config)
├── calculate_commit_frequency_score(total, contributors)
├── calculate_commit_quality_score(message_lengths)
├── calculate_individual_contribution_score(commits_by_author)
├── calculate_branch_strategy_score(branches, total_commits)
└── calculate_documentation_score(repo_data)
```

### grader.py
```
GradingEngine
├── __init__(config)
├── calculate_final_score(metrics)
├── get_letter_grade(score)
├── generate_student_report(name, repo, metrics, score)
└── _generate_feedback(metrics, score)
```

### evaluator.py
```
StudentEvaluator
├── __init__(config)
├── evaluate_organization(org, pattern)
├── evaluate_repository(repo)
├── _check_readme(repo)
└── _extract_student_name(repo_name)
```

### reporter.py
```
ReportGenerator
├── __init__(output_dir)
├── export_csv(results, filename)
├── export_json(results, filename)
├── export_text(results, filename)
└── export_all_formats(results)
```

## Configuration Structure

```yaml
github:
  token: GitHub API token
  organization: Org name
  classroom_prefix: Repo filter pattern

evaluation:
  start_date: "YYYY-MM-DD"
  end_date: "YYYY-MM-DD"

scoring:
  commit_frequency: 0-100 (weight %)
  commit_quality: 0-100
  individual_contribution: 0-100
  branch_strategy: 0-100
  documentation: 0-100
  (must sum to 100)

commit_quality:
  min_length: characters
  good_length: characters
  quality_keywords: [list]

contribution:
  flag_anomaly: 0.0-1.0
  min_commits_for_score: int

grading:
  excellent: score
  good: score
  satisfactory: score
  passing: score

output:
  format: [csv, json, txt]
  directory: path
  include_details: boolean
```

## Error Handling

### Authentication Errors
```
GitHub Token Invalid
    ↓
Caught in GitHubClient.__init__
    ↓
Raises ValueError with helpful message
    ↓
main.py catches and exits with status 1
```

### Repository Access Errors
```
No access to repository
    ↓
Caught in get_repo_commits()
    ↓
Logs error and returns empty list
    ↓
Metrics calculated with zeros
    ↓
Student gets low score (fair penalty)
```

### Configuration Errors
```
Invalid YAML
    ↓
Caught in load_config()
    ↓
Raises ValueError
    ↓
main.py catches and exits with status 1
```

## Performance Considerations

### Optimization Strategies
1. **Parallel Metric Calculation**: Each metric calculated independently
2. **Lazy Loading**: Only fetch data when needed
3. **Batching**: Process repos sequentially (API limits respected)
4. **Caching**: GitHub library caches API responses

### Time Complexity
- Per Repository: O(commits + branches + PRs)
- Per Student: O(1) metric calculation
- Total: O(n × m) where n=students, m=avg commits

### API Rate Limits
- GitHub API: 5000 requests/hour (authenticated)
- Per student: ~5-10 API calls
- Safe for: ~500-1000 students per hour

## Extension Points

### Adding New Metrics
1. Add calculation method to `MetricsExtractor`
2. Return (score, details_dict)
3. Add to config weights
4. Add to grading engine calculation
5. Report automatically includes it

### Custom Scoring Logic
- Modify `calculate_final_score()` in `GradingEngine`
- Supports weighted sum, weighted average, or custom formula

### Additional Output Formats
- Add `export_<format>()` method to `ReportGenerator`
- Called automatically by `export_all_formats()`

### Alternative GitHub Sources
- Replace `PyGithub` with `GitPython` for local repos
- Add support for GitLab, Gitea, or other platforms
- Modify `github_client.py` interface only

## Testing Considerations

### Unit Tests Needed
- Metric calculation correctness
- Scoring edge cases (0 commits, 100% one person)
- Config loading and validation
- Report format generation

### Integration Tests Needed
- End-to-end evaluation flow
- Multiple student repositories
- Different configurations
- Error scenarios (missing token, private repos)

### Test Data
- Sample repos with known metrics
- Edge cases (solo work, no commits, very old commits)
- Multiple evaluation periods
- Different team sizes

---

**Last Updated:** 2024-01-26
**Version:** 1.0.0
**Status:** Production Ready
