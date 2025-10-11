#!/usr/bin/env python3
"""
Add back ALL required columns: provenance AND time-tagged columns
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
market_nb_path = base_dir / 'dd_pd_market.ipynb'

print("="*80)
print("ADDING PROVENANCE AND TIME-TAGGED COLUMNS")
print("="*80)

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find the cell after equity volatility merge
for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "# 5.7 Add sigma_E provenance columns from merged equity volatility" in source:
            print(f"Found provenance cell at index {i}")
            
            # Replace with complete version including time-tagged columns
            new_source = [
                "# 5.5 Finalize equity volatility column without defaults\n",
                "df['equity_vol'] = df['equity_volatility']\n",
                "\n",
                "# 5.6 Surviving row counts by year for audit\n",
                "surviving_rows_by_year = df.groupby('year').size().sort_index()\n",
                "print('[INFO] Surviving rows by year after input validation:')\n",
                "print(surviving_rows_by_year)\n",
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
                "    df['sigma_E_window_months'] = 0\n",
                "\n",
                "# 5.8 Create time-tagged columns for solver\n",
                "print('[INFO] Creating time-tagged columns...')\n",
                "\n",
                "# Current year values (time t)\n",
                "df['E_t'] = df['market_cap']  # Equity value at time t\n",
                "df['F_t'] = df['F']  # Face value of debt at time t (already in same units)\n",
                "df['rf_t'] = df['rf']  # Risk-free rate at time t\n",
                "df['T'] = 1.0  # Time horizon\n",
                "\n",
                "# Sigma_E at t-1 (already loaded from equity_volatility_by_year.csv)\n",
                "df['sigma_E_tminus1'] = df['equity_volatility']  # This is already at t-1 from the file\n",
                "\n",
                "# Validate time-tagged columns\n",
                "print(f'  E_t (market_cap): {df[\"E_t\"].notna().sum()} values')\n",
                "print(f'  F_t (debt): {df[\"F_t\"].notna().sum()} values')\n",
                "print(f'  rf_t: {df[\"rf_t\"].notna().sum()} values')\n",
                "print(f'  sigma_E_tminus1: {df[\"sigma_E_tminus1\"].notna().sum()} values')\n"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added complete provenance and time-tagged columns")
            break

with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("COMPLETE - All required columns now created properly:")
print("  - sigma_E provenance (method, window, etc.)")
print("  - Time-tagged columns (E_t, F_t, rf_t, sigma_E_tminus1)")
print("\nNEXT: Restart kernel and re-run dd_pd_market.ipynb")
print("="*80)
