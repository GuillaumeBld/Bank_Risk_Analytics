#!/usr/bin/env python3
"""
Quick fix: Copy existing market results to timestamped format for merging
"""

import shutil
from pathlib import Path
from datetime import datetime
import pytz

def find_repo_root(start: Path, marker: str = '.git') -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / marker).exists():
            return candidate
    return current

base_dir = find_repo_root(Path.cwd())
output_dir = base_dir / 'data' / 'outputs' / 'datasheet'

# Get timestamp
cdt = pytz.timezone('America/Chicago')
timestamp = datetime.now(cdt).strftime('%Y%m%d_%H%M%S')

# Copy old market file to new timestamped format
old_market = output_dir / 'dd_pd_market_results.csv'
new_market = output_dir / f'market_{timestamp}.csv'

if old_market.exists():
    shutil.copy(old_market, new_market)
    print(f"[INFO] Copied {old_market.name} to {new_market.name}")
    print(f"[INFO] You can now run merging.ipynb")
else:
    print(f"[ERROR] {old_market} not found")
    print("[INFO] Please run dd_pd_market.ipynb first")
