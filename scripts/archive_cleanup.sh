#!/bin/bash

# Repository Cleanup Script
# Date: October 14, 2025
# Purpose: Archive working documents and prepare for clean git push

echo "=========================================="
echo "Repository Cleanup - October 14, 2025"
echo "=========================================="

# Define base paths
BASE_DIR="/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank"
ARCHIVE_BASE="$BASE_DIR/archive/2025_10_14_working_drafts"

# Create archive structure
echo "Creating archive structure..."
mkdir -p "$ARCHIVE_BASE/email_drafts"
mkdir -p "$ARCHIVE_BASE/paper_drafts"
mkdir -p "$ARCHIVE_BASE/analysis_summaries"
mkdir -p "$ARCHIVE_BASE/old_datasheets"
mkdir -p "$ARCHIVE_BASE/migration_docs"
mkdir -p "$ARCHIVE_BASE/old_scripts"

# Move email drafts
echo "Archiving email drafts..."
mv "$BASE_DIR/papers/EMAIL_1_VOLATILITY_UPDATE_ENHANCED.md" "$ARCHIVE_BASE/email_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/EMAIL_2_2SLS_RESULTS.md" "$ARCHIVE_BASE/email_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/EMAIL_3_EXPLANATIONS.md" "$ARCHIVE_BASE/email_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/EMAIL_TO_PROFESSOR.md" "$ARCHIVE_BASE/email_drafts/" 2>/dev/null

# Move paper working documents
echo "Archiving paper working documents..."
mv "$BASE_DIR/papers/EXECUTIVE_SUMMARY.md" "$ARCHIVE_BASE/paper_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/IMMEDIATE_REVISIONS_CHECKLIST.md" "$ARCHIVE_BASE/paper_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/LITERATURE_VALIDATION_ANALYSIS.md" "$ARCHIVE_BASE/paper_drafts/" 2>/dev/null
mv "$BASE_DIR/papers/ROBUSTNESS_2021_SUMMARY.md" "$ARCHIVE_BASE/paper_drafts/" 2>/dev/null

# Move old datasheets (keep only the latest)
echo "Archiving old datasheets..."
mv "$BASE_DIR/data/outputs/datasheet/accounting_20251014_022117.csv" "$ARCHIVE_BASE/old_datasheets/" 2>/dev/null
mv "$BASE_DIR/data/outputs/datasheet/market_20251014_022125.csv" "$ARCHIVE_BASE/old_datasheets/" 2>/dev/null
mv "$BASE_DIR/data/outputs/datasheet/merged_20251014_022322.csv" "$ARCHIVE_BASE/old_datasheets/" 2>/dev/null
mv "$BASE_DIR/data/outputs/datasheet/esg_dd_pd_1100.xlsx" "$ARCHIVE_BASE/old_datasheets/" 2>/dev/null
mv "$BASE_DIR/data/outputs/datasheet/esg_dd_pd_1110.xlsx" "$ARCHIVE_BASE/old_datasheets/" 2>/dev/null

# Move old analysis files
echo "Archiving old analysis summaries..."
mv "$BASE_DIR/data/outputs/analysis/accounting_20251004_041436_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/accounting_20251011_035109_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/accounting_20251011_040830_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/accounting_20251011_042343_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/accounting_20251011_042604_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/market_20251004_050613_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/market_20251011_035307_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/market_20251011_042302_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/market_20251011_042610_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/market_20251011_042629_summary.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/extreme_accounting_20251008_055912.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/extreme_market_20251008_055912.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/outliers_accounting_20251008_081905.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/outliers_market_20251008_081905.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/sample_sizes_20251008_055405.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/sample_sizes_20251008_055603.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/sample_sizes_20251008_055912.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/sample_sizes_20251008_081905.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/regression_summary_20251008_055913.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/volatility_comparison_analysis.png" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null
mv "$BASE_DIR/data/outputs/analysis/volatility_comparison_data.csv" "$ARCHIVE_BASE/analysis_summaries/" 2>/dev/null

# Move migration documentation
echo "Archiving migration documentation..."
mv "$BASE_DIR/migration_to_daily_volatility" "$ARCHIVE_BASE/migration_docs/" 2>/dev/null

# Move old fix scripts
echo "Archiving old fix scripts..."
mv "$BASE_DIR/scripts/fix_accounting_FINAL.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_accounting_add_flags.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_accounting_notebook.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_accounting_notebook_v2.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_duplicates.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_market_notebook_sigma.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_market_notebook_v2.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_market_notebook_v3.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_market_notebook_v4_COMPLETE.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_merging_FINAL.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_merging_display.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/fix_merging_notebook.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/patch_notebooks.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/patch_notebooks_v2.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/analyze_early_years_coverage.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/analyze_return_data_coverage.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/create_total_return_mapping.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/deep_dive_return_data.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/diagnose_volatility.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/find_leverage_threshold.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/investigate_2018.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/link_latest_dd_outputs.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null
mv "$BASE_DIR/scripts/validate_instruction3.py" "$ARCHIVE_BASE/old_scripts/" 2>/dev/null

# Create archive README
echo "Creating archive README..."
cat > "$ARCHIVE_BASE/README.md" << 'EOF'
# Archive: October 14, 2025 - Working Drafts & Migration Docs

## Contents

### Email Drafts (`email_drafts/`)
- Email drafts to Professor Jalilvand about:
  1. Daily volatility implementation
  2. 2SLS regression results
  3. Literature validation and mechanisms
  4. Comprehensive email with all findings

### Paper Drafts (`paper_drafts/`)
- Executive summary of complete paper
- Immediate revisions checklist (based on literature validation)
- Literature validation analysis (5 papers from 2024-2025)
- Robustness check excluding 2021 anomaly year

### Old Datasheets (`old_datasheets/`)
- Intermediate versions of accounting, market, and merged datasets
- Kept for reference but superseded by final version:
  - `esg_dd_pd_20251014_022322.csv` (current, in main datasheet folder)

### Analysis Summaries (`analysis_summaries/`)
- Multiple iterations of summary statistics
- Outlier analysis results
- Sample size checks
- Volatility comparison analyses

### Migration Documentation (`migration_docs/`)
- Complete migration from annual to daily volatility
- Implementation plans, checklists, validation tests
- All documentation from the volatility calculation update

### Old Scripts (`old_scripts/`)
- Fix scripts used during debugging and migration
- Analysis scripts for specific investigations
- Validation and diagnostic tools
- Kept for reference but no longer needed for regular workflow

## Current State (Post-Cleanup)

**Active Files Only**:
- Main notebooks: `dd_pd_accounting.ipynb`, `dd_pd_market.ipynb`, `merging.ipynb`
- Final dataset: `data/outputs/datasheet/esg_dd_pd_20251014_022322.csv`
- Paper drafts: `papers/ESG_and_Bank_Default_Risk_Part1-3.md`
- Analysis results: Latest summaries and regression output
- Core scripts: Volatility calculator, pillar decomposition, robustness checks

**Why Archived**:
- Working documents no longer needed for active development
- Intermediate data files superseded by final version
- Migration documentation completed and frozen
- Old fix scripts no longer relevant after bugs resolved

## Recovery

If you need any archived file:
```bash
# Files are in: archive/2025_10_14_working_drafts/
# Structure preserved with original organization
```

**Date**: October 14, 2025  
**Status**: Migration complete, daily volatility implemented, paper drafted, results validated
EOF

echo ""
echo "=========================================="
echo "Cleanup Summary"
echo "=========================================="
echo "✅ Archived email drafts"
echo "✅ Archived paper working documents"
echo "✅ Archived old datasheets"
echo "✅ Archived old analysis summaries"
echo "✅ Archived migration documentation"
echo "✅ Archived old fix scripts"
echo "✅ Created archive README"
echo ""
echo "Archive location: archive/2025_10_14_working_drafts/"
echo ""
echo "Repository is now clean and ready for git push!"
echo "=========================================="
