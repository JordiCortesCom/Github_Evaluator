"""
Example usage and test scenarios for GitHub Evaluator.
"""

# TEST SCENARIO 1: Evaluate all repositories in an organization
# python main.py --org my-classroom

# TEST SCENARIO 2: Evaluate only assignment repositories
# python main.py --org my-classroom --pattern "assignment-"

# TEST SCENARIO 3: Custom evaluation period
# python main.py \
#   --org my-classroom \
#   --pattern "assignment-" \
#   --start-date 2024-09-01 \
#   --end-date 2024-12-31

# TEST SCENARIO 4: Custom output directory and formats
# python main.py \
#   --org my-classroom \
#   --output-dir ~/grades \
#   --formats csv txt

# TEST SCENARIO 5: Override configuration
# python main.py \
#   --org my-classroom \
#   --token ghp_xxxxxxxxxxxx \
#   --config config/custom_config.yaml

# SETUP INSTRUCTIONS:
# 
# 1. Install dependencies:
#    pip install -r requirements.txt
#
# 2. Create GitHub Personal Access Token:
#    - Go to https://github.com/settings/tokens
#    - Click "Generate new token"
#    - Select scopes: repo:public_repo, read:org
#    - Copy the token
#
# 3. Set environment variable:
#    export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
#
# 4. Update config/default_config.yaml:
#    - Set organization name
#    - Set repository pattern (e.g., "assignment-")
#    - Adjust scoring weights if needed
#
# 5. Run evaluation:
#    python main.py --org your-organization --pattern "assignment-"
#
# 6. Check results:
#    ls -la reports/
#    - evaluation_results.csv (for gradebook)
#    - evaluation_results.json (for analysis)
#    - evaluation_report.txt (human readable)

"""
Sample Configuration Customization
"""

# config/custom_config.yaml Example:

# github:
#   token: "${GITHUB_TOKEN}"
#   organization: "my-fall-2024-class"
#   classroom_prefix: "assignment-"
# 
# evaluation:
#   start_date: "2024-09-01"
#   end_date: "2024-12-15"
# 
# scoring:
#   commit_frequency: 30      # Increased weight
#   commit_quality: 20        # Decreased weight
#   individual_contribution: 25
#   branch_strategy: 15
#   documentation: 10
# 
# commit_quality:
#   min_length: 15            # Higher minimum
#   good_length: 75           # Higher good threshold
# 
# contribution:
#   flag_anomaly: 0.7         # More strict (70%)
# 
# grading:
#   excellent: 95
#   good: 85
#   satisfactory: 75
#   passing: 65


"""
Post-Evaluation Analysis
"""

# After running the evaluator:

# 1. Import results into gradebook:
#    - Open evaluation_results.csv in your grade management system
#    - Map scores to your grading scale

# 2. Identify students needing help:
#    - Check evaluation_report.txt for feedback
#    - Look for "anomaly_detected" in JSON for imbalanced teams
#    - Review commit quality scores for documentation issues

# 3. Customize thresholds:
#    - Adjust scoring weights based on your priorities
#    - Run evaluator again with different configuration
#    - Compare results

# 4. Analyze trends:
#    - Use JSON output with pandas for statistical analysis
#    - Track metrics over multiple assignments
#    - Identify common improvement areas
