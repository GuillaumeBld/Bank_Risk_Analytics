#!/usr/bin/env python3
"""
Validation script for daily volatility migration
Tests key aspects without running full notebooks
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent

print("="*80)
print("MIGRATION VALIDATION")
print("="*80)

passed = 0
failed = 0
warnings = 0

def test_pass(msg):
    global passed
    print(f"✅ PASS: {msg}")
    passed += 1

def test_fail(msg):
    global failed
    print(f"❌ FAIL: {msg}")
    failed += 1

def test_warn(msg):
    global warnings
    print(f"⚠️  WARN: {msg}")
    warnings += 1

# ============================================================================
# TEST 1: Daily Volatility File Exists and Valid
# ============================================================================

print("\n[TEST 1] Daily Volatility File")
print("-"*80)

vol_daily_path = BASE_DIR / 'data/clean/equity_volatility_by_year_DAILY.csv'
if vol_daily_path.exists():
    test_pass(f"File exists: {vol_daily_path.name}")
    
    vol_daily = pd.read_csv(vol_daily_path)
    test_pass(f"Loaded {len(vol_daily)} rows")
    
    required_cols = ['ticker', 'year', 'sigma_E', 'method', 'days_used']
    if all(col in vol_daily.columns for col in required_cols):
        test_pass("All required columns present")
    else:
        test_fail(f"Missing columns: {[c for c in required_cols if c not in vol_daily.columns]}")
    
    # Coverage check
    with_vol = vol_daily['sigma_E'].notna().sum()
    total = len(vol_daily)
    coverage_pct = (with_vol / total) * 100
    
    if coverage_pct >= 90:
        test_pass(f"Coverage: {coverage_pct:.1f}% (≥90% target)")
    else:
        test_fail(f"Coverage: {coverage_pct:.1f}% (<90% target)")
    
    # Method distribution
    method_counts = vol_daily[vol_daily['sigma_E'].notna()]['method'].value_counts()
    primary_pct = (method_counts.get('daily_252', 0) / with_vol) * 100
    
    if primary_pct >= 80:
        test_pass(f"Primary method: {primary_pct:.1f}% (≥80% target)")
    else:
        test_warn(f"Primary method: {primary_pct:.1f}% (<80% target)")
    
    # Value range check
    valid_range = vol_daily['sigma_E'].between(0.01, 3.0)
    if valid_range.all():
        test_pass("All volatility values in reasonable range (1%-300%)")
    else:
        outside = (~valid_range & vol_daily['sigma_E'].notna()).sum()
        test_warn(f"{outside} values outside reasonable range")
        
else:
    test_fail(f"File not found: {vol_daily_path.name}")
    sys.exit(1)

# ============================================================================
# TEST 2: Notebook Files Updated
# ============================================================================

print("\n[TEST 2] Notebook Files Updated")
print("-"*80)

# Check accounting notebook
acc_nb_path = BASE_DIR / 'dd_pd_accounting.ipynb'
if acc_nb_path.exists():
    with open(acc_nb_path, 'r') as f:
        content = f.read()
    
    if 'equity_volatility_by_year_DAILY.csv' in content:
        test_pass("Accounting notebook uses DAILY file")
    else:
        test_fail("Accounting notebook still uses old file path")
    
    if 'Bharath' in content or 'Shumway' in content:
        test_pass("Accounting notebook cites Bharath & Shumway")
    else:
        test_warn("Accounting notebook missing B&S citation")
    
    if 'DATA QUALITY FILTER' in content:
        test_pass("Accounting notebook has data quality filter")
    else:
        test_fail("Accounting notebook missing data quality filter")
else:
    test_fail("Accounting notebook not found")

# Check market notebook
mkt_nb_path = BASE_DIR / 'dd_pd_market.ipynb'
if mkt_nb_path.exists():
    with open(mkt_nb_path, 'r') as f:
        content = f.read()
    
    if 'equity_volatility_by_year_DAILY.csv' in content:
        test_pass("Market notebook uses DAILY file")
    else:
        test_fail("Market notebook still uses old file path")
    
    if 'DATA QUALITY FILTER' in content:
        test_pass("Market notebook has data quality filter")
    else:
        test_fail("Market notebook missing data quality filter")
else:
    test_fail("Market notebook not found")

# ============================================================================
# TEST 3: Documentation Updated
# ============================================================================

print("\n[TEST 3] Documentation Updated")
print("-"*80)

doc_path = BASE_DIR / 'docs/writing/dd_and_pd.md'
if doc_path.exists():
    with open(doc_path, 'r') as f:
        content = f.read()
    
    if 'Daily Returns' in content or 'daily returns' in content:
        test_pass("Documentation mentions daily returns")
    else:
        test_warn("Documentation may not mention daily returns")
    
    if '252' in content:
        test_pass("Documentation mentions 252-day window")
    else:
        test_warn("Documentation missing 252-day reference")
    
    if 'Bharath' in content or 'Shumway' in content:
        test_pass("Documentation cites Bharath & Shumway")
    else:
        test_warn("Documentation missing B&S citation")
    
    if '1,821' in content or '93.1' in content:
        test_pass("Documentation shows updated coverage statistics")
    else:
        test_warn("Documentation may have old coverage numbers")
else:
    test_fail("Main documentation file not found")

# Check for disclosure document
disclosure_path = BASE_DIR / 'docs/writing/DATA_COVERAGE_DISCLOSURE.md'
if disclosure_path.exists():
    test_pass("Data coverage disclosure document created")
else:
    test_warn("Data coverage disclosure document not found")

# ============================================================================
# TEST 4: Comparison Analysis Outputs
# ============================================================================

print("\n[TEST 4] Comparison Analysis")
print("-"*80)

comparison_png = BASE_DIR / 'data/outputs/analysis/volatility_comparison_analysis.png'
if comparison_png.exists():
    test_pass("Comparison visualization created")
else:
    test_warn("Comparison visualization not found")

comparison_csv = BASE_DIR / 'data/outputs/analysis/volatility_comparison_data.csv'
if comparison_csv.exists():
    test_pass("Comparison data CSV created")
    
    comp_data = pd.read_csv(comparison_csv)
    if 'delta_pct' in comp_data.columns:
        mean_change = comp_data['delta_pct'].mean()
        test_pass(f"Mean volatility change: {mean_change:.1f}%")
    
else:
    test_warn("Comparison data CSV not found")

summary_txt = BASE_DIR / 'data/outputs/analysis/migration_summary_report.txt'
if summary_txt.exists():
    test_pass("Migration summary report created")
else:
    test_warn("Migration summary report not found")

# ============================================================================
# TEST 5: Git Branch Status
# ============================================================================

print("\n[TEST 5] Git Branch")
print("-"*80)

import subprocess
try:
    result = subprocess.run(
        ['git', 'branch', '--show-current'],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=5
    )
    
    branch = result.stdout.strip()
    if 'daily-volatility' in branch:
        test_pass(f"On correct branch: {branch}")
    else:
        test_warn(f"On unexpected branch: {branch}")
except:
    test_warn("Could not check git branch")

# ============================================================================
# TEST 6: Old File Still Exists (for backup)
# ============================================================================

print("\n[TEST 6] Backup Status")
print("-"*80)

old_vol_path = BASE_DIR / 'data/clean/equity_volatility_by_year.csv'
if old_vol_path.exists():
    test_pass("Old volatility file still exists (good for backup)")
else:
    test_warn("Old volatility file not found (was it deleted?)")

# ============================================================================
# TEST 7: Migration Documentation
# ============================================================================

print("\n[TEST 7] Migration Documentation")
print("-"*80)

migration_dir = BASE_DIR / 'migration_to_daily_volatility'
if migration_dir.exists():
    test_pass("Migration folder exists")
    
    key_files = [
        'START_HERE.md',
        '05_VOLATILITY_CALCULATOR_SCRIPT.py',
        '06_VALIDATION_TESTS.py',
        '07_COMPARISON_ANALYSIS.py',
        'ADDENDUM_DATA_QUALITY_FILTERING.md',
        'MIGRATION_PROGRESS_REPORT.md'
    ]
    
    for filename in key_files:
        if (migration_dir / filename).exists():
            test_pass(f"Found: {filename}")
        else:
            test_warn(f"Missing: {filename}")
else:
    test_fail("Migration folder not found")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("VALIDATION SUMMARY")
print("="*80)

print(f"\n✅ Tests Passed: {passed}")
print(f"⚠️  Warnings: {warnings}")
print(f"❌ Tests Failed: {failed}")

if failed == 0 and warnings <= 3:
    print("\n✅ MIGRATION VALIDATED - READY TO COMMIT")
    sys.exit(0)
elif failed == 0:
    print("\n⚠️  MIGRATION MOSTLY GOOD - Review warnings before commit")
    sys.exit(0)
else:
    print("\n❌ MIGRATION HAS ISSUES - Fix failures before proceeding")
    sys.exit(1)
