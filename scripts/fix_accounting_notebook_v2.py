#!/usr/bin/env python3
"""
Add back the size_bucket creation code that was accidentally removed
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
acct_nb_path = base_dir / 'dd_pd_accounting.ipynb'

print("="*80)
print("ADDING BACK SIZE_BUCKET COLUMN TO ACCOUNTING NOTEBOOK")
print("="*80)

with open(acct_nb_path, 'r') as f:
    acct_nb = json.load(f)

# Find the cell after sigma_E loading and add size_bucket creation
for i, cell in enumerate(acct_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the cell that loads sigma_E (has "equity_volatility_by_year.csv")
        if "equity_volatility_by_year.csv" in source and "df['sigma_E'] = df['sigma_E_tminus1']" in source:
            print(f"Found sigma_E loading cell at index {i}")
            
            # Add size_bucket creation at the end
            current_source = cell['source']
            
            new_lines = [
                "\n",
                "# Build mu_hat_t = r_{i,t-1} with provenance tracking\n",
                "print('[INFO] Computing mu_hat_t = r_{i,t-1} with fallbacks...')\n",
                "\n",
                "df['mu_hat_from'] = 'rit_tminus1'\n",
                "df['mu_source_year'] = df['year'] - 1\n",
                "df['mu_hat'] = df.groupby('instrument', group_keys=False)['rit'].shift(1)\n",
                "\n",
                "# Create size buckets for imputation (needed for mu_hat fallback)\n",
                "print('[INFO] Creating size buckets...')\n",
                "df = df.sort_values(['instrument', 'year']).reset_index(drop=True)\n",
                "\n",
                "size_bucket = np.select(\n",
                "    [df.get('dummylarge', 0) == 1, df.get('dummymid', 0) == 1],\n",
                "    ['large', 'mid'],\n",
                "    default='small'\n",
                ")\n",
                "df['size_bucket'] = size_bucket\n",
                "print(f'  Size bucket distribution: {df[\"size_bucket\"].value_counts().to_dict()}')\n"
            ]
            
            cell['source'] = current_source + new_lines
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added size_bucket creation to cell")
            break

with open(acct_nb_path, 'w') as f:
    json.dump(acct_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("COMPLETE - size_bucket column will now be created properly")
print("This column is needed for mu_hat imputation later in the notebook")
print("\n" + "="*80)
print("NEXT: Restart kernel and re-run dd_pd_accounting.ipynb")
print("="*80)
