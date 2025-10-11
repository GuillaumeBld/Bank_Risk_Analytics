#!/usr/bin/env python3
"""
Remove the OLD sigma_E calculation cell from dd_pd_market.ipynb
that's overwriting the correctly merged equity volatility values
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
market_nb_path = base_dir / 'dd_pd_market.ipynb'

print("="*80)
print("FIXING MARKET NOTEBOOK - REMOVING OLD SIGMA_E CALCULATION")
print("="*80)

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find and remove the cell that calculates sigma_E_tminus1 from rolling rit
removed_count = 0
new_cells = []

for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        # Check if this is the problematic cell
        if "def rolling_sigma_prior" in source and "df['equity_vol'] = df['sigma_E_tminus1']" in source:
            print(f"Found problematic cell at index {i}")
            print("Cell content (first 200 chars):")
            print(source[:200])
            print("\n❌ REMOVING this cell - it overwrites correct sigma_E!")
            removed_count += 1
            continue  # Skip this cell
    
    new_cells.append(cell)

market_nb['cells'] = new_cells

# Save fixed notebook
with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)

print(f"\n✅ Removed {removed_count} problematic cell(s)")
print(f"✅ Saved fixed notebook: {market_nb_path.name}")
print("\n" + "="*80)
print("NEXT STEPS:")
print("1. Reopen dd_pd_market.ipynb in Jupyter")
print("2. Restart kernel")
print("3. Run all cells")
print("4. Check 2018 DD values - they should now be realistic!")
print("="*80)
