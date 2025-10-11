#!/usr/bin/env python3
"""
Add missing flags that were created in the old sigma_E calculation cell
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
acct_nb_path = base_dir / 'dd_pd_accounting.ipynb'

print("="*80)
print("ADDING MISSING FLAGS TO ACCOUNTING NOTEBOOK")
print("="*80)

with open(acct_nb_path, 'r') as f:
    acct_nb = json.load(f)

# Find the cell with size_bucket creation
for i, cell in enumerate(acct_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the cell that creates size_bucket
        if "df['size_bucket'] = size_bucket" in source and "print(f'  Size bucket counts:" in source:
            print(f"Found size_bucket cell at index {i}")
            
            # Get current source
            current_lines = cell['source']
            
            # Add missing flags
            additional_lines = [
                "\n",
                "# Create flags that were in old sigma_E calculation (now dummy flags)\n",
                "# Since we're using pre-calculated sigma_E from file, these are all False\n",
                "df['insufficient_returns'] = False  # All sigma_E come from file, none insufficient\n",
                "df['imputed_sigmaE_sizebucket'] = False  # Will be set properly based on sigma_E_method\n",
                "\n",
                "# Mark imputed values based on method from equity_volatility file\n",
                "if 'sigma_E_method' in df.columns:\n",
                "    df['imputed_sigmaE_sizebucket'] = df['sigma_E_method'] == 'peer_median'\n",
                "    print(f'  Imputed sigma_E (peer_median): {df[\"imputed_sigmaE_sizebucket\"].sum()} rows')\n"
            ]
            
            # Combine
            cell['source'] = current_lines + additional_lines
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added missing flags")
            break

with open(acct_nb_path, 'w') as f:
    json.dump(acct_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("MISSING FLAGS NOW CREATED:")
print("  - insufficient_returns (dummy: False for all)")
print("  - imputed_sigmaE_sizebucket (based on sigma_E_method)")
print("\n" + "="*80)
print("NEXT: Restart kernel and re-run dd_pd_accounting.ipynb")
print("="*80)
