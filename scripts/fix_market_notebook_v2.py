#!/usr/bin/env python3
"""
Add back the provenance columns from equity_volatility_by_year.csv merge
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
market_nb_path = base_dir / 'dd_pd_market.ipynb'

print("="*80)
print("ADDING PROVENANCE COLUMNS FROM EQUITY VOLATILITY FILE")
print("="*80)

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find the cell after equity volatility merge (should have "# 5.5 Finalize equity volatility")
for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "# 5.5 Finalize equity volatility column without defaults" in source or "df['equity_vol'] = df['equity_volatility']" in source:
            print(f"Found merge cell at index {i}")
            
            # Add provenance column creation at the end of this cell
            current_source = cell['source']
            
            # Add new lines for provenance
            new_lines = [
                "\n",
                "# 5.7 Add sigma_E provenance columns from merged equity volatility\n",
                "print('[INFO] Adding sigma_E provenance columns from equity_volatility_by_year.csv...')\n",
                "\n",
                "# Merge provenance columns from equity_vol DataFrame\n",
                "provenance_cols = ['ticker_prefix', 'year', 'sigma_E_method', 'sigma_E_window_months']\n",
                "if all(col in equity_vol.columns for col in provenance_cols):\n",
                "    vol_provenance = equity_vol[provenance_cols].copy()\n",
                "    df = df.merge(vol_provenance, on=['ticker_prefix', 'year'], how='left')\n",
                "    \n",
                "    # Calculate window years from window_months\n",
                "    df['sigmaE_window_end_year'] = df['year'] - 1\n",
                "    df['sigma_E_window_months'] = df['sigma_E_window_months'].fillna(0)\n",
                "    df['sigmaE_window_start_year'] = df['sigmaE_window_end_year'] - (df['sigma_E_window_months'] / 12 - 1).clip(lower=0).astype(int)\n",
                "    \n",
                "    print(f'  Provenance added: {df[\"sigma_E_method\"].notna().sum()} rows')\n",
                "    print(f'  Methods: {df[\"sigma_E_method\"].value_counts().to_dict()}')\n",
                "else:\n",
                "    print('  Warning: Provenance columns not found in equity_vol')\n",
                "    # Create dummy provenance for backward compatibility\n",
                "    df['sigmaE_window_end_year'] = df['year'] - 1\n",
                "    df['sigmaE_window_start_year'] = df['year'] - 1\n",
                "    df['sigma_E_method'] = 'unknown'\n",
                "    df['sigma_E_window_months'] = 0\n"
            ]
            
            cell['source'] = current_source + new_lines
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added provenance columns code")
            break

with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("NEXT: Restart kernel and re-run dd_pd_market.ipynb")
print("="*80)
