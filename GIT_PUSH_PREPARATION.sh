#!/bin/bash

# Git Push Preparation Script
# Date: October 14, 2025
# Purpose: Prepare clean repository for git push

echo "=========================================="
echo "Git Push Preparation"
echo "=========================================="

cd "/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank"

# Check git status
echo ""
echo "1️⃣ Current Git Status:"
echo "----------------------------------------"
git status --short

# Show untracked files
echo ""
echo "2️⃣ Untracked Files:"
echo "----------------------------------------"
git ls-files --others --exclude-standard

# Check if archive directory is gitignored
echo ""
echo "3️⃣ Checking .gitignore:"
echo "----------------------------------------"
if grep -q "archive/2025_10_14_working_drafts" .gitignore 2>/dev/null; then
    echo "✅ Archive directory is gitignored"
else
    echo "⚠️  Adding archive directory to .gitignore..."
    echo "" >> .gitignore
    echo "# Archive of working drafts (October 14, 2025)" >> .gitignore
    echo "archive/2025_10_14_working_drafts/" >> .gitignore
    echo "✅ Added to .gitignore"
fi

# Show what will be committed
echo ""
echo "4️⃣ Files Staged for Commit:"
echo "----------------------------------------"
git diff --cached --name-status

# Show modified files not staged
echo ""
echo "5️⃣ Modified Files (Not Staged):"
echo "----------------------------------------"
git diff --name-status

echo ""
echo "=========================================="
echo "Recommended Git Commands"
echo "=========================================="
echo ""
echo "# Stage all changes:"
echo "git add ."
echo ""
echo "# Review what will be committed:"
echo "git status"
echo ""
echo "# Commit with prepared message:"
echo "git commit -F docs/status/GIT_COMMIT_MESSAGE.txt"
echo ""
echo "# Or commit with inline message:"
echo 'git commit -m "Complete Analysis: ESG and Bank Default Risk (Daily Volatility Implementation)"'
echo ""
echo "# Push to remote:"
echo "git push origin main"
echo ""
echo "# Or if you're on a different branch:"
echo "git push origin \$(git branch --show-current)"
echo ""
echo "=========================================="
echo ""

# Optional: Show recent commits
echo "6️⃣ Recent Commits (Last 3):"
echo "----------------------------------------"
git log --oneline -3

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

# Count files to be committed
MODIFIED_COUNT=$(git status --short | grep "^ M" | wc -l | tr -d ' ')
NEW_COUNT=$(git status --short | grep "^??" | wc -l | tr -d ' ')
DELETED_COUNT=$(git status --short | grep "^ D" | wc -l | tr -d ' ')

echo "Modified files: $MODIFIED_COUNT"
echo "New files: $NEW_COUNT"
echo "Deleted files: $DELETED_COUNT"
echo ""

echo "✅ Repository is organized and ready to push!"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Stage files: git add ."
echo "3. Commit: git commit -F GIT_COMMIT_MESSAGE.txt"
echo "4. Push: git push origin main"
echo ""
echo "=========================================="
