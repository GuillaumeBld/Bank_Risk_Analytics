#!/usr/bin/env python3
"""
Create fixed-name links to latest DD output files.
This ensures validator can find the correct files after notebooks run with timestamps.
"""

import glob
import shutil
from pathlib import Path

base_dir = Path(__file__).parent.parent
output_dir = base_dir / 'data' / 'outputs' / 'datasheet'

print("="*80)
print("LINKING LATEST DD OUTPUTS TO FIXED NAMES")
print("="*80)

# Market DD: find latest market_*.csv and copy to dd_pd_market_results.csv
market_pattern = str(output_dir / 'market_*.csv')
market_files = sorted(glob.glob(market_pattern), key=lambda x: Path(x).stat().st_mtime, reverse=True)

if market_files:
    latest_market = Path(market_files[0])
    target_market = output_dir / 'dd_pd_market_results.csv'
    shutil.copy2(latest_market, target_market)
    print(f"✅ Market DD: {latest_market.name} → dd_pd_market_results.csv")
else:
    print("⚠️  No market DD files found")

# Accounting DD: find latest accounting_*.csv and copy to dd_pd_accounting_results.csv
accounting_pattern = str(output_dir / 'accounting_*.csv')
accounting_files = sorted(glob.glob(accounting_pattern), key=lambda x: Path(x).stat().st_mtime, reverse=True)

if accounting_files:
    latest_accounting = Path(accounting_files[0])
    target_accounting = output_dir / 'dd_pd_accounting_results.csv'
    shutil.copy2(latest_accounting, target_accounting)
    print(f"✅ Accounting DD: {latest_accounting.name} → dd_pd_accounting_results.csv")
else:
    print("⚠️  No accounting DD files found")

print("="*80)
print("COMPLETE - Fixed-name files ready for validation")
print("="*80)
