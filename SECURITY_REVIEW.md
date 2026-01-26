# SECURITY & CODE REVIEW - FINDINGS

## 🔴 CRITICAL ISSUES (Must Fix)

### 1. **Path Traversal Vulnerability in main.py**
**Location:** `main.py`, line 103 in `load_config()`
**Severity:** HIGH
**Issue:** Config file path is user-controlled with no validation
```python
with open(config_path, 'r') as f:  # No path validation
    config = yaml.safe_load(f)
```
**Impact:** Attacker could read any file with `--config ../../etc/passwd`
**Fix Required:**
```python
config_path = Path(config_path).resolve()
if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")
# Optionally: restrict to config/ directory
allowed_dir = Path("config").resolve()
if not str(config_path).startswith(str(allowed_dir)):
    raise ValueError("Config path must be in config/ directory")
```

### 2. **Bare Exception Handling in evaluator.py**
**Location:** `src/evaluator.py`, line 146 `_check_readme()`
**Severity:** MEDIUM
**Issue:** 
```python
except:  # Too broad - catches all exceptions
    return False
```
**Impact:** Masks real errors (auth failures, API issues), makes debugging hard
**Fix Required:**
```python
except (GithubException, Exception) as e:
    logger.debug(f"Could not check README: {e}")
    return False
```

### 3. **No Output Path Validation**
**Location:** `src/reporter.py`, line 18 `__init__`
**Severity:** MEDIUM
**Issue:** No validation of output directory path
```python
self.output_dir = Path(output_dir)  # Could create files anywhere
self.output_dir.mkdir(parents=True, exist_ok=True)
```
**Impact:** Could write reports to unexpected locations, overwrite files
**Fix Required:**
```python
output_path = Path(output_dir).resolve()
if not str(output_path).startswith(str(Path.cwd())):
    raise ValueError("Output directory must be within current working directory")
self.output_dir = output_path
```

---

## 🟠 HIGH PRIORITY ISSUES

### 4. **Import Paths Breaking (evaluator.py)**
**Location:** `src/evaluator.py`, lines 9-11
**Severity:** HIGH
**Issue:**
```python
from github_client import GitHubClient  # WRONG - relative import without dots
from metrics import MetricsExtractor
from grader import GradingEngine
```
**Why Fails:** When running from project root (`python main.py`), these imports fail
**Impact:** Project won't run - ImportError
**Fix Required:**
```python
from src.github_client import GitHubClient
from src.metrics import MetricsExtractor
from src.grader import GradingEngine
```

### 5. **GitHub Token Exposed in Logs**
**Location:** `src/github_client.py`, line 27
**Severity:** HIGH
**Issue:**
```python
logger.info(f"Authenticated as: {self.user.login}")  # OK
# BUT: Token could be logged elsewhere in errors
```
**Potential:** If error occurs with token in stack trace
**Fix Required:**
```python
# Add this to prevent token logging
logging.getLogger("github").setLevel(logging.WARNING)
```

### 6. **No Input Validation on Organization/Pattern**
**Location:** `main.py`, line 72-76
**Severity:** MEDIUM
**Issue:** No validation before passing to GitHub API
```python
--org my-classroom  # What if someone passes: ../../../etc/passwd?
--pattern "'; DROP TABLE *; --"  # SQL injection?
```
**Fix Required:**
```python
def validate_github_name(name: str) -> bool:
    """Validate GitHub org/repo names contain only allowed characters"""
    import re
    if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$', name):
        raise ValueError(f"Invalid GitHub name: {name}")
    return True
```

---

## 🟡 MEDIUM PRIORITY BUGS

### 7. **Division by Zero Risk in metrics.py**
**Location:** `src/metrics.py`, line 162
**Severity:** MEDIUM
**Issue:**
```python
avg_percentage = 100 / len(commits_by_author)  # OK
variance = sum(...) / len(distribution)  # This one is protected, good
```
But contribution checking doesn't validate:
```python
# Line 155: total_commits could theoretically be 0
if not commits_by_author:
    return 0, {"distribution": {}, "anomaly_detected": False}  # OK
# But if empty dict: max(distribution.values()) will fail
```
**Fix:** Already handled, but add belt-and-suspenders:
```python
if not distribution:
    return 0, {"distribution": {}, "anomaly_detected": False}
```

### 8. **Empty Results Crash in reporter.py**
**Location:** `src/reporter.py`, line 130
**Severity:** MEDIUM
**Issue:**
```python
max(scores)  # Crashes if scores is empty
min(scores)  # Crashes if scores is empty
```
**Impact:** If evaluation returns 0 repos, text report crashes
**Fix Required:**
```python
if results:
    scores = [r.get("final_score", 0) for r in results]
    if scores:  # Add this check
        highest = max(scores)
        lowest = min(scores)
```

### 9. **Unsafe YAML Loading (Potential)**
**Location:** `main.py`, line 38
**Severity:** LOW (using safe_load, but...)
**Issue:**
```python
config = yaml.safe_load(f)  # Good - using safe_load, not load()
```
**Note:** Current code is correct, but document that users shouldn't edit with untrusted YAML

### 10. **No Date Validation**
**Location:** `src/evaluator.py`, line 53
**Severity:** MEDIUM
**Issue:**
```python
start_date = datetime.fromisoformat(eval_config.get("start_date", "2024-01-01"))
end_date = datetime.fromisoformat(eval_config.get("end_date", "2024-12-31"))
```
**Problem:** If user provides bad date format, crashes with unhelpful error
**Fix Required:**
```python
try:
    start_date = datetime.fromisoformat(eval_config.get("start_date", "2024-01-01"))
except ValueError:
    raise ValueError(f"Invalid start_date format. Use YYYY-MM-DD")
```

### 11. **Double Configuration Loading (main.py)**
**Location:** `main.py`, line 114-116
**Severity:** MEDIUM
**Issue:**
```python
config = load_config(args.config)  # First load
if overrides:
    config = load_config(args.config, overrides)  # Reload - inefficient!
```
**Fix:** Consolidate:
```python
config = load_config(args.config, overrides if overrides else None)
```

---

## 🟢 LOW PRIORITY ISSUES

### 12. **Magic Numbers Without Constants**
**Location:** Multiple files
**Severity:** LOW
**Examples:**
```python
expected_commits_per_person = 7  # Where does 7 come from?
score = 30  # Solo work gets 30 - not in config
score = 50  # Base score - magic number
frequency_ratio = min(total_commits / ideal_total, 1.5)  # 1.5 cap - undocumented
```
**Fix:** Move to config:
```yaml
metrics:
  commit_frequency:
    expected_per_person: 7
    solo_score: 30
  branch_strategy:
    base_score: 50
```

### 13. **Inconsistent Error Handling**
**Location:** Multiple places
**Severity:** LOW
**Issue:**
- `github_client.py` logs errors and returns empty list
- `evaluator.py` lets errors bubble up
- `reporter.py` logs and returns empty string

**Fix:** Document error handling strategy in README

### 14. **No Rate Limit Handling**
**Location:** `src/github_client.py`
**Severity:** LOW (informational)
**Issue:** No handling for GitHub API rate limits (5000/hour)
**Fix:** Optional enhancement:
```python
def check_rate_limit(self):
    rate_limit = self.github.get_rate_limit()
    if rate_limit.core.remaining < 100:
        logger.warning(f"Low rate limit: {rate_limit.core.remaining} remaining")
```

### 15. **No Logging Config in main.py**
**Location:** `main.py`, line 18
**Severity:** LOW
**Issue:** Duplicate logging setup (also in modules)
```python
logging.basicConfig(...)  # In main.py
logging.basicConfig(...)  # In github_client.py
logging.basicConfig(...)  # In evaluator.py
```
**Fix:** Only one in main, remove from modules:
```python
# main.py
logging.basicConfig(..., force=True)
# Modules: logger = logging.getLogger(__name__)
```

---

## 🔧 LOGIC/CALCULATION ISSUES

### 16. **Metrics Weights Not Validated**
**Location:** `main.py` setup
**Severity:** MEDIUM
**Issue:** Config allows weights to not sum to 100
```yaml
scoring:
  commit_frequency: 25
  commit_quality: 25
  individual_contribution: 30
  branch_strategy: 10
  documentation: 10
  # No validation that these sum to 100
```
**Fix Required:**
```python
def validate_weights(config: dict):
    weights = config.get("scoring", {})
    total = sum(weights.values())
    if total != 100:
        raise ValueError(f"Scoring weights must sum to 100, got {total}")
```

### 17. **Contribution Score Anomaly Logic**
**Location:** `src/metrics.py`, line 176-177
**Severity:** LOW (works, but confusing)
**Issue:**
```python
if anomaly_detected:
    score *= 0.7  # Multiply by 0.7 - is this the right penalty?
```
**Better Design:** Could be config:
```yaml
contribution:
  anomaly_penalty: 0.7  # Or 0.5 or 0.3?
```

### 18. **Unused PR Data**
**Location:** `src/evaluator.py`, line 69
**Severity:** LOW (inefficiency)
**Issue:**
```python
prs = self.github.get_pull_requests(repo)  # Fetched but never used
```
**Fix:** Remove or use in metrics

---

## 📋 SUMMARY OF FIXES

| Issue | Severity | Status | Fix Time |
|-------|----------|--------|----------|
| Path traversal config | 🔴 | Must fix | 10 min |
| Import paths (evaluator.py) | 🔴 | Must fix | 5 min |
| Bare except in evaluator | 🔴 | Must fix | 5 min |
| Output path validation | 🟠 | Should fix | 15 min |
| Organization name validation | 🟠 | Should fix | 15 min |
| Date validation | 🟠 | Should fix | 10 min |
| Empty results crash | 🟠 | Should fix | 10 min |
| Token in logs | 🟠 | Should fix | 5 min |
| Weights validation | 🟡 | Nice to have | 15 min |
| Magic numbers to config | 🟡 | Nice to have | 20 min |
| Rate limit handling | 🟢 | Optional | 15 min |

---

## 🎯 RECOMMENDED FIX ORDER

**Phase 1 (CRITICAL - 35 minutes):**
1. Fix import paths in evaluator.py
2. Fix path traversal vulnerability
3. Fix bare exception handling
4. Add organization name validation

**Phase 2 (HIGH - 40 minutes):**
1. Add output path validation
2. Add date validation with error messages
3. Add weights validation
4. Fix token logging risk

**Phase 3 (MEDIUM - Optional):**
1. Move magic numbers to config
2. Add rate limit checking
3. Clean up logging setup
4. Remove unused PR fetching

---

## ✅ WHAT'S GOOD

- ✅ Using `yaml.safe_load()` (not `load()`)
- ✅ PyGithub for auth (not hardcoding tokens)
- ✅ Try-catch in most API calls
- ✅ Comprehensive error messages
- ✅ Type hints throughout
- ✅ Good separation of concerns
- ✅ CSV escaping via DictWriter (safe)
- ✅ JSON default=str (safe serialization)

