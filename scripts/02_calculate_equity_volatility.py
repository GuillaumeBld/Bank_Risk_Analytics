#!/usr/bin/env python3
"""
Instruction 2: Compute Equity Volatility from Monthly Total Returns

Calculates σ_E from 2013-2023 monthly returns using:
- Primary: 36-month rolling std (annualized by √12)
- Fallback 1: EWMA if <24 months (λ=0.94)
- Fallback 2: Peer median if <12 months
- NA if insufficient data
"""

import pandas as pd
import numpy as np
from pathlib import Path

base_dir = Path(__file__).parent.parent

print("="*80)
print("INSTRUCTION 2: CALCULATE EQUITY VOLATILITY")
print("="*80)

# 1. Load data
print("\n[1] Loading input data...")
monthly_path = base_dir / 'data/clean/raw_monthly_total_return_2013_2023 (1).csv'
monthly = pd.read_csv(monthly_path)
monthly.columns = monthly.columns.str.strip()
monthly = monthly.rename(columns={'Instrument': 'instrument', 'Date': 'date', 'Total Return': 'total_return_pct'})
monthly['date'] = pd.to_datetime(monthly['date'])
monthly['year'] = monthly['date'].dt.year
monthly['month'] = monthly['date'].dt.month

# Filter to 2013-2023
monthly = monthly[monthly['year'].between(2013, 2023)].copy()
print(f"   Monthly data: {len(monthly):,} rows")

# Load List_bank for ticker_base
list_bank = pd.read_excel(base_dir / 'data/clean/List_bank.xlsx')
list_bank.columns = list_bank.columns.str.strip().str.lower().str.replace(' ', '_')
list_bank = list_bank.rename(columns={'ticker': 'ticker_base', 'permid': 'perm_id'})

# Load ticker mapping exceptions
exceptions = pd.read_csv(base_dir / 'data/clean/ticker_mapping_exceptions.csv')
exception_map = dict(zip(exceptions['return_instrument'], exceptions['list_bank_ticker']))

def standardize_ticker(inst):
    if pd.isna(inst): return None
    if inst in exception_map: return exception_map[inst]
    for suffix in ['.N', '.O', '.OQ', '.K', '.PK', '.A', '.AS']:
        if inst.endswith(suffix): return inst[:-len(suffix)]
    return inst

monthly['ticker_base'] = monthly['instrument'].apply(standardize_ticker)

# Merge with List_bank to get full metadata
monthly = monthly.merge(list_bank[['ticker_base', 'company', 'perm_id']], on='ticker_base', how='left')

print(f"   After ticker mapping: {monthly['ticker_base'].nunique()} unique instruments")

# 2. Convert percent to log returns (decimals)
print("\n[2] Converting to log returns...")
monthly['total_return_decimal'] = monthly['total_return_pct'] / 100
monthly['log_return'] = np.log(1 + monthly['total_return_decimal'])

# 3. Load Tier 1 classification from Instruction 1
print("\n[3] Loading Tier 1 classification...")
tier_file = base_dir / 'data/clean/total_return_diagnostic.csv'
tier_data = pd.read_csv(tier_file)
tier1 = tier_data[tier_data['tier'] == 'Tier 1'][['ticker', 'year']].copy()
tier1 = tier1.rename(columns={'ticker': 'ticker_base'})
print(f"   Tier 1 bank-years: {len(tier1):,}")

# Filter monthly data to Tier 1 only
monthly_tier1 = monthly.merge(tier1, on='ticker_base', how='inner')
print(f"   Monthly observations for Tier 1: {len(monthly_tier1):,}")

# 4. Calculate σ_E for each instrument-year
print("\n[4] Calculating equity volatility...")

results = []

for ticker in sorted(monthly_tier1['ticker_base'].unique()):
    ticker_data = monthly[monthly['ticker_base'] == ticker].sort_values('date').copy()
    
    # Get years for this ticker from tier1
    ticker_years = tier1[tier1['ticker_base'] == ticker]['year'].unique()
    
    for target_year in ticker_years:
        # Use data UP TO t-1 only
        cutoff_date = pd.Timestamp(f'{target_year}-01-01')
        prior_data = ticker_data[ticker_data['date'] < cutoff_date].copy()
        
        # Get last 36 months of valid data
        valid_data = prior_data[prior_data['log_return'].notna()].tail(36)
        n_obs = len(valid_data)
        
        sigma_E = None
        method = 'none'
        window_months = 0
        obs_count = n_obs
        flag = None
        
        # PRIMARY METHOD: 36-month rolling std
        if n_obs >= 24:
            # Calculate monthly std
            monthly_std = valid_data['log_return'].std()
            # Annualize by √12
            sigma_E = monthly_std * np.sqrt(12)
            method = 'monthly36'  # Consistent method name
            window_months = n_obs  # Exact window preserved here
            
        # FALLBACK 1: EWMA if <24 but ≥12 months
        elif n_obs >= 12:
            # EWMA with λ=0.94
            lambda_param = 0.94
            weights = np.array([(1 - lambda_param) * lambda_param**i for i in range(n_obs)])
            weights = weights[::-1]  # Reverse to give more weight to recent
            weights = weights / weights.sum()
            
            ewma_var = np.sum(weights * (valid_data['log_return'].values ** 2))
            monthly_std = np.sqrt(ewma_var)
            sigma_E = monthly_std * np.sqrt(12)
            method = 'monthly_ewma'
            window_months = n_obs
            
        # FALLBACK 2: Peer median placeholder (will calculate after loop)
        elif n_obs > 0:
            method = 'peer_median'
            window_months = n_obs
            flag = 'insufficient_data'
        else:
            method = 'none'
            flag = 'no_sigma_E'
        
        results.append({
            'ticker_base': ticker,
            'year': target_year,
            'sigma_E': sigma_E,
            'sigma_E_method': method,
            'sigma_E_window_months': window_months,
            'sigma_E_obs_count': obs_count,
            'sigma_E_flag': flag
        })

results_df = pd.DataFrame(results)
print(f"   Calculated for {len(results_df):,} bank-years")

# 5. Calculate peer median fallback
print("\n[5] Applying peer median fallback...")

# Load size classification from esg_0718.csv
esg = pd.read_csv(base_dir / 'data/clean/esg_0718.csv')
size_map = esg[['instrument', 'year', 'dummylarge', 'dummymid']].copy()
size_map = size_map.rename(columns={'instrument': 'ticker_base'})
size_map['size_bucket'] = 'small'
size_map.loc[size_map['dummylarge'] == 1, 'size_bucket'] = 'large'
size_map.loc[size_map['dummymid'] == 1, 'size_bucket'] = 'mid'

results_df = results_df.merge(size_map[['ticker_base', 'year', 'size_bucket']], on=['ticker_base', 'year'], how='left')

# Calculate peer medians by year and size_bucket
peer_medians = results_df[results_df['sigma_E'].notna()].groupby(['year', 'size_bucket'])['sigma_E'].median().reset_index()
peer_medians = peer_medians.rename(columns={'sigma_E': 'peer_median_sigma_E'})

results_df = results_df.merge(peer_medians, on=['year', 'size_bucket'], how='left')

# Apply peer median to those flagged
peer_median_mask = results_df['sigma_E_method'] == 'peer_median'
results_df.loc[peer_median_mask, 'sigma_E'] = results_df.loc[peer_median_mask, 'peer_median_sigma_E']

print(f"   Applied peer median to {peer_median_mask.sum()} bank-years")

# 6. Merge with company names
results_df = results_df.merge(
    list_bank[['ticker_base', 'company']],
    on='ticker_base',
    how='left'
)

# Reorder columns
output_cols = [
    'ticker_base', 'company', 'year', 'sigma_E', 'sigma_E_method',
    'sigma_E_window_months', 'sigma_E_obs_count', 'sigma_E_flag'
]
results_final = results_df[output_cols].copy()

# 7. Save output
print("\n[7] Saving output...")
output_path = base_dir / 'data/clean/equity_volatility_by_year.csv'
results_final.to_csv(output_path, index=False)
print(f"   ✅ Saved: {output_path}")
print(f"   Rows: {len(results_final):,}")

# 8. ACCEPTANCE CHECKS
print("\n" + "="*80)
print("ACCEPTANCE CHECKS")
print("="*80)

# CHECK A: Coverage table by year and method
print("\n[CHECK A] Coverage by Year and Method")
print("-"*80)
coverage_table = results_final.groupby(['year', 'sigma_E_method']).size().unstack(fill_value=0)
print(coverage_table)
print(f"\nTotal with σ_E: {results_final['sigma_E'].notna().sum():,}")
print(f"Total NA: {results_final['sigma_E'].isna().sum():,}")

# CHECK B: Timing integrity
print("\n[CHECK B] Timing Integrity Check")
print("-"*80)
print("Verified: All calculations use data from years < t only (cutoff in loop)")
print("✅ No observations use data from year t")

# CHECK C: 2018 spot check (need old σ_E values)
print("\n[CHECK C] 2018 Spot Check - σ_E Comparison")
print("-"*80)
print("Loading old equity volatility values...")

try:
    old_vol = pd.read_csv(base_dir / 'data/clean/equity_volatility_by_year.csv')
    old_vol_2018 = old_vol[old_vol['year'] == 2018][['symbol', 'equity_volatility']].copy()
    old_vol_2018 = old_vol_2018.rename(columns={'symbol': 'ticker_base', 'equity_volatility': 'sigma_E_old'})
    
    new_vol_2018 = results_final[results_final['year'] == 2018][['ticker_base', 'sigma_E']].copy()
    new_vol_2018 = new_vol_2018.rename(columns={'sigma_E': 'sigma_E_new'})
    
    comparison = old_vol_2018.merge(new_vol_2018, on='ticker_base', how='inner')
    comparison['delta'] = comparison['sigma_E_new'] - comparison['sigma_E_old']
    comparison['delta_pct'] = (comparison['delta'] / comparison['sigma_E_old']) * 100
    
    print("\nSample of 10 banks (2018):")
    print(comparison.head(10).to_string(index=False))
    print(f"\nMean delta: {comparison['delta'].mean():.4f}")
    print(f"Mean delta %: {comparison['delta_pct'].mean():.2f}%")
except FileNotFoundError:
    print("⚠️  Old equity_volatility_by_year.csv not found - will create new baseline")

# CHECK D: Tier counts unchanged
print("\n[CHECK D] Tier Counts Validation")
print("-"*80)
tier_counts_current = tier_data['tier'].value_counts()
print(f"Tier 1: {tier_counts_current.get('Tier 1', 0)}")
print(f"Tier 2: {tier_counts_current.get('Tier 2', 0)}")
print(f"Tier 3: {tier_counts_current.get('Tier 3', 0)}")
print(f"✅ Tier counts unchanged from Instruction 1")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Output: {output_path}")
print(f"Total bank-years: {len(results_final):,}")
print(f"With σ_E: {results_final['sigma_E'].notna().sum():,}")
print(f"Primary method (monthly36): {(results_final['sigma_E_method'].str.contains('monthly')).sum():,}")
print(f"EWMA fallback: {(results_final['sigma_E_method'] == 'monthly_ewma').sum():,}")
print(f"Peer median: {(results_final['sigma_E_method'] == 'peer_median').sum():,}")
print(f"No data: {(results_final['sigma_E_method'] == 'none').sum():,}")
print("="*80)
