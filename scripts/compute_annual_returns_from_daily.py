#!/usr/bin/env python3
"""
Compute Annual Returns from Daily Total Returns

This script processes raw daily total return data and computes annual returns
by compounding daily returns within each calendar year.

Output: annual_returns_from_daily.csv with columns [ticker, year, annual_return]
"""

import pandas as pd
import numpy as np
from pathlib import Path

def find_repo_root(start: Path, marker: str = '.git') -> Path:
    """Walk up from start until a directory containing marker is found."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / marker).exists():
            return candidate
    return current

def compute_annual_returns():
    """Compute annual returns from daily data."""
    base_dir = find_repo_root(Path.cwd())
    
    # Input and output paths
    daily_fp = base_dir / 'data' / 'clean' / 'raw_daily_total_return_2015_2023.csv'
    output_fp = base_dir / 'data' / 'clean' / 'annual_returns_from_daily.csv'
    
    print(f'[INFO] Loading daily returns from {daily_fp.name}...')
    
    # Load daily returns
    daily = pd.read_csv(daily_fp)
    daily.columns = ['Instrument', 'Total Return', 'Date']
    
    print(f'  Loaded {len(daily):,} daily observations')
    
    # Standardize ticker: remove exchange suffixes (.N, .OQ, etc.)
    daily['ticker'] = daily['Instrument'].str.replace(r'\..*$', '', regex=True)
    
    # Parse date
    daily['date'] = pd.to_datetime(daily['Date'], format='%m/%d/%y', errors='coerce')
    daily = daily.dropna(subset=['date'])
    daily['year'] = daily['date'].dt.year
    
    # Convert total return to decimal (assuming percentage)
    daily['daily_return'] = pd.to_numeric(daily['Total Return'], errors='coerce') / 100.0
    
    # Drop missing returns
    initial_count = len(daily)
    daily = daily.dropna(subset=['daily_return'])
    dropped = initial_count - len(daily)
    if dropped > 0:
        print(f'  Dropped {dropped:,} rows with missing returns')
    
    print(f'[INFO] Computing annual returns by compounding daily returns...')
    
    # Compound daily returns to annual: (1+r1)*(1+r2)*...*(1+rn) - 1
    annual_returns = daily.groupby(['ticker', 'year']).agg(
        annual_return=('daily_return', lambda x: np.prod(1 + x) - 1),
        days_count=('daily_return', 'count')
    ).reset_index()
    
    print(f'  Computed {len(annual_returns):,} annual returns')
    print(f'  Years covered: {sorted(annual_returns["year"].unique())}')
    print(f'  Unique tickers: {annual_returns["ticker"].nunique()}')
    
    # Show summary statistics
    print(f'\n[INFO] Annual return statistics:')
    print(f'  Mean: {annual_returns["annual_return"].mean():.4f}')
    print(f'  Median: {annual_returns["annual_return"].median():.4f}')
    print(f'  Std: {annual_returns["annual_return"].std():.4f}')
    print(f'  Min: {annual_returns["annual_return"].min():.4f}')
    print(f'  Max: {annual_returns["annual_return"].max():.4f}')
    
    print(f'\n[INFO] Days per year statistics:')
    print(f'  Mean: {annual_returns["days_count"].mean():.1f}')
    print(f'  Median: {annual_returns["days_count"].median():.1f}')
    print(f'  Min: {annual_returns["days_count"].min()}')
    print(f'  Max: {annual_returns["days_count"].max()}')
    
    # Save output
    output_fp.parent.mkdir(parents=True, exist_ok=True)
    annual_returns.to_csv(output_fp, index=False)
    print(f'\n[INFO] Saved annual returns to {output_fp}')
    
    return annual_returns

if __name__ == '__main__':
    compute_annual_returns()
