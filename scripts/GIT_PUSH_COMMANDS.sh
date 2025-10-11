#!/bin/bash
# Git Push Script - Leverage Threshold Implementation
# Date: 2025-10-08
# Run this script to commit and push all changes

# Navigate to repo
cd "$(dirname "$0")"

echo "=========================================="
echo "Git Push: Leverage Threshold Implementation"
echo "=========================================="
echo ""

# Show current status
echo "Current git status:"
git status --short
echo ""

# Stage core implementation files
echo "Staging core implementation..."
git add trim.ipynb
git add dd_pd_accounting.ipynb
git add dd_pd_market.ipynb
git add merging.ipynb
git add analysis.ipynb

# Stage documentation
echo "Staging documentation..."
git add docs/writing/markdown/dd_and_pd.md
git add docs/writing/markdown/leverage_threshold_recommendation.md
git add docs/writing/markdown/2018_anomaly_investigation.md
git add docs/writing/markdown/bank_comparison_report.md

# Stage project documentation
echo "Staging project documentation..."
git add IMPLEMENTATION_SUMMARY.md
git add VERIFICATION_RESULTS.md
git add FINAL_COMPLETION_REPORT.md
git add DOCUMENTATION_REVIEW_COMPLETE.md
git add COMMIT_SUMMARY.md
git add README.md

# Stage analysis scripts
echo "Staging analysis scripts..."
git add find_leverage_threshold.py
git add diagnose_volatility.py
git add bank_comparison_script.py

# Stage utility files
echo "Staging utilities..."
git add utils/
git add tests/

# Stage other modified files
echo "Staging other modified files..."
git add .gitignore
git add solver_diagnostics.ipynb

echo ""
echo "Staged files:"
git status --short
echo ""

# Show what will be committed
echo "=========================================="
echo "Files ready to commit:"
echo "=========================================="
git diff --cached --name-status
echo ""

# Ask for confirmation
read -p "Proceed with commit? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Commit cancelled."
    exit 1
fi

# Commit with comprehensive message
echo ""
echo "Committing changes..."
git commit -m "feat: Implement leverage-based exclusion filter (TD/TA >= 2%)

Complete implementation of leverage threshold filter with documentation and verification.

Core Implementation:
- trim.ipynb: Add Step 2.5 Leverage-Based Exclusion
- trim.ipynb: Fix DD/NaN logic for low_leverage_td_ta status
- dd_pd_accounting.ipynb: Update 2-year volatility window
- dd_pd_market.ipynb: Update 2-year volatility window
- analysis.ipynb: Fix TD/TA column handling

Impact:
- Excludes 184 observations (12.9%) with TD/TA < 2%
- Reduces 2018 DD anomaly: mean -5.3%, max -8.0%
- Maintains 87.1% of sample (1,247 observations)
- Removes mechanical DD inflation from atypical banks

Documentation:
- dd_and_pd.md: Version 3.1 with Section 5.2.3 (Leverage Filter)
- leverage_threshold_recommendation.md: Technical analysis
- 2018_anomaly_investigation.md: Root cause analysis
- bank_comparison_report.md: BAC/JPM/MFIN/FBIZ comparison
- Complete verification and completion reports

Analysis Scripts:
- find_leverage_threshold.py: Threshold optimization
- diagnose_volatility.py: 2-year vs 3-year comparison
- bank_comparison_script.py: Automated comparison

Testing:
- 100% verification success
- All 184 low_leverage_td_ta observations confirmed
- DD values properly set to NaN
- ESG data preserved (99.5%)

Status: Ready for publication and manuscript preparation"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Commit successful!"
    echo "=========================================="
    echo ""
    
    # Ask to push
    read -p "Push to GitHub? (y/n): " push_confirm
    if [ "$push_confirm" = "y" ]; then
        echo ""
        echo "Pushing to GitHub..."
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "=========================================="
            echo "✅ Successfully pushed to GitHub!"
            echo "=========================================="
            echo ""
            echo "Next steps:"
            echo "1. Verify on GitHub: https://github.com/[your-repo]"
            echo "2. Create release tag: git tag -a v3.1.0 -m 'Leverage filter v3.1'"
            echo "3. Push tag: git push origin v3.1.0"
        else
            echo "❌ Push failed. Check your GitHub credentials and try again."
        fi
    else
        echo ""
        echo "Commit completed but not pushed."
        echo "To push later, run: git push origin main"
    fi
else
    echo "❌ Commit failed. Please check the error messages above."
    exit 1
fi

echo ""
echo "Done!"
