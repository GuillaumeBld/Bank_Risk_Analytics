#!/usr/bin/env python3
"""
FINAL FIX: Add size_bucket creation to the END of the sigma_E/mu_hat cell
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
acct_nb_path = base_dir / 'dd_pd_accounting.ipynb'

print("="*80)
print("FINAL FIX - ADDING SIZE_BUCKET TO ACCOUNTING NOTEBOOK")
print("="*80)

with open(acct_nb_path, 'r') as f:
    acct_nb = json.load(f)

# Find the cell with mu_hat creation (line 411 ends with mu_hat = ...)
for i, cell in enumerate(acct_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the cell that has both sigma_E and mu_hat
        if "df['mu_hat'] = df.groupby('instrument', group_keys=False)['rit'].shift(1)" in source:
            print(f"Found mu_hat cell at index {i}")
            
            # Get current source
            current_lines = cell['source']
            
            # Add size_bucket creation at the end
            additional_lines = [
                "\n",
                "# Create size buckets for later imputation\n",
                "print('[INFO] Creating size buckets...')\n",
                "df = df.sort_values(['instrument', 'year']).reset_index(drop=True)\n",
                "\n",
                "size_bucket = np.select(\n",
                "    [df.get('dummylarge', 0) == 1, df.get('dummymid', 0) == 1],\n",
                "    ['large', 'mid'],\n",
                "    default='small'\n",
                ")\n",
                "df['size_bucket'] = size_bucket\n",
                "print(f'  Size bucket counts: {df[\"size_bucket\"].value_counts().to_dict()}')\n"
            ]
            
            # Combine
            cell['source'] = current_lines + additional_lines
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added size_bucket creation")
            break

with open(acct_nb_path, 'w') as f:
    json.dump(acct_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("SIZE_BUCKET NOW CREATED PROPERLY")
print("Cell 5 now includes:")
print("  1. Load sigma_E from equity_volatility_by_year.csv")
print("  2. Calculate window provenance")
print("  3. Create mu_hat")
print("  4. CREATE SIZE_BUCKET ← NEW!")
print("\n" + "="*80)
print("NEXT: Restart kernel and re-run dd_pd_accounting.ipynb")
print("="*80)
