# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Create GitHub Token
1. Visit: https://github.com/settings/tokens/new
2. Select scopes: `repo:public_repo` and `read:org`
3. Generate and copy the token

### Step 3: Set Environment Variable
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### Step 4: Update Configuration
Edit `config/default_config.yaml`:
```yaml
github:
  token: "${GITHUB_TOKEN}"
  organization: "your-classroom-org"  # Change this
  classroom_prefix: "assignment-"      # Change if needed
```

### Step 5: Run Evaluation
```bash
python main.py --org your-classroom-org --pattern "assignment-"
```

### Step 6: Check Results
```bash
ls -la reports/
cat reports/evaluation_report.txt
```

---

## Common Use Cases

### Evaluate a Single Assignment
```bash
python main.py --org classroom-org --pattern "assignment-1-"
```

### Evaluate with Custom Date Range
```bash
python main.py \
  --org classroom-org \
  --pattern "assignment-" \
  --start-date 2024-09-01 \
  --end-date 2024-09-30
```

### Export Only CSV (for Gradebook)
```bash
python main.py \
  --org classroom-org \
  --formats csv \
  --output-dir ./gradebook
```

### Use Custom Configuration
```bash
python main.py \
  --config config/my_config.yaml \
  --org classroom-org
```

---

## Understanding the Scores

Each student gets evaluated on 5 metrics (0-100 each):

| Metric | Weight | What It Measures |
|--------|--------|------------------|
| **Commit Frequency** | 25% | How often they commit (collaboration indicator) |
| **Commit Quality** | 25% | How clear their commit messages are |
| **Individual Contribution** | 30% | Fair distribution of work in team projects |
| **Branch Strategy** | 10% | Use of branches for organized workflow |
| **Documentation** | 10% | README and project description completeness |

**Final Score** = Weighted average of all 5 metrics

**Grades:**
- A: 90-100
- B: 80-89
- C: 70-79
- D: 60-69
- F: <60

---

## Interpreting Reports

### CSV File
- Import into Excel, Google Sheets, or Canvas
- Contains: Student name, score, grade, metric breakdowns
- Best for: Gradebook integration

### JSON File
- Full detailed data for programmatic analysis
- Contains: All metrics with descriptions and values
- Best for: Custom analysis, visualization, data processing

### Text File
- Human-readable summary and per-student feedback
- Contains: Class statistics, individual feedback, warnings
- Best for: Quick review, identifying issues

---

## Troubleshooting

### Token Error
```
Failed to authenticate with GitHub
```
**Solution:** Check token is valid and has correct scopes:
```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Organization Not Found
```
Error fetching repositories
```
**Solution:** Verify organization name matches exactly (case-sensitive):
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/your-org
```

### No Repositories Found
```
Found 0 repositories
```
**Solution:** Check the pattern matches your repo naming:
```bash
# List repos in org to see actual names
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/your-org/repos?per_page=100
```

---

## Customizing Scores

Edit `config/default_config.yaml` to adjust weights:

**Example: Emphasize Code Quality Over Frequency**
```yaml
scoring:
  commit_frequency: 15      # Down from 25
  commit_quality: 40        # Up from 25
  individual_contribution: 25
  branch_strategy: 10
  documentation: 10
```

**Example: Stricter Contribution Balance Detection**
```yaml
contribution:
  flag_anomaly: 0.6  # Flag if >60% (was 80%)
```

**Example: Higher Commit Message Quality Standards**
```yaml
commit_quality:
  min_length: 20     # Up from 10
  good_length: 100   # Up from 50
```

Then run again to see new results!

---

## Next Steps

- Check the full documentation in `README.md`
- See example configurations in `config/`
- Review the feedback in `evaluation_report.txt`
- Customize scores in `default_config.yaml`
- Share results with your class (CSV file)

---

## Need Help?

- Check if token has correct permissions (repo:public_repo, read:org)
- Verify organization name and repository pattern
- Ensure evaluation dates are within actual commits
- Review `evaluation_report.txt` for per-student feedback
