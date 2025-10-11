#!/usr/bin/env python3
"""
Analyze Total Return Data Coverage
Identifies monthly data gaps and annual backup availability
"""

import pandas as pd
import numpy as np
from pathlib import Path

# File paths
base_dir = Path('/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank')
monthly_file = base_dir / 'data/clean/raw_monthly_total_return_2013_2023 (1).csv'
annual_file = base_dir / 'data/clean/raw_yearly_total_return_2013_2023 (1).csv'
output_dir = base_dir / 'docs/guides'
output_dir.mkdir(exist_ok=True)

print('='*100)
print('TOTAL RETURN DATA COVERAGE ANALYSIS')
print('='*100)
print()

# Load data
print('Loading data...')
monthly_df = pd.read_csv(monthly_file)
annual_df = pd.read_csv(annual_file)

print(f'  Monthly data: {len(monthly_df):,} rows')
print(f'  Annual data:  {len(annual_df):,} rows')
print()

# Clean instrument names (remove suffixes like .N, .O, .OQ)
monthly_df['instrument_clean'] = monthly_df['Instrument'].str.replace(r'\.[A-Z]+$', '', regex=True)
annual_df['instrument_clean'] = annual_df['Instrument'].str.replace(r'\.[A-Z]+$', '', regex=True)

# Parse dates
monthly_df['date_parsed'] = pd.to_datetime(monthly_df['Date'])
monthly_df['year'] = monthly_df['date_parsed'].dt.year
monthly_df['month'] = monthly_df['date_parsed'].dt.month

# Annual data - year is already in Date column
annual_df['year'] = annual_df['Date'].astype(int)

print('='*100)
print('1. OVERALL DATA SUMMARY')
print('='*100)
print()

# Monthly data summary
monthly_years = sorted(monthly_df['year'].unique())
monthly_instruments = sorted(monthly_df['instrument_clean'].unique())

print(f'Monthly Data:')
print(f'  Years covered: {monthly_years[0]}-{monthly_years[-1]}')
print(f'  Unique banks: {len(monthly_instruments)}')
print(f'  Total observations: {len(monthly_df):,}')
print(f'  Missing returns: {monthly_df["Total Return"].isna().sum():,}')
print()

# Annual data summary
annual_years = sorted(annual_df['year'].unique())
annual_instruments = sorted(annual_df['instrument_clean'].unique())

print(f'Annual Data:')
print(f'  Years covered: {annual_years[0]}-{annual_years[-1]}')
print(f'  Unique banks: {len(annual_instruments)}')
print(f'  Total observations: {len(annual_df):,}')
print(f'  Missing returns: {annual_df["Total Return"].isna().sum():,}')
print()

print('='*100)
print('2. MONTHLY DATA COVERAGE BY BANK-YEAR')
print('='*100)
print()

# Count monthly observations per bank-year
monthly_coverage = monthly_df.groupby(['instrument_clean', 'year']).agg({
    'Total Return': ['count', lambda x: x.notna().sum()]
}).reset_index()
monthly_coverage.columns = ['instrument', 'year', 'total_months', 'valid_months']

print(f'Total bank-year combinations in monthly data: {len(monthly_coverage)}')
print()

# Identify incomplete coverage (< 9 valid months)
incomplete = monthly_coverage[monthly_coverage['valid_months'] < 9].copy()
print(f'Bank-years with < 9 months of data: {len(incomplete)}')
print()

print('='*100)
print('3. ANNUAL BACKUP AVAILABILITY')
print('='*100)
print()

# Check which incomplete cases have annual backup
incomplete['has_annual_backup'] = False
incomplete['annual_return'] = np.nan

for idx, row in incomplete.iterrows():
    instrument = row['instrument']
    year = row['year']
    
    # Look for annual data
    annual_match = annual_df[
        (annual_df['instrument_clean'] == instrument) & 
        (annual_df['year'] == year)
    ]
    
    if len(annual_match) > 0:
        annual_return = annual_match['Total Return'].iloc[0]
        if pd.notna(annual_return):
            incomplete.at[idx, 'has_annual_backup'] = True
            incomplete.at[idx, 'annual_return'] = annual_return

backup_available = incomplete['has_annual_backup'].sum()
backup_missing = len(incomplete) - backup_available

print(f'Incomplete monthly coverage (< 9 months): {len(incomplete)}')
print(f'  With annual backup available: {backup_available} ({100*backup_available/len(incomplete):.1f}%)')
print(f'  Without annual backup: {backup_missing} ({100*backup_missing/len(incomplete):.1f}%)')
print()

print('='*100)
print('4. BREAKDOWN BY COVERAGE LEVEL')
print('='*100)
print()

coverage_bins = [
    (0, 'No data (0 months)'),
    (1, 6, 'Sparse (1-5 months)'),
    (6, 9, 'Partial (6-8 months)'),
    (9, 12, 'Good (9-11 months)'),
    (12, 'Complete (12 months)')
]

for item in coverage_bins:
    if len(item) == 2:
        months, label = item
        count = len(monthly_coverage[monthly_coverage['valid_months'] == months])
    else:
        min_m, max_m, label = item
        count = len(monthly_coverage[
            (monthly_coverage['valid_months'] >= min_m) & 
            (monthly_coverage['valid_months'] < max_m)
        ])
    
    pct = 100 * count / len(monthly_coverage) if len(monthly_coverage) > 0 else 0
    print(f'  {label:<25} {count:>5} ({pct:>5.1f}%)')

print()

print('='*100)
print('5. WORST CASES (< 6 months, no annual backup)')
print('='*100)
print()

worst_cases = incomplete[
    (incomplete['valid_months'] < 6) & 
    (incomplete['has_annual_backup'] == False)
].sort_values(['valid_months', 'instrument'])

if len(worst_cases) > 0:
    print(f'Found {len(worst_cases)} cases with < 6 months and no annual backup:')
    print()
    print(worst_cases[['instrument', 'year', 'valid_months']].head(20).to_string(index=False))
    if len(worst_cases) > 20:
        print(f'  ... and {len(worst_cases) - 20} more')
else:
    print('✓ No worst cases found!')

print()
print('='*100)
print('6. GENERATING DETAILED DOCUMENTATION')
print('='*100)
print()

# Save detailed reports
output_file = output_dir / 'return_data_coverage.md'

with open(output_file, 'w') as f:
    f.write('# Total Return Data Coverage Analysis\n\n')
    f.write('**Generated**: Auto-generated documentation\n\n')
    f.write('---\n\n')
    
    # Overview
    f.write('## Overview\n\n')
    f.write('This document analyzes the coverage and completeness of monthly and annual total return data.\n\n')
    f.write('### Monthly Data\n')
    f.write(f'- **File**: `raw_monthly_total_return_2013_2023 (1).csv`\n')
    f.write(f'- **Years**: {monthly_years[0]}-{monthly_years[-1]}\n')
    f.write(f'- **Banks**: {len(monthly_instruments)}\n')
    f.write(f'- **Observations**: {len(monthly_df):,}\n')
    f.write(f'- **Missing values**: {monthly_df["Total Return"].isna().sum():,}\n\n')
    
    f.write('### Annual Data\n')
    f.write(f'- **File**: `raw_yearly_total_return_2013_2023 (1).csv`\n')
    f.write(f'- **Years**: {annual_years[0]}-{annual_years[-1]}\n')
    f.write(f'- **Banks**: {len(annual_instruments)}\n')
    f.write(f'- **Observations**: {len(annual_df):,}\n')
    f.write(f'- **Missing values**: {annual_df["Total Return"].isna().sum():,}\n\n')
    
    f.write('---\n\n')
    
    # Coverage analysis
    f.write('## Coverage Analysis\n\n')
    f.write('### Monthly Coverage by Level\n\n')
    f.write('| Coverage Level | Count | Percentage |\n')
    f.write('|---------------|-------|------------|\n')
    
    for item in coverage_bins:
        if len(item) == 2:
            months, label = item
            count = len(monthly_coverage[monthly_coverage['valid_months'] == months])
        else:
            min_m, max_m, label = item
            count = len(monthly_coverage[
                (monthly_coverage['valid_months'] >= min_m) & 
                (monthly_coverage['valid_months'] < max_m)
            ])
        pct = 100 * count / len(monthly_coverage) if len(monthly_coverage) > 0 else 0
        f.write(f'| {label} | {count} | {pct:.1f}% |\n')
    
    f.write('\n')
    
    # Incomplete coverage
    f.write('## Incomplete Monthly Coverage (< 9 months)\n\n')
    f.write(f'**Total cases**: {len(incomplete)}\n\n')
    f.write(f'- **With annual backup**: {backup_available} ({100*backup_available/len(incomplete):.1f}%)\n')
    f.write(f'- **Without annual backup**: {backup_missing} ({100*backup_missing/len(incomplete):.1f}%)\n\n')
    
    # Detailed table
    f.write('### Detailed Breakdown\n\n')
    f.write('| Bank | Year | Valid Months | Annual Backup | Annual Return (%) |\n')
    f.write('|------|------|--------------|---------------|-------------------|\n')
    
    for _, row in incomplete.sort_values(['instrument', 'year']).iterrows():
        backup_status = '✓' if row['has_annual_backup'] else '✗'
        annual_val = f"{row['annual_return']:.2f}" if pd.notna(row['annual_return']) else 'N/A'
        f.write(f"| {row['instrument']} | {int(row['year'])} | {int(row['valid_months'])} | {backup_status} | {annual_val} |\n")
    
    f.write('\n---\n\n')
    
    # Recommendations
    f.write('## Recommendations\n\n')
    f.write('### Data Quality Tiers\n\n')
    f.write('**Tier 1: Use as-is** (9-12 months of data)\n')
    tier1 = len(monthly_coverage[monthly_coverage['valid_months'] >= 9])
    f.write(f'- Count: {tier1} bank-years\n')
    f.write(f'- Action: Use monthly data directly\n\n')
    
    f.write('**Tier 2: Use with annual backup** (< 9 months, annual available)\n')
    f.write(f'- Count: {backup_available} bank-years\n')
    f.write(f'- Action: Supplement with annual return data\n\n')
    
    f.write('**Tier 3: Exclude** (< 9 months, no annual backup)\n')
    f.write(f'- Count: {backup_missing} bank-years\n')
    f.write(f'- Action: Exclude from analysis\n\n')
    
    # Summary stats
    f.write('### Summary Statistics\n\n')
    f.write('```\n')
    f.write(f'Total bank-year combinations: {len(monthly_coverage)}\n')
    f.write(f'Usable directly (Tier 1):    {tier1} ({100*tier1/len(monthly_coverage):.1f}%)\n')
    f.write(f'Needs backup (Tier 2):        {backup_available} ({100*backup_available/len(monthly_coverage):.1f}%)\n')
    f.write(f'Should exclude (Tier 3):      {backup_missing} ({100*backup_missing/len(monthly_coverage):.1f}%)\n')
    f.write('```\n\n')
    
    f.write('---\n\n')
    f.write('*Auto-generated by `scripts/analyze_return_data_coverage.py`*\n')

print(f'✓ Documentation saved to: {output_file}')
print()

# Save CSV files for detailed analysis
csv_output = base_dir / 'data/outputs/analysis/return_coverage_detailed.csv'
incomplete.to_csv(csv_output, index=False)
print(f'✓ Detailed CSV saved to: {csv_output}')
print()

print('='*100)
print('ANALYSIS COMPLETE')
print('='*100)
