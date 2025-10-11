#!/usr/bin/env python3
"""
Diagnostic: Test 2-year vs 3-year volatility calculation
"""

import pandas as pd
import numpy as np

# Load input data
df = pd.read_csv('data/clean/Book2_clean.csv')
print(f"Loaded {len(df)} observations")
print(f"Years: {sorted(df['year'].unique())}")

# Sort by instrument and year
df = df.sort_values(['instrument', 'year'])

# Test with JPM as example
jpm = df[df['instrument'] == 'JPM'].copy()
print(f"\nJPM data: {len(jpm)} observations")
print(jpm[['instrument', 'year', 'rit']].to_string())

# Calculate 2-year rolling volatility
def rolling_sigma_2year(s):
    """2-year window"""
    return s.shift(1).rolling(2, min_periods=2).std()

# Calculate 3-year rolling volatility  
def rolling_sigma_3year(s):
    """3-year window"""
    return s.shift(1).rolling(3, min_periods=2).std()

jpm['sigma_2year'] = rolling_sigma_2year(jpm['rit'])
jpm['sigma_3year'] = rolling_sigma_3year(jpm['rit'])

print("\n" + "="*80)
print("JPM VOLATILITY COMPARISON: 2-year vs 3-year windows")
print("="*80)
print(jpm[['year', 'rit', 'sigma_2year', 'sigma_3year']].to_string())

# Calculate DD_a for both
print("\n" + "="*80)
print("IMPACT ON DD_a FOR 2018")
print("="*80)

jpm_2018 = jpm[jpm['year'] == 2018].iloc[0]
print(f"\n2018 Return (rit): {jpm_2018['rit']:.6f}")
print(f"2-year volatility: {jpm_2018['sigma_2year']:.6f}")
print(f"3-year volatility: {jpm_2018['sigma_3year']:.6f}")
print(f"Difference: {((jpm_2018['sigma_2year'] - jpm_2018['sigma_3year']) / jpm_2018['sigma_3year'] * 100):.1f}%")

# Show for all banks in 2018
print("\n" + "="*80)
print("ALL BANKS 2018: Volatility Comparison")
print("="*80)

df_2018 = df[df['year'] == 2018].copy()
df_2018['sigma_2year'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_2year)
df_2018['sigma_3year'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_3year)

comparison = df_2018[['instrument', 'sigma_2year', 'sigma_3year']].copy()
comparison['diff_pct'] = ((comparison['sigma_2year'] - comparison['sigma_3year']) / comparison['sigma_3year'] * 100)
comparison = comparison.dropna()
comparison = comparison.sort_values('diff_pct', ascending=False)

print(comparison.head(20).to_string())

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"2018 banks with data: {len(comparison)}")
print(f"Average difference: {comparison['diff_pct'].mean():.2f}%")
print(f"Median difference: {comparison['diff_pct'].median():.2f}%")
print(f"2-year > 3-year: {(comparison['diff_pct'] > 0).sum()} banks")
print(f"2-year < 3-year: {(comparison['diff_pct'] < 0).sum()} banks")

print("\nKEY INSIGHT:")
if comparison['diff_pct'].mean() > 0:
    print("✓ 2-year window produces HIGHER volatility on average")
    print("  → Should result in LOWER DD values (not higher!)")
else:
    print("✓ 2-year window produces LOWER volatility on average") 
    print("  → Should result in HIGHER DD values")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("If 2-year volatility is similar to or higher than 3-year,")
print("then the 2018 anomaly is NOT caused by window size.")
print("The issue must be elsewhere (data quality, calculation method, etc.)")
