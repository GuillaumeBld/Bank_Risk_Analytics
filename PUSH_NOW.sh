#!/bin/bash

# One-Command Git Push Script
# Execute this to stage, commit, and push all changes

echo "=========================================="
echo "Git Push - ESG Bank Risk Analysis"
echo "=========================================="
echo ""

cd "/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank"

# Stage all changes
echo "1️⃣ Staging all changes..."
git add .

# Show summary
echo ""
echo "2️⃣ Changes to be committed:"
git status --short | head -20
echo "... (showing first 20 files)"
echo ""

# Ask for confirmation
read -p "Proceed with commit and push? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    # Commit
    echo ""
    echo "3️⃣ Committing changes..."
    git commit -F docs/status/GIT_COMMIT_MESSAGE.txt
    
    # Push
    echo ""
    echo "4️⃣ Pushing to remote..."
    BRANCH=$(git branch --show-current)
    git push origin $BRANCH
    
    echo ""
    echo "=========================================="
    echo "✅ SUCCESS! Repository pushed to GitHub"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Verify on GitHub"
    echo "2. Email Professor Jalilvand"
    echo "3. Continue with paper revisions"
    echo ""
else
    echo ""
    echo "Push cancelled. No changes made."
    echo ""
fi
