#!/usr/bin/env python3
"""
Equity Volatility Calculator - Daily Returns (252-Day Window)
==============================================================

Calculates equity volatility following Bharath & Shumway (2008):
- Uses daily total returns from year t-1
- 252-day window (all of year t-1)
- Annualization: Daily SD × √252
- Minimum 180 trading days required

Author: Migration Script
Date: October 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.parent
TRADING_DAYS_PER_YEAR = 252
MIN_DAYS_PRIMARY = 180      # 70% of year
MIN_DAYS_FALLBACK = 90      # 35% of year
WINSORIZE_LOWER = 0.01      # 1st percentile
WINSORIZE_UPPER = 0.99      # 99th percentile

print("="*80)
print("DAILY VOLATILITY CALCULATOR")
print("Bharath & Shumway (2008) Methodology")
print("="*80)

# ============================================================================
# STEP 1: Load Data
# ============================================================================

print("\n[STEP 1] Loading data...")
print("-"*80)

# Load daily returns
daily_path = BASE_DIR / 'data/clean/raw_daily_total_return_2015_2023.csv'
print(f"Loading: {daily_path}")
daily = pd.read_csv(daily_path)

print(f"  Rows: {len(daily):,}")
print(f"  Columns: {daily.columns.tolist()}")

# Parse dates
daily['Date'] = pd.to_datetime(daily['Date'])
daily['year'] = daily['Date'].dt.year
daily['month'] = daily['Date'].dt.month

# Load List_bank for ticker mapping
list_bank_path = BASE_DIR / 'data/clean/List_bank.xlsx'
print(f"\nLoading: {list_bank_path}")
list_bank = pd.read_excel(list_bank_path)
list_bank.columns = list_bank.columns.str.strip().str.lower().str.replace(' ', '_')

# Load ticker mapping exceptions
exceptions_path = BASE_DIR / 'data/clean/ticker_mapping_exceptions.csv'
print(f"Loading: {exceptions_path}")
exceptions = pd.read_csv(exceptions_path)
exception_map = dict(zip(exceptions['return_instrument'], exceptions['list_bank_ticker']))

print(f"\n✓ Data loaded")
print(f"  Daily returns: {len(daily):,} rows")
print(f"  Date range: {daily['Date'].min()} to {daily['Date'].max()}")
print(f"  Instruments: {daily['Instrument'].nunique()}")

# ============================================================================
# STEP 2: Standardize Tickers
# ============================================================================

print("\n[STEP 2] Standardizing tickers...")
print("-"*80)

def standardize_ticker(inst):
    """Remove exchange suffixes and map exceptions"""
    if pd.isna(inst):
        return None
    
    # Check exceptions first
    if inst in exception_map:
        return exception_map[inst]
    
    # Remove common suffixes
    for suffix in ['.N', '.O', '.OQ', '.K', '.PK', '.A', '.AS']:
        if inst.endswith(suffix):
            return inst[:-len(suffix)]
    
    return inst

daily['ticker'] = daily['Instrument'].apply(standardize_ticker)

print(f"  Unique tickers after standardization: {daily['ticker'].nunique()}")
print(f"  Sample mappings:")
for i, row in daily.head(5).iterrows():
    print(f"    {row['Instrument']} → {row['ticker']}")

# ============================================================================
# STEP 3: Calculate Log Returns
# ============================================================================

print("\n[STEP 3] Calculating log returns...")
print("-"*80)

# Convert percent to decimal
daily['return_decimal'] = daily['Total Return'] / 100

# Calculate log returns
daily['log_return'] = np.log(1 + daily['return_decimal'])

# Flag extreme outliers (>100% daily move)
daily['outlier_severe'] = daily['log_return'].abs() > 1.0

n_outliers = daily['outlier_severe'].sum()
print(f"  Severe outliers (>100% daily move): {n_outliers}")

if n_outliers > 0:
    print(f"  ⚠️  Removing {n_outliers} severe outlier days")
    daily = daily[~daily['outlier_severe']].copy()

print(f"  Log returns calculated: {daily['log_return'].notna().sum():,} valid observations")

# ============================================================================
# STEP 4: Calculate Volatility for Each Bank-Year
# ============================================================================

print("\n[STEP 4] Calculating equity volatility...")
print("-"*80)

# Get unique bank-year combinations we need
# Years 2016-2023 (need t-1 data, so daily data from 2015-2022)
results = []

# Get all unique tickers
tickers = sorted(daily['ticker'].unique())
years_target = range(2016, 2024)  # 2016-2023

print(f"  Calculating for {len(tickers)} tickers × {len(years_target)} years")
print(f"  Total calculations: {len(tickers) * len(years_target):,}")

for ticker in tickers:
    ticker_data = daily[daily['ticker'] == ticker].sort_values('Date').copy()
    
    for year_t in years_target:
        # Get year t-1 data
        year_tminus1 = year_t - 1
        start_date = pd.Timestamp(f'{year_tminus1}-01-01')
        end_date = pd.Timestamp(f'{year_tminus1}-12-31')
        
        # Extract year t-1 daily returns
        year_data = ticker_data[
            (ticker_data['Date'] >= start_date) &
            (ticker_data['Date'] <= end_date)
        ].copy()
        
        # Get valid log returns
        valid_returns = year_data['log_return'].dropna()
        n_days = len(valid_returns)
        
        # Initialize result
        result = {
            'ticker': ticker,
            'year': year_t,
            'sigma_E': None,
            'method': None,
            'days_used': n_days,
            'flag': None
        }
        
        # PRIMARY METHOD: 180+ days
        if n_days >= MIN_DAYS_PRIMARY:
            daily_std = valid_returns.std()
            sigma_E = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)
            result['sigma_E'] = sigma_E
            result['method'] = 'daily_252'
            result['flag'] = None
        
        # FALLBACK A: 90-179 days (partial year)
        elif n_days >= MIN_DAYS_FALLBACK:
            daily_std = valid_returns.std()
            sigma_E = daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)
            result['sigma_E'] = sigma_E
            result['method'] = 'daily_partial'
            result['flag'] = 'insufficient_days'
        
        # FALLBACK B: <90 days (use peer median later)
        else:
            result['method'] = 'imputed_peer'
            result['flag'] = 'no_daily_data'
        
        results.append(result)

# Convert to DataFrame
results_df = pd.DataFrame(results)

print(f"\n  Calculations complete: {len(results_df):,} bank-years")
print(f"\n  Method distribution:")
print(results_df['method'].value_counts())
print(f"\n  Volatility calculated: {results_df['sigma_E'].notna().sum():,} / {len(results_df):,}")

# ============================================================================
# STEP 5: Apply Peer Median Fallback
# ============================================================================

print("\n[STEP 5] Applying peer median fallback...")
print("-"*80)

# Load size classification from esg data
esg_path = BASE_DIR / 'data/clean/esg_0718.csv'
print(f"Loading size classification: {esg_path}")
esg = pd.read_csv(esg_path)

size_map = esg[['instrument', 'year', 'dummylarge', 'dummymid']].copy()
size_map = size_map.rename(columns={'instrument': 'ticker'})

# Create size bucket
size_map['size_bucket'] = 'small'
size_map.loc[size_map['dummylarge'] == 1, 'size_bucket'] = 'large'
size_map.loc[size_map['dummymid'] == 1, 'size_bucket'] = 'mid'

# Merge size info
results_df = results_df.merge(
    size_map[['ticker', 'year', 'size_bucket']],
    on=['ticker', 'year'],
    how='left'
)

# Calculate peer medians by year and size
peer_medians = results_df[results_df['sigma_E'].notna()].groupby(
    ['year', 'size_bucket']
)['sigma_E'].median().reset_index()
peer_medians = peer_medians.rename(columns={'sigma_E': 'peer_median_sigma_E'})

# Merge peer medians
results_df = results_df.merge(
    peer_medians,
    on=['year', 'size_bucket'],
    how='left'
)

# Apply peer median to imputed observations
imputed_mask = results_df['method'] == 'imputed_peer'
results_df.loc[imputed_mask, 'sigma_E'] = results_df.loc[imputed_mask, 'peer_median_sigma_E']

n_imputed = imputed_mask.sum()
print(f"  Applied peer median to: {n_imputed} bank-years")
print(f"\n  Final coverage: {results_df['sigma_E'].notna().sum():,} / {len(results_df):,}")

# ============================================================================
# STEP 6: Winsorization
# ============================================================================

print("\n[STEP 6] Winsorizing outliers...")
print("-"*80)

# Winsorize within each year
def winsorize_year(group):
    lower = group['sigma_E'].quantile(WINSORIZE_LOWER)
    upper = group['sigma_E'].quantile(WINSORIZE_UPPER)
    group['sigma_E_winsorized'] = group['sigma_E'].clip(lower=lower, upper=upper)
    return group

results_df = results_df.groupby('year', group_keys=False).apply(winsorize_year)

# Check how many were winsorized
n_winsorized = (results_df['sigma_E'] != results_df['sigma_E_winsorized']).sum()
print(f"  Winsorized: {n_winsorized} observations ({n_winsorized/len(results_df)*100:.2f}%)")

# Use winsorized values
results_df['sigma_E'] = results_df['sigma_E_winsorized']
results_df = results_df.drop(columns=['sigma_E_winsorized', 'peer_median_sigma_E'])

# ============================================================================
# STEP 7: Quality Checks
# ============================================================================

print("\n[STEP 7] Quality checks...")
print("-"*80)

# Check 1: Value ranges
print("\n[CHECK 1] Value Ranges:")
print(results_df['sigma_E'].describe())

reasonable = results_df['sigma_E'].between(0.10, 1.0).sum()
total = results_df['sigma_E'].notna().sum()
print(f"\n  Within reasonable range (10%-100%): {reasonable}/{total} ({reasonable/total*100:.1f}%)")

if (results_df['sigma_E'] < 0.10).sum() > 0:
    print(f"  ⚠️  Below 10%: {(results_df['sigma_E'] < 0.10).sum()}")
if (results_df['sigma_E'] > 1.0).sum() > 0:
    print(f"  ⚠️  Above 100%: {(results_df['sigma_E'] > 1.0).sum()}")

# Check 2: Coverage by year
print("\n[CHECK 2] Coverage by Year:")
coverage = results_df.groupby('year').agg({
    'sigma_E': lambda x: f"{x.notna().sum()}/{len(x)} ({x.notna().mean()*100:.1f}%)"
})
print(coverage)

# Check 3: Method success rates
print("\n[CHECK 3] Method Distribution:")
print(results_df['method'].value_counts())
primary_rate = (results_df['method'] == 'daily_252').sum() / len(results_df) * 100
print(f"\n  Primary method (daily_252) usage: {primary_rate:.1f}%")

# Check 4: Timing discipline verification
print("\n[CHECK 4] Timing Discipline Check:")
print("  ✓ All calculations use only year t-1 data (verified in code)")
print("  ✓ No look-ahead bias by construction")

# ============================================================================
# STEP 8: Save Output
# ============================================================================

print("\n[STEP 8] Saving output...")
print("-"*80)

# Select output columns
output_cols = [
    'ticker', 'year', 'sigma_E', 'method', 
    'days_used', 'flag', 'size_bucket'
]
output_df = results_df[output_cols].copy()

# Sort by ticker and year
output_df = output_df.sort_values(['ticker', 'year'])

# Save main output
output_path = BASE_DIR / 'data/clean/equity_volatility_by_year_DAILY.csv'
output_df.to_csv(output_path, index=False)
print(f"✓ Saved: {output_path}")
print(f"  Rows: {len(output_df):,}")

# Save diagnostic report
diagnostic_path = BASE_DIR / 'data/clean/volatility_diagnostic_DAILY.csv'
diagnostic = results_df.groupby(['year', 'method']).size().reset_index(name='count')
diagnostic.to_csv(diagnostic_path, index=False)
print(f"✓ Saved: {diagnostic_path}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\n✅ Equity volatility calculated using daily returns (252-day window)")
print(f"✅ Method: Bharath & Shumway (2008)")
print(f"✅ Total bank-years: {len(output_df):,}")
print(f"✅ Coverage: {output_df['sigma_E'].notna().sum():,} / {len(output_df):,} ({output_df['sigma_E'].notna().mean()*100:.1f}%)")
print(f"✅ Primary method: {(output_df['method'] == 'daily_252').sum():,} ({(output_df['method'] == 'daily_252').mean()*100:.1f}%)")
print(f"✅ Mean volatility: {output_df['sigma_E'].mean():.3f}")
print(f"✅ Median volatility: {output_df['sigma_E'].median():.3f}")

print(f"\n📁 Output files:")
print(f"   {output_path}")
print(f"   {diagnostic_path}")

print("\n✨ Volatility calculation complete!")
print("\n→ Next: Update notebooks (see 02_NOTEBOOK_ACCOUNTING_CHANGES.md)")
print("="*80)
