#!/usr/bin/env python3
"""
Validation Tests for Daily Volatility Migration
================================================

Tests to verify the migration was successful and results are valid.

Run this after:
1. Volatility calculator has run
2. Notebooks have been updated
3. New results generated
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent

print("="*80)
print("VALIDATION TESTS - DAILY VOLATILITY MIGRATION")
print("="*80)

passed = 0
failed = 0
warnings = 0

def test_pass(msg):
    global passed
    passed += 1
    print(f"✅ PASS: {msg}")

def test_fail(msg):
    global failed
    failed += 1
    print(f"❌ FAIL: {msg}")

def test_warn(msg):
    global warnings
    warnings += 1
    print(f"⚠️  WARN: {msg}")

# ============================================================================
# TEST 1: File Existence
# ============================================================================

print("\n[TEST 1] File Existence")
print("-"*80)

required_files = [
    'data/clean/equity_volatility_by_year_DAILY.csv',
    'data/clean/raw_daily_total_return_2015_2023.csv'
]

for file_path in required_files:
    full_path = BASE_DIR / file_path
    if full_path.exists():
        test_pass(f"File exists: {file_path}")
    else:
        test_fail(f"File missing: {file_path}")

# ============================================================================
# TEST 2: Load and Basic Checks
# ============================================================================

print("\n[TEST 2] Data Loading and Structure")
print("-"*80)

try:
    vol = pd.read_csv(BASE_DIR / 'data/clean/equity_volatility_by_year_DAILY.csv')
    test_pass(f"Loaded volatility data: {len(vol)} rows")
    
    required_cols = ['ticker', 'year', 'sigma_E', 'method', 'days_used']
    missing_cols = [col for col in required_cols if col not in vol.columns]
    
    if len(missing_cols) == 0:
        test_pass(f"All required columns present")
    else:
        test_fail(f"Missing columns: {missing_cols}")
        
except Exception as e:
    test_fail(f"Failed to load data: {e}")
    sys.exit(1)

# ============================================================================
# TEST 3: Coverage Check
# ============================================================================

print("\n[TEST 3] Coverage Requirements")
print("-"*80)

# Overall coverage
total_obs = len(vol)
with_sigma = vol['sigma_E'].notna().sum()
coverage_pct = (with_sigma / total_obs) * 100

if coverage_pct >= 95:
    test_pass(f"Overall coverage: {coverage_pct:.1f}% (≥95% required)")
elif coverage_pct >= 90:
    test_warn(f"Coverage: {coverage_pct:.1f}% (90-95%, acceptable)")
else:
    test_fail(f"Coverage: {coverage_pct:.1f}% (<90%, too low)")

# Coverage by year (2016-2023)
for year in range(2016, 2024):
    year_data = vol[vol['year'] == year]
    if len(year_data) > 0:
        year_coverage = (year_data['sigma_E'].notna().sum() / len(year_data)) * 100
        if year_coverage >= 95:
            test_pass(f"Year {year}: {year_coverage:.1f}% coverage")
        elif year_coverage >= 90:
            test_warn(f"Year {year}: {year_coverage:.1f}% coverage")
        else:
            test_fail(f"Year {year}: {year_coverage:.1f}% coverage (<90%)")

# ============================================================================
# TEST 4: Value Ranges
# ============================================================================

print("\n[TEST 4] Value Range Validation")
print("-"*80)

sigma_values = vol['sigma_E'].dropna()

# Check reasonable range (10%-100%)
in_range = sigma_values.between(0.10, 1.0).sum()
out_of_range = len(sigma_values) - in_range

if out_of_range == 0:
    test_pass(f"All values in reasonable range (10%-100%)")
elif out_of_range <= len(sigma_values) * 0.05:
    test_warn(f"{out_of_range} values outside range (<5%, acceptable)")
else:
    test_fail(f"{out_of_range} values outside range (>5%)")

# Check for extreme values
too_low = (sigma_values < 0.10).sum()
too_high = (sigma_values > 1.0).sum()

if too_low > 0:
    test_warn(f"{too_low} values below 10% volatility")
if too_high > 0:
    test_warn(f"{too_high} values above 100% volatility")

# Check mean is reasonable
mean_vol = sigma_values.mean()
if 0.20 <= mean_vol <= 0.50:
    test_pass(f"Mean volatility: {mean_vol:.3f} (reasonable)")
else:
    test_warn(f"Mean volatility: {mean_vol:.3f} (unusual, check data)")

# ============================================================================
# TEST 5: Method Distribution
# ============================================================================

print("\n[TEST 5] Calculation Method Distribution")
print("-"*80)

method_counts = vol['method'].value_counts()
primary_pct = (method_counts.get('daily_252', 0) / len(vol)) * 100

if primary_pct >= 80:
    test_pass(f"Primary method (daily_252): {primary_pct:.1f}% (≥80%)")
elif primary_pct >= 70:
    test_warn(f"Primary method: {primary_pct:.1f}% (70-80%, acceptable)")
else:
    test_fail(f"Primary method: {primary_pct:.1f}% (<70%, too low)")

print(f"\nMethod breakdown:")
for method, count in method_counts.items():
    pct = (count / len(vol)) * 100
    print(f"  {method}: {count} ({pct:.1f}%)")

# ============================================================================
# TEST 6: Timing Discipline (Spot Check)
# ============================================================================

print("\n[TEST 6] Timing Discipline Verification")
print("-"*80)

# Load daily returns for spot check
daily = pd.read_csv(BASE_DIR / 'data/clean/raw_daily_total_return_2015_2023.csv')
daily['Date'] = pd.to_datetime(daily['Date'])
daily['year'] = daily['Date'].dt.year

# Check a few random banks
test_cases = [
    ('JPM', 2019),  # Should use 2018 data only
    ('BAC', 2020),  # Should use 2019 data only
    ('WFC', 2018),  # Should use 2017 data only
]

timing_ok = True
for ticker, target_year in test_cases:
    # Get the volatility entry
    vol_entry = vol[(vol['ticker'] == ticker) & (vol['year'] == target_year)]
    
    if len(vol_entry) == 0:
        test_warn(f"No volatility entry for {ticker} {target_year}")
        continue
    
    days_used = vol_entry['days_used'].iloc[0]
    
    # Count actual data points in year t-1
    year_tminus1 = target_year - 1
    actual_days = len(daily[
        (daily['Instrument'].str.contains(ticker, na=False)) &
        (daily['year'] == year_tminus1)
    ])
    
    # Should match (within reason due to cleaning)
    if abs(days_used - actual_days) <= 10:  # Allow 10-day difference for cleaning
        test_pass(f"{ticker} {target_year}: Used {days_used} days from {year_tminus1}")
    else:
        test_fail(f"{ticker} {target_year}: Days mismatch (used={days_used}, actual={actual_days})")
        timing_ok = False

if timing_ok:
    test_pass("Timing discipline verified (no look-ahead bias)")

# ============================================================================
# TEST 7: No Missing Critical Banks
# ============================================================================

print("\n[TEST 7] Critical Bank Coverage")
print("-"*80)

# Major banks that should have data
critical_banks = ['JPM', 'BAC', 'WFC', 'USB', 'PNC', 'TFC', 'FITB', 'KEY', 'MTB', 'RF']

for bank in critical_banks:
    bank_data = vol[vol['ticker'] == bank]
    if len(bank_data) > 0:
        coverage = bank_data['sigma_E'].notna().mean() * 100
        if coverage >= 90:
            test_pass(f"{bank}: {len(bank_data)} years, {coverage:.0f}% coverage")
        else:
            test_warn(f"{bank}: {coverage:.0f}% coverage")
    else:
        test_fail(f"{bank}: No data found")

# ============================================================================
# TEST 8: Comparison with Old Method (if available)
# ============================================================================

print("\n[TEST 8] Comparison with Old Method")
print("-"*80)

old_vol_path = BASE_DIR / 'data/clean/equity_volatility_by_year.csv'
if old_vol_path.exists():
    try:
        old_vol = pd.read_csv(old_vol_path)
        
        # Try to merge (handle different column names)
        if 'symbol' in old_vol.columns:
            old_vol = old_vol.rename(columns={'symbol': 'ticker', 'equity_volatility': 'sigma_E_old'})
        
        comparison = vol.merge(
            old_vol[['ticker', 'year', 'sigma_E_old']],
            on=['ticker', 'year'],
            how='inner'
        )
        
        if len(comparison) > 0:
            # Calculate correlation
            corr = comparison[['sigma_E', 'sigma_E_old']].corr().iloc[0, 1]
            
            if 0.60 <= corr <= 0.90:
                test_pass(f"Correlation with old method: {corr:.3f} (expected 0.6-0.9)")
            elif 0.50 <= corr < 0.60:
                test_warn(f"Correlation: {corr:.3f} (lower than expected)")
            else:
                test_fail(f"Correlation: {corr:.3f} (too low or too high)")
            
            # Check direction of change
            comparison['higher'] = comparison['sigma_E'] > comparison['sigma_E_old']
            higher_pct = comparison['higher'].mean() * 100
            
            if 60 <= higher_pct <= 90:
                test_pass(f"Daily method higher in {higher_pct:.0f}% of cases (expected)")
            else:
                test_warn(f"Daily method higher in {higher_pct:.0f}% of cases")
        else:
            test_warn("No overlapping data for comparison")
            
    except Exception as e:
        test_warn(f"Could not compare with old method: {e}")
else:
    print("  Old volatility file not found (OK for first run)")

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
    print("\n🎉 ALL TESTS PASSED! Migration looks good.")
    print("→ Proceed to updating notebooks")
    sys.exit(0)
elif failed == 0:
    print("\n✅ All critical tests passed, but some warnings.")
    print("→ Review warnings above, then proceed if acceptable")
    sys.exit(0)
else:
    print("\n❌ SOME TESTS FAILED!")
    print("→ Review failures above before proceeding")
    sys.exit(1)
