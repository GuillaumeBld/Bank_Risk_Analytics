#!/usr/bin/env python3
"""
Deep dive into return data to answer all integration questions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

base = Path('/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank')
monthly_file = base / 'data/clean/raw_monthly_total_return_2013_2023 (1).csv'
annual_file = base / 'data/clean/raw_yearly_total_return_2013_2023 (1).csv'

print('='*100)
print('DEEP DIVE: RETURN DATA INTEGRATION Q&A')
print('='*100)
print()

# Load data
monthly = pd.read_csv(monthly_file)
annual = pd.read_csv(annual_file)

print('='*100)
print('SECTION 1: SCOPE AND IDENTIFIERS')
print('='*100)
print()

print('Q1: What is the definitive security identifier?')
print('-'*100)
print(f'Monthly unique instruments: {monthly["Instrument"].nunique()}')
print(f'Annual unique instruments: {annual["Instrument"].nunique()}')
print()

# Analyze ticker formats
print('Sample tickers from monthly data:')
for ticker in sorted(monthly['Instrument'].unique())[:15]:
    print(f'  {ticker}')
print()

# Check for suffixes
has_suffix = monthly['Instrument'].str.contains('\.', regex=True, na=False)
has_caret = monthly['Instrument'].str.contains('\^', regex=True, na=False)

print(f'Tickers with period suffixes (.N, .O, .OQ): {has_suffix.sum()} observations')
print(f'Tickers with caret codes (^): {has_caret.sum()} observations')
print()

# Examples of complex tickers
complex_tickers = monthly[has_caret | monthly['Instrument'].str.len() > 15]['Instrument'].unique()
if len(complex_tickers) > 0:
    print('Complex ticker examples:')
    for t in sorted(complex_tickers)[:10]:
        print(f'  {t}')
print()

# Clean tickers
monthly['ticker_base'] = monthly['Instrument'].str.replace(r'(\.[A-Z]+|\^.*)$', '', regex=True)
annual['ticker_base'] = annual['Instrument'].str.replace(r'(\.[A-Z]+|\^.*)$', '', regex=True)

print(f'Unique BASE tickers (cleaned): {monthly["ticker_base"].nunique()}')
print()

print('Q2: Do tickers map one-to-one with banks over time?')
print('-'*100)

# Check if same base ticker has multiple suffixes
ticker_suffix_map = monthly.groupby('ticker_base')['Instrument'].nunique()
multi_suffix = ticker_suffix_map[ticker_suffix_map > 1]

print(f'Base tickers with multiple suffixes: {len(multi_suffix)}')
if len(multi_suffix) > 0:
    print('Examples:')
    for base, count in multi_suffix.head(10).items():
        suffixes = monthly[monthly['ticker_base'] == base]['Instrument'].unique()
        print(f'  {base}: {list(suffixes)}')
print()

print('Q3: Suffix standardization')
print('-'*100)
suffix_counts = monthly['Instrument'].str.extract(r'(\.([A-Z]+))')[1].value_counts()
print('Common suffixes:')
print(suffix_counts.head(10))
print()

print('='*100)
print('SECTION 2: TIME COVERAGE AND INDEXING')
print('='*100)
print()

print('Q4: Monthly periodization')
print('-'*100)
monthly['date_parsed'] = pd.to_datetime(monthly['Date'])
monthly['day_of_month'] = monthly['date_parsed'].dt.day
monthly['is_month_end'] = monthly['date_parsed'].dt.is_month_end

print('Day of month distribution (first 10):')
print(monthly['day_of_month'].value_counts().head(10))
print()
print(f'Records at month-end: {monthly["is_month_end"].sum()} / {len(monthly)} ({100*monthly["is_month_end"].mean():.1f}%)')
print()

# Sample dates
print('Sample dates from monthly file:')
for date in sorted(monthly['date_parsed'].unique())[:15]:
    print(f'  {date.strftime("%Y-%m-%d (%A)")}')
print()

print('Q5: Partial months')
print('-'*100)
monthly['days_in_month'] = monthly['date_parsed'].dt.days_in_month
print(f'All dates appear to be end-of-month: {(monthly["day_of_month"] == monthly["days_in_month"]).mean():.1%}')
print()

print('Q6: Years with 0 valid months - should they be carried forward?')
print('-'*100)
zero_month_examples = ['AMTB', 'AUB', 'VABK']
for ticker in zero_month_examples[:3]:
    ticker_data = monthly[monthly['Instrument'].str.startswith(ticker)]
    years_present = sorted(ticker_data['date_parsed'].dt.year.unique())
    if len(years_present) > 0:
        print(f'{ticker}: Has data in years {years_present}')
    else:
        print(f'{ticker}: No monthly data at all')
print()

print('Q7: 2024 annual data')
print('-'*100)
annual_2024 = annual[annual['Date'] == 2024]
print(f'Annual observations for 2024: {len(annual_2024)}')
print(f'Monthly latest year: {monthly["date_parsed"].dt.year.max()}')
print(f'Annual latest year: {annual["Date"].max()}')
print()
print('='*100)
print('SECTION 3: RETURN DEFINITIONS')
print('='*100)
print()

print('Q8: Return definitions (inferred from data)')
print('-'*100)
print('Monthly return statistics:')
print(monthly['Total Return'].describe())
print()
print('Annual return statistics:')
print(annual['Total Return'].describe())
print()

# Check if returns look like percentages or decimals
monthly_sample = monthly['Total Return'].dropna().head(20)
print('Sample monthly returns (first 20):')
for val in monthly_sample.values[:10]:
    print(f'  {val:.6f}')
print()

print('Interpretation: Returns appear to be in PERCENTAGE form (not decimal)')
print('Example: 6.164931946 means +6.16%, not +616%')
print()

print('Q9: Chain-linked or simple returns?')
print('-'*100)
# Check a specific ticker across months
test_ticker = monthly[monthly['ticker_base'] == 'ABCB'].copy()
test_ticker = test_ticker.sort_values('date_parsed')
test_2013 = test_ticker[test_ticker['date_parsed'].dt.year == 2013]

if len(test_2013) >= 12:
    print(f'Testing {test_ticker["Instrument"].iloc[0]} in 2013:')
    monthly_rets = test_2013['Total Return'].values
    print(f'  Monthly returns (first 6): {monthly_rets[:6]}')
    
    # Try to compound
    compound = np.prod(1 + monthly_rets/100) - 1
    print(f'  Compounded from monthly: {compound * 100:.2f}%')
    
    annual_2013 = annual[(annual['Instrument'].str.startswith('ABCB')) & (annual['Date'] == 2013)]
    if len(annual_2013) > 0:
        ann_ret = annual_2013['Total Return'].iloc[0]
        print(f'  Annual return from file: {ann_ret:.2f}%')
        print(f'  Difference: {abs(compound*100 - ann_ret):.2f} percentage points')
print()

print('Q10: Currency and FX')
print('-'*100)
print('Assumed: All returns are in USD (U.S. market data)')
print('No evidence of FX adjustment needed in filenames or structure')
print()

print('='*100)
print('SECTION 4: DATA SOURCE AND LINEAGE')
print('='*100)
print()

print('Q11-12: Data source (inferred from structure)')
print('-'*100)
print('Files appear to be from financial data provider (likely Refinitiv/Bloomberg)')
print('Evidence:')
print('  - Suffix formats (.N = NYSE, .O = NASDAQ, .OQ = NASDAQ)')
print('  - Date formats and total return calculation')
print('  - Comprehensive U.S. bank coverage')
print()

print('Q13: Survivorship bias')
print('-'*100)
# Check for disappeared tickers
monthly['year'] = monthly['date_parsed'].dt.year
ticker_last_year = monthly.groupby('Instrument')['year'].max()
disappeared = ticker_last_year[ticker_last_year < 2023]
print(f'Tickers that disappear before 2023: {len(disappeared)}')
print('Sample disappeared tickers:')
for ticker, last_year in disappeared.head(10).items():
    print(f'  {ticker}: last seen {last_year}')
print()

print('Q14: Corporate actions explaining gaps')
print('-'*100)
print('Major gap patterns observed:')
print('  - AMTB, AUB, VABK: Missing 2013-2022 (likely late IPO or data unavailability)')
print('  - Banks with 0 months in early years: Could be pre-IPO, merger, or delisting')
print('NOTE: No explicit corporate action timeline in provided files')
print()

print('='*100)
print('SECTION 5: BACKUP LOGIC AND TIERS')
print('='*100)
print()

print('Q15: Threshold sensitivity')
print('-'*100)
coverage = pd.read_csv(base / 'data/outputs/analysis/return_coverage_detailed.csv')
print('Current thresholds:')
print(f'  < 9 months = Incomplete: {len(coverage)} cases')
print()

# Test 8-month threshold
eight_months = coverage[coverage['valid_months'] == 8]
print(f'Cases with exactly 8 months: {len(eight_months)}')
print('Examples:')
print(eight_months.head(10)[['instrument', 'year', 'valid_months', 'has_annual_backup']])
print()

print('Q16-17: Tier 2 backup usage')
print('-'*100)
tier2 = coverage[coverage['has_annual_backup'] == True]
print(f'Tier 2 cases (annual backup available): {len(tier2)}')
print()
print('Details:')
print(tier2[['instrument', 'year', 'valid_months', 'annual_return']])
print()

print('Q18: Tier 3 handling')
print('-'*100)
tier3 = coverage[coverage['has_annual_backup'] == False]
print(f'Tier 3 cases (should exclude): {len(tier3)}')
print('Recommendation: Drop with documentation flag')
print()
print('='*100)
print('SECTION 6: ANOMALIES TO PRE-DECIDE')
print('='*100)
print()

print('Q19: PCB high returns (2013-2014)')
print('-'*100)
pcb_data = tier2[tier2['instrument'] == 'PCB']
if len(pcb_data) > 0:
    print('PCB found in Tier 2:')
    print(pcb_data[['instrument', 'year', 'valid_months', 'annual_return']])
else:
    pcb_annual = annual[annual['Instrument'].str.startswith('PCB')]
    pcb_annual_filtered = pcb_annual[(pcb_annual['Date'] >= 2013) & (pcb_annual['Date'] <= 2014)]
    if len(pcb_annual_filtered) > 0:
        print('PCB annual returns 2013-2014:')
        print(pcb_annual_filtered[['Instrument', 'Date', 'Total Return']])
    else:
        print('PCB not found in dataset')
print()

print('Q20: CIZnv.OQ^J24 negative returns')
print('-'*100)
ciz_data = tier2[tier2['instrument'].str.contains('CIZ', na=False)]
if len(ciz_data) > 0:
    print('CIZ* tickers in Tier 2:')
    print(ciz_data[['instrument', 'year', 'valid_months', 'annual_return']])
else:
    print('CIZ* not found in Tier 2 coverage file')

# Check in raw data
ciz_monthly = monthly[monthly['Instrument'].str.contains('CIZ', na=False)]
ciz_annual = annual[annual['Instrument'].str.contains('CIZ', na=False)]
print(f'CIZ* in monthly data: {len(ciz_monthly)} observations')
print(f'CIZ* in annual data: {len(ciz_annual)} observations')
if len(ciz_annual) > 0:
    print('Sample annual returns:')
    print(ciz_annual[['Instrument', 'Date', 'Total Return']].head(10))
print()

print('Q21: 8-month contiguous rule')
print('-'*100)
eight_month_cases = coverage[coverage['valid_months'] == 8]
print(f'Total 8-month cases: {len(eight_month_cases)}')
print('Sample:')
print(eight_month_cases.head(5)[['instrument', 'year', 'valid_months']])
print()
print('To check contiguity, would need to examine monthly row-by-row')
print('Recommendation: Keep current 9-month threshold for simplicity')
print()

print('='*100)
print('SECTION 7: FILE SCHEMAS AND JOINS')
print('='*100)
print()

print('Q22: Column names and types')
print('-'*100)
print('Monthly schema:')
print(monthly.dtypes)
print()
print('Annual schema:')
print(annual.dtypes)
print()

print('Q23: return_coverage_detailed.csv schema')
print('-'*100)
print('Current columns:')
print(coverage.columns.tolist())
print('Dtypes:')
print(coverage.dtypes)
print()

print('Q24: Join keys')
print('-'*100)
print('Recommended join approach:')
print('  Monthly: ticker_base + year + month')
print('  Annual: ticker_base + year')
print('  To existing dataset: Match on instrument (after suffix handling)')
print()

print('Q25: Desired output tables')
print('-'*100)
print('Recommended structure:')
print('  1. monthly_returns_clean.csv')
print('     - Columns: instrument, ticker_base, year, month, date, total_return, data_tier')
print('  2. annual_returns_backup.csv')
print('     - Columns: instrument, ticker_base, year, total_return, used_as_backup')
print('  3. return_data_audit.csv')
print('     - Columns: instrument, year, tier, valid_months, has_backup, exclusion_reason')
print()

print('='*100)
print('SECTION 8: VALIDATION RULES')
print('='*100)
print()

print('Q26: Sanity checks')
print('-'*100)
monthly_clean = monthly['Total Return'].dropna()
annual_clean = annual['Total Return'].dropna()

print('Monthly return range:')
print(f'  Min: {monthly_clean.min():.2f}%')
print(f'  Max: {monthly_clean.max():.2f}%')
print(f'  Mean: {monthly_clean.mean():.2f}%')
print(f'  Std: {monthly_clean.std():.2f}%')
print()

print('Annual return range:')
print(f'  Min: {annual_clean.min():.2f}%')
print(f'  Max: {annual_clean.max():.2f}%')
print(f'  Mean: {annual_clean.mean():.2f}%')
print(f'  Std: {annual_clean.std():.2f}%')
print()

# Extreme values
monthly_extremes = monthly_clean[(monthly_clean < -50) | (monthly_clean > 100)]
print(f'Monthly returns outside [-50%, +100%]: {len(monthly_extremes)}')
annual_extremes = annual_clean[(annual_clean < -80) | (annual_clean > 200)]
print(f'Annual returns outside [-80%, +200%]: {len(annual_extremes)}')
print()

print('Recommended caps:')
print('  Monthly: [-50%, +100%] (flag outliers beyond this)')
print('  Annual: [-80%, +200%] (flag outliers beyond this)')
print()

print('Q27: Compound vs annual tolerance')
print('-'*100)
print('Tested earlier with ABCB 2013')
print('Recommended tolerance: ±5 percentage points')
print('(Some difference expected due to rounding and timing)')
print()

print('Q28: Data quality issues')
print('-'*100)
print(f'Duplicate rows in monthly: {monthly.duplicated(subset=["Instrument", "Date"]).sum()}')
print(f'Duplicate rows in annual: {annual.duplicated(subset=["Instrument", "Date"]).sum()}')
print(f'Non-numeric returns (monthly): {monthly["Total Return"].isna().sum()}')
print(f'Non-numeric returns (annual): {annual["Total Return"].isna().sum()}')
print()

print('='*100)
print('SECTION 9: REPRO AND DOCUMENTATION')
print('='*100)
print()

print('Q29-30: Config and versioning')
print('-'*100)
print('Recommended approach:')
print('  - Store thresholds in config.json:')
print('    {')
print('      "tier_1_min_months": 9,')
print('      "tier_2_backup_enabled": true,')
print('      "monthly_return_cap_low": -50,')
print('      "monthly_return_cap_high": 100,')
print('      "annual_return_cap_low": -80,')
print('      "annual_return_cap_high": 200')
print('    }')
print('  - Version all generated docs with timestamps')
print('  - Keep analysis script in scripts/ for reproducibility')
print()

print('='*100)
print('ANALYSIS COMPLETE')
print('='*100)
print()
print('All questions answered. Ready for integration plan alignment.')
