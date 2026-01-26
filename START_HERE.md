# 🎓 GitHub Evaluator - Start Here

**A complete Python system to automatically grade 30+ students' GitHub repositories based on Git best practices, commit quality, and team collaboration.**

---

## ✨ What This Does

Evaluates student GitHub repositories on:
- ✅ **Commit Frequency** (25%) - How often they commit
- ✅ **Commit Quality** (25%) - How clear their messages are  
- ✅ **Individual Contribution** (30%) - Fair distribution of work
- ✅ **Branch Strategy** (10%) - Proper use of branches
- ✅ **Documentation** (10%) - README and description

**Result:** Automated grade (A-F) + detailed feedback for each student

---

## 🚀 Quick Start (5 minutes)

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Get GitHub Token
1. Visit https://github.com/settings/tokens/new
2. Create token with `repo:public_repo` + `read:org` scopes
3. Copy the token

### 3. Set Token
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### 4. Edit Configuration
Open `config/default_config.yaml` and change:
```yaml
github:
  organization: "your-classroom-org"  # Change this!
  classroom_prefix: "assignment-"      # Match your repo names
```

### 5. Run Evaluation
```bash
python main.py --org your-classroom-org --pattern "assignment-"
```

### 6. Check Results
```bash
ls reports/
# evaluation_results.csv     <- Import to gradebook
# evaluation_results.json    <- Full detailed data
# evaluation_report.txt      <- Human readable
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [README.md](README.md) | Full documentation |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Technical overview |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design details |

---

## 🎯 Key Features

### Automated Grading
```bash
python main.py --org my-classroom --pattern "assignment-"
```
Evaluates all student repos in seconds!

### Fully Customizable
```bash
# Adjust evaluation period
python main.py --org my-classroom --start-date 2024-09-01 --end-date 2024-09-30

# Different report formats
python main.py --org my-classroom --formats csv json txt
```

### Multiple Output Formats
- **CSV**: Import into Canvas/Blackboard/Google Classroom
- **JSON**: Full data for analysis and visualization
- **Text**: Human-readable summary and per-student feedback

### Configurable Scoring
Edit `config/default_config.yaml` to:
- Adjust weight of each metric
- Change quality thresholds
- Customize grade cutoffs
- Set anomaly detection levels

---

## 📊 Example Results

### CSV Output
```
student,repository,final_score,letter_grade
alice,assignment-alice,85.5,B
bob,assignment-bob,72.0,C
charlie,assignment-charlie,92.3,A
```

### Text Report
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
Final Score: 85.50/100
Grade: B
Feedback: ✓ Good commit frequency | ✓ Excellent commit message quality
```

---

## 🔧 Project Structure

```
Github_Evaluator/
├── main.py                      ← Run this: python main.py --org ...
├── requirements.txt             ← Dependencies
├── config/
│   └── default_config.yaml      ← Customize evaluation rules
├── src/
│   ├── github_client.py         ← Fetches data from GitHub
│   ├── metrics.py               ← Calculates 5 metrics
│   ├── grader.py                ← Assigns final grades
│   ├── evaluator.py             ← Orchestrates evaluation
│   └── reporter.py              ← Generates reports
├── reports/                     ← Output directory (auto-created)
├── START_HERE.md               ← This file
├── QUICKSTART.md               ← 5-minute setup
├── README.md                   ← Full documentation
├── ARCHITECTURE.md             ← Technical design
└── PROJECT_SUMMARY.md          ← Overview
```

---

## 💡 Common Tasks

### Evaluate Single Assignment
```bash
python main.py --org classroom-org --pattern "assignment-1-"
```

### Export Only for Gradebook
```bash
python main.py --org classroom-org --formats csv
```

### Different Date Range
```bash
python main.py \
  --org classroom-org \
  --start-date 2024-09-01 \
  --end-date 2024-09-30
```

### Custom Configuration
```bash
python main.py \
  --config config/my_custom_config.yaml \
  --org classroom-org
```

### See All Options
```bash
python main.py --help
```

---

## 🎓 Scoring Details

### Commit Frequency (25%)
- **Ideal:** 5-10 commits per student
- **Evaluates:** How often they commit (collaboration indicator)
- **Penalizes:** Solo work or very few commits

### Commit Message Quality (25%)
- **Minimum:** 10 characters
- **Good:** 50+ characters
- **Penalizes:** Vague messages like "fix" or "update"

### Individual Contribution (30%)
- **Flags:** One person >80% of commits
- **Rewards:** Equal participation
- **Penalizes:** Solo work (30 point base)

### Branch Strategy (10%)
- **Rewards:** Multiple branches, feature branches, develop branch
- **Evaluates:** Proper git workflow usage

### Documentation (10%)
- **Checks:** README.md existence
- **Checks:** Repository description
- **Rewards:** Complete documentation

### Final Score
```
Score = (Freq×0.25 + Quality×0.25 + Contribution×0.30 + 
         Branch×0.10 + Documentation×0.10)

Grades:
  A: 90-100
  B: 80-89
  C: 70-79
  D: 60-69
  F: <60
```

---

## ⚙️ System Requirements

- Python 3.8+
- GitHub API token
- Internet connection
- ~1 minute per 30 students

---

## 🆘 Troubleshooting

### "GitHub token not provided"
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### "Organization not found"
```bash
# Verify org name (case-sensitive)
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/orgs/your-org
```

### "No repositories found"
```bash
# Check repository naming pattern
python main.py --org your-org --pattern ""  # Empty pattern = all repos
```

### More help?
- Check [QUICKSTART.md](QUICKSTART.md) for detailed setup
- See [README.md](README.md) for full documentation
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design

---

## 📈 Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Get GitHub token: https://github.com/settings/tokens/new
3. ✅ Set token: `export GITHUB_TOKEN=ghp_xxxxx`
4. ✅ Edit `config/default_config.yaml` with your org name
5. ✅ Run evaluation: `python main.py --org your-org --pattern "assignment-"`
6. ✅ Import CSV to gradebook
7. ✅ Share feedback with students

---

## 📝 Example Workflow

```bash
# Set up once
export GITHUB_TOKEN=ghp_your_token

# Evaluate assignment 1
python main.py --org my-classroom --pattern "assignment-1-"
cat reports/evaluation_report.txt
cp reports/evaluation_results.csv ~/grades/assignment_1.csv

# Evaluate assignment 2 (different dates)
python main.py --org my-classroom \
  --pattern "assignment-2-" \
  --start-date 2024-09-15 \
  --end-date 2024-09-22

# Compare results over time
# Use JSON output for analysis
python main.py --org my-classroom --formats json
# Process with pandas, matplotlib, etc.
```

---

## 🎉 You're Ready!

The system is fully set up and ready to evaluate your students. 

**Next:** Follow the Quick Start above or read [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

**Questions?** Check the [README.md](README.md) for comprehensive documentation.

---

**Happy Grading! 🚀**
