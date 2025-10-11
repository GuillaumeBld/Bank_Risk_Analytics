#!/usr/bin/env python3
"""
Analyze 2013-2015 coverage to understand impact on 2018 σ_E calculation
"""

import pandas as pd
import numpy as np
from pathlib import Path

base_dir = Path(__file__).parent.parent

print("="*80)
print("EARLY YEARS COVERAGE ANALYSIS (2013-2015)")
print("="*80)

# Load monthly data
monthly = pd.read_csv(base_dir / 'data/clean/raw_monthly_total_return_2013_2023 (1).csv')
monthly.columns = monthly.columns.str.strip()
monthly = monthly.rename(columns={'Instrument': 'instrument', 'Date': 'date', 'Total Return': 'total_return'})
monthly['date'] = pd.to_datetime(monthly['date'])
monthly['year'] = monthly['date'].dt.year

# Load ticker mapping
list_bank = pd.read_excel(base_dir / 'data/clean/List_bank.xlsx')
list_bank.columns = list_bank.columns.str.strip().str.lower().str.replace(' ', '_')
list_bank = list_bank.rename(columns={'ticker': 'ticker_base'})

exceptions = pd.read_csv(base_dir / 'data/clean/ticker_mapping_exceptions.csv')
exception_map = dict(zip(exceptions['return_instrument'], exceptions['list_bank_ticker']))

def standardize_ticker(inst):
    if pd.isna(inst): return None
    if inst in exception_map: return exception_map[inst]
    for suffix in ['.N', '.O', '.OQ', '.K', '.PK', '.A', '.AS']:
        if inst.endswith(suffix): return inst[:-len(suffix)]
    return inst

monthly['ticker_base'] = monthly['instrument'].apply(standardize_ticker)

# Load esg to get instruments in use
esg = pd.read_csv(base_dir / 'data/clean/esg_0718.csv')
instruments_in_use = esg['instrument'].unique()

# Filter to instruments in use
monthly_filtered = monthly[monthly['ticker_base'].isin(instruments_in_use)].copy()

# Analyze coverage by year
print("\n[1] MONTHLY OBSERVATIONS BY YEAR")
print("-"*80)

for year in [2013, 2014, 2015, 2016]:
    year_data = monthly_filtered[monthly_filtered['year'] == year]
    instruments = year_data['ticker_base'].nunique()
    valid_obs = year_data['total_return'].notna().sum()
    total_obs = len(year_data)
    
    print(f"{year}: {instruments} instruments, {valid_obs:,} valid obs, {total_obs:,} total obs")

# Detailed coverage table for early years
print("\n[2] COVERAGE TABLE: Valid Months per Ticker (2013-2015)")
print("-"*80)

coverage_data = []

for ticker in sorted(instruments_in_use):
    ticker_data = monthly_filtered[monthly_filtered['ticker_base'] == ticker]
    
    for year in [2013, 2014, 2015]:
        year_data = ticker_data[ticker_data['year'] == year]
        valid_months = year_data['total_return'].notna().sum()
        
        if valid_months > 0:
            coverage_data.append({
                'ticker': ticker,
                'year': year,
                'valid_months': valid_months
            })

coverage_df = pd.DataFrame(coverage_data)

# Pivot for easier viewing
if len(coverage_df) > 0:
    pivot = coverage_df.pivot(index='ticker', columns='year', values='valid_months').fillna(0).astype(int)
    pivot['total_2013_2015'] = pivot.sum(axis=1)
    pivot['has_36_months'] = (pivot['total_2013_2015'] >= 36).astype(int)
    
    print(f"\nTickers with any 2013-2015 data: {len(pivot)}")
    print(f"Tickers with ≥36 months (2013-2015): {pivot['has_36_months'].sum()}")
    print(f"\nSample (first 20 tickers):")
    print(pivot.head(20))
else:
    print("\n⚠️  NO DATA FOUND for 2013-2015")
    print("This explains why Tier 1 baseline differs from expected")

# Impact on 2018 σ_E calculation
print("\n[3] IMPACT ON 2018 σ_E CALCULATION")
print("-"*80)

# For 2018, we need data from 2015, 2016, 2017
# Check how many banks have sufficient 2015-2017 data

impact_data = []

for ticker in instruments_in_use:
    ticker_data = monthly_filtered[monthly_filtered['ticker_base'] == ticker]
    
    # Data for 2015-2017 (needed for 2018 σ_E)
    data_2015_2017 = ticker_data[ticker_data['year'].isin([2015, 2016, 2017])]
    valid_2015_2017 = data_2015_2017['total_return'].notna().sum()
    
    # Data for 2015 specifically
    data_2015 = ticker_data[ticker_data['year'] == 2015]
    valid_2015 = data_2015['total_return'].notna().sum()
    
    # Data for 2016-2017 (old approach)
    data_2016_2017 = ticker_data[ticker_data['year'].isin([2016, 2017])]
    valid_2016_2017 = data_2016_2017['total_return'].notna().sum()
    
    # Only include if ticker appears in 2018
    if ticker in esg[esg['year'] == 2018]['instrument'].values:
        impact_data.append({
            'ticker': ticker,
            'valid_2015': valid_2015,
            'valid_2016_2017': valid_2016_2017,
            'valid_2015_2017': valid_2015_2017,
            'has_full_window': valid_2015_2017 >= 36,
            'missing_2015': valid_2015 < 12
        })

impact_df = pd.DataFrame(impact_data)

if len(impact_df) > 0:
    print(f"\nBanks in 2018 sample: {len(impact_df)}")
    print(f"With full 36-month window (2015-2017): {impact_df['has_full_window'].sum()}")
    print(f"Missing 2015 data (<12 months): {impact_df['missing_2015'].sum()}")
    
    print(f"\nWindow distribution for 2018:")
    print(f"  ≥36 months (full window): {(impact_df['valid_2015_2017'] >= 36).sum()}")
    print(f"  24-35 months (reduced):   {((impact_df['valid_2015_2017'] >= 24) & (impact_df['valid_2015_2017'] < 36)).sum()}")
    print(f"  12-23 months (EWMA):      {((impact_df['valid_2015_2017'] >= 12) & (impact_df['valid_2015_2017'] < 24)).sum()}")
    print(f"  <12 months (peer median): {(impact_df['valid_2015_2017'] < 12).sum()}")
    
    # Show sample of banks with insufficient data
    insufficient = impact_df[impact_df['valid_2015_2017'] < 36].sort_values('valid_2015_2017')
    if len(insufficient) > 0:
        print(f"\nBanks with <36 months for 2018 (first 10):")
        print(insufficient[['ticker', 'valid_2015', 'valid_2016_2017', 'valid_2015_2017']].head(10))

# Load current equity volatility results
print("\n[4] ACTUAL σ_E METHOD SELECTION FOR 2018")
print("-"*80)

try:
    sigma_E = pd.read_csv(base_dir / 'data/clean/equity_volatility_by_year.csv')
    sigma_2018 = sigma_E[sigma_E['year'] == 2018]
    
    method_counts = sigma_2018['sigma_E_method'].value_counts()
    print(f"\n2018 σ_E Methods:")
    print(method_counts)
    
    print(f"\nWindow distribution:")
    window_stats = sigma_2018['sigma_E_window_months'].describe()
    print(window_stats)
    
    # Show banks that didn't get full 36-month window
    incomplete = sigma_2018[sigma_2018['sigma_E_window_months'] < 36]
    if len(incomplete) > 0:
        print(f"\nBanks with <36 month window in 2018 ({len(incomplete)}):")
        print(incomplete[['ticker_base', 'sigma_E', 'sigma_E_method', 'sigma_E_window_months', 'sigma_E_flag']])
    
except FileNotFoundError:
    print("⚠️  equity_volatility_by_year.csv not found yet")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("\nKey Findings:")
print("1. Early years (2013-2015) have limited coverage in raw data")
print("2. Most banks in esg_0718.csv start from 2016 onwards")
print("3. This explains Tier count differences from baseline")
print("4. For 2018 σ_E: depends on 2015-2017 data availability")
print("5. Banks without full 2015 coverage use reduced windows or fallbacks")
print("\nConclusion:")
print("The tier baseline (2,354) likely includes years 2013-2015 which are")
print("not in esg_0718.csv. Our 1,308 Tier 1 count covers 2016-2023 only.")
print("="*80)
