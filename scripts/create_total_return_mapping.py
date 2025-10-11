#!/usr/bin/env python3
"""
Create lean total return mapping for esg_0718.csv instruments
Maps 2013-2023 total returns to existing instrument tickers
"""

import pandas as pd
from pathlib import Path

base_dir = Path(__file__).parent.parent
print("="*80)
print("CREATE TOTAL RETURN MAPPING FOR ESG_0718 INSTRUMENTS")
print("="*80)

# 1. Load main datasheet to get instruments
print("\n[1] Loading esg_0718.csv to get instrument list...")
esg = pd.read_csv(base_dir / 'data/clean/esg_0718.csv')
instruments_in_use = esg['instrument'].unique()
print(f"    Found {len(instruments_in_use)} unique instruments")
print(f"    Years: {sorted(esg['year'].unique())}")

# 2. Load raw return data
print("\n[2] Loading raw return data (2013-2023)...")
monthly = pd.read_csv(base_dir / 'data/clean/raw_monthly_total_return_2013_2023 (1).csv')
monthly.columns = monthly.columns.str.strip()
monthly = monthly.rename(columns={'Instrument': 'instrument', 'Date': 'date', 'Total Return': 'total_return'})
monthly['date'] = pd.to_datetime(monthly['date'])
monthly['year'] = monthly['date'].dt.year

annual = pd.read_csv(base_dir / 'data/clean/raw_yearly_total_return_2013_2023 (1).csv')
annual.columns = annual.columns.str.strip()
annual = annual.rename(columns={'Instrument': 'instrument', 'Date': 'year', 'Total Return': 'total_return'})
annual['year'] = annual['year'].astype(int)

# Filter to 2013-2023
monthly = monthly[monthly['year'].between(2013, 2023)].copy()
annual = annual[annual['year'].between(2013, 2023)].copy()

# IMPORTANT: Convert from percentage to decimal (e.g., 6.16% -> 0.0616)
monthly['total_return'] = monthly['total_return'] / 100
annual['total_return'] = annual['total_return'] / 100

print(f"    Monthly: {len(monthly):,} rows, {monthly['instrument'].nunique()} instruments")
print(f"    Annual: {len(annual):,} rows, {annual['instrument'].nunique()} instruments")

# 3. Load ticker mapping exceptions
print("\n[3] Loading ticker mapping exceptions...")
exceptions = pd.read_csv(base_dir / 'data/clean/ticker_mapping_exceptions.csv')
exception_map = dict(zip(exceptions['return_instrument'], exceptions['list_bank_ticker']))
print(f"    Loaded {len(exceptions)} manual mappings")

# 4. Standardize tickers in return data
def standardize_ticker(inst):
    """Map return instrument to esg_0718 ticker using exceptions and suffix stripping."""
    if pd.isna(inst):
        return None
    
    # Check manual exceptions first
    if inst in exception_map:
        return exception_map[inst]
    
    # Strip common suffixes
    ticker = inst
    for suffix in ['.N', '.O', '.OQ', '.K', '.PK', '.A', '.AS']:
        if ticker.endswith(suffix):
            return ticker[:-len(suffix)]
    
    return ticker

print("\n[4] Mapping tickers...")
monthly['ticker'] = monthly['instrument'].apply(standardize_ticker)
annual['ticker'] = annual['instrument'].apply(standardize_ticker)

# 5. Filter to only instruments in esg_0718.csv
print("\n[5] Filtering to esg_0718 instruments only...")
monthly_filtered = monthly[monthly['ticker'].isin(instruments_in_use)].copy()
annual_filtered = annual[annual['ticker'].isin(instruments_in_use)].copy()

print(f"    Monthly: {len(monthly_filtered):,} rows ({len(monthly_filtered)/len(monthly)*100:.1f}% kept)")
print(f"    Annual: {len(annual_filtered):,} rows ({len(annual_filtered)/len(annual)*100:.1f}% kept)")

# 6. Calculate annual returns from monthly (for Tier 1 logic)
print("\n[6] Calculating annual returns from monthly data...")
monthly_valid = monthly_filtered[monthly_filtered['total_return'].notna()].copy()

# Count valid months per ticker-year
monthly_counts = monthly_valid.groupby(['ticker', 'year']).size().reset_index(name='valid_months')

# Calculate annual return as product of (1+monthly returns) - 1
def calc_annual_from_monthly(group):
    """Compound monthly returns to annual (returns already in decimal form)."""
    if group['total_return'].isna().any():
        return pd.Series({'annual_return_from_monthly': None, 'months_used': 0})
    
    # Product of (1 + r_i) - 1 (where r_i is already in decimal form)
    annual_ret = (1 + group['total_return']).prod() - 1
    return pd.Series({
        'annual_return_from_monthly': annual_ret,
        'months_used': len(group)
    })

monthly_annual = monthly_valid.groupby(['ticker', 'year']).apply(calc_annual_from_monthly, include_groups=False).reset_index()

# 7. Merge monthly and annual, apply tier logic
print("\n[7] Applying tier logic...")
# Start with all ticker-year combinations from esg_0718
base = esg[['instrument', 'year']].drop_duplicates().copy()
base = base.rename(columns={'instrument': 'ticker'})

# Add monthly-derived annual returns
base = base.merge(monthly_annual, on=['ticker', 'year'], how='left')

# Add direct annual returns (already in decimal form)
annual_clean = annual_filtered[['ticker', 'year', 'total_return']].rename(columns={'total_return': 'annual_return_direct'})
base = base.merge(annual_clean, on=['ticker', 'year'], how='left')

# Apply tier rules
def assign_tier_and_return(row):
    """
    Tier 1: ≥9 valid months → use monthly-derived annual
    Tier 2: <9 months but annual available → use direct annual
    Tier 3: Neither → exclude
    """
    if pd.notna(row['months_used']) and row['months_used'] >= 9:
        return pd.Series({
            'tier': 'Tier 1',
            'total_return': row['annual_return_from_monthly'],
            'data_source': f"monthly_{int(row['months_used'])}m"
        })
    elif pd.notna(row['annual_return_direct']):
        return pd.Series({
            'tier': 'Tier 2',
            'total_return': row['annual_return_direct'],
            'data_source': 'annual_direct'
        })
    else:
        return pd.Series({
            'tier': 'Tier 3',
            'total_return': None,
            'data_source': 'excluded'
        })

result = base.apply(assign_tier_and_return, axis=1)
base[['tier', 'total_return', 'data_source']] = result

# 8. Generate summary statistics
print("\n" + "="*80)
print("TIER CLASSIFICATION SUMMARY")
print("="*80)
tier_counts = base['tier'].value_counts()
print(tier_counts)
print(f"\nExpected: Tier 1=2354, Tier 2=9, Tier 3=301")
print(f"Actual:   Tier 1={tier_counts.get('Tier 1', 0)}, Tier 2={tier_counts.get('Tier 2', 0)}, Tier 3={tier_counts.get('Tier 3', 0)}")

# 9. Save lean output
print("\n[9] Saving output files...")

# Main output: ticker, year, total_return, tier, data_source
output = base[['ticker', 'year', 'total_return', 'tier', 'data_source']].copy()
output_path = base_dir / 'data/clean/total_return_2013_2023.csv'
output.to_csv(output_path, index=False)
print(f"    ✅ Saved: {output_path}")
print(f"       Rows: {len(output):,}")
print(f"       Columns: {list(output.columns)}")

# Diagnostic output: full details
diagnostic = base.copy()
diagnostic_path = base_dir / 'data/clean/total_return_diagnostic.csv'
diagnostic.to_csv(diagnostic_path, index=False)
print(f"    ✅ Saved: {diagnostic_path} (diagnostic)")

# 10. Validation checks
print("\n" + "="*80)
print("VALIDATION CHECKS")
print("="*80)

# Check A: Coverage
total_in_esg = len(esg)
total_with_returns = len(base[base['total_return'].notna()])
coverage_rate = total_with_returns / total_in_esg * 100
print(f"\n✓ Coverage: {total_with_returns:,} / {total_in_esg:,} ({coverage_rate:.1f}%)")

# Check B: Year range
min_year = base['year'].min()
max_year = base['year'].max()
print(f"✓ Year range: {min_year} to {max_year}")
assert max_year == 2023, "Max year should be 2023"

# Check C: Tier counts
expected = {'Tier 1': 2354, 'Tier 2': 9, 'Tier 3': 301}
tier_match = all([
    tier_counts.get('Tier 1', 0) == expected['Tier 1'],
    tier_counts.get('Tier 2', 0) == expected['Tier 2'],
    tier_counts.get('Tier 3', 0) == expected['Tier 3']
])
if tier_match:
    print(f"✓ Tier counts: MATCH baseline")
else:
    print(f"⚠️  Tier counts: DIFFER from baseline")
    for tier in ['Tier 1', 'Tier 2', 'Tier 3']:
        actual = tier_counts.get(tier, 0)
        expected_val = expected[tier]
        diff = actual - expected_val
        print(f"   {tier}: {actual} (expected {expected_val}, diff {diff:+d})")

# Sample data
print("\n" + "="*80)
print("SAMPLE OUTPUT (first 10 rows)")
print("="*80)
print(output.head(10).to_string(index=False))

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print("\nNext step: Merge total_return_2013_2023.csv into esg_0718.csv")
print("This will replace the 'rit' column with new total return data")
print("="*80)
