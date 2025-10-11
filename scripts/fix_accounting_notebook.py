#!/usr/bin/env python3
"""
Remove the OLD sigma_E calculation from dd_pd_accounting.ipynb
that's overwriting the correctly merged equity volatility values
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
acct_nb_path = base_dir / 'dd_pd_accounting.ipynb'

print("="*80)
print("FIXING ACCOUNTING NOTEBOOK - REMOVING OLD SIGMA_E CALCULATION")
print("="*80)

with open(acct_nb_path, 'r') as f:
    acct_nb = json.load(f)

# Find and remove the cell that recalculates sigma_E from rolling rit
removed_count = 0
new_cells = []

for i, cell in enumerate(acct_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        # Check if this is the problematic cell
        if "def rolling_sigma(series: pd.Series)" in source and "df['sigma_E'] = df['sigma_E_raw'].copy()" in source:
            print(f"Found problematic cell at index {i}")
            print("Cell content (first 300 chars):")
            print(source[:300])
            print("\n❌ REMOVING this cell - it overwrites correct sigma_E!")
            removed_count += 1
            continue  # Skip this cell
    
    new_cells.append(cell)

acct_nb['cells'] = new_cells

# Save fixed notebook
with open(acct_nb_path, 'w') as f:
    json.dump(acct_nb, f, indent=1)

print(f"\n✅ Removed {removed_count} problematic cell(s)")
print(f"✅ Saved fixed notebook: {acct_nb_path.name}")
print("\n" + "="*80)
print("IMPORTANT:")
print("The accounting notebook now correctly uses sigma_E from equity_volatility_by_year.csv")
print("WITHOUT recalculating it from rolling rit!")
print("\n" + "="*80)
print("NEXT STEPS:")
print("1. Reopen dd_pd_accounting.ipynb in Jupyter")
print("2. Restart kernel")
print("3. Run all cells")
print("="*80)
