#!/usr/bin/env python3
"""
COMPLETE FIX: Add back the FULL equity volatility loading and merging code
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
market_nb_path = base_dir / 'dd_pd_market.ipynb'

print("="*80)
print("COMPLETE FIX - ADDING FULL EQUITY VOLATILITY MERGE")
print("="*80)

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find the cell after market cap merge (Cell 4) and replace/update Cell 5
for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the cell that should have equity vol loading (has provenance code)
        if "# 5.5 Finalize equity volatility column" in source or "# 5.7 Add sigma_E provenance" in source:
            print(f"Found cell to replace at index {i}")
            
            # Replace with COMPLETE equity volatility loading, merging, and provenance
            complete_source = [
                "# 5. Load and Merge Equity Volatility\n",
                "print('[INFO] Loading equity volatility...')\n",
                "\n",
                "# 5.1 Load equity volatility file\n",
                "equity_vol = pd.read_csv(vol_fp)\n",
                "\n",
                "# 5.2 NEW FORMAT: Use ticker_base and sigma_E (already standardized)\n",
                "equity_vol['ticker_prefix'] = equity_vol['ticker_base']\n",
                "equity_vol['equity_volatility'] = equity_vol['sigma_E']\n",
                "vol_annual = equity_vol[['ticker_prefix','year','equity_volatility']]\n",
                "\n",
                "# 5.3 Merge into main DataFrame\n",
                "df = df.merge(\n",
                "    vol_annual,\n",
                "    on=['ticker_prefix','year'],\n",
                "    how='left'\n",
                ")\n",
                "\n",
                "# 5.4 Validate required inputs\n",
                "required_columns = ['instrument', 'year', 'market_cap', 'equity_volatility', 'rf', 'debt_total']\n",
                "missing_required = [col for col in required_columns if col not in df.columns]\n",
                "if missing_required:\n",
                "    missing_str = ', '.join(missing_required)\n",
                "    raise AssertionError(f\"Missing required columns after merge: {missing_str}\")\n",
                "\n",
                "invalid_mask = df[required_columns].isna().any(axis=1)\n",
                "if invalid_mask.any():\n",
                "    invalid_count = invalid_mask.sum()\n",
                "    print(f\"[WARN] Dropping {invalid_count} rows with missing required inputs.\")\n",
                "    invalid_summary = df.loc[invalid_mask, ['instrument','year']].copy()\n",
                "    print(invalid_summary.to_string(index=False))\n",
                "    df = df[~invalid_mask].copy()\n",
                "    df['solver_status'] = 'pending'\n",
                "else:\n",
                "    print(\"[INFO] All required inputs present for merged dataset.\")\n",
                "\n",
                "# 5.5 Finalize equity volatility column\n",
                "df['equity_vol'] = df['equity_volatility']\n",
                "\n",
                "# 5.6 Surviving row counts by year\n",
                "surviving_rows_by_year = df.groupby('year').size().sort_index()\n",
                "print('[INFO] Surviving rows by year after input validation:')\n",
                "print(surviving_rows_by_year)\n",
                "\n",
                "# 5.7 Add sigma_E provenance columns from merged equity volatility\n",
                "print('[INFO] Adding sigma_E provenance columns...')\n",
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
                "    print('  Warning: Provenance columns not found')\n",
                "    df['sigmaE_window_end_year'] = df['year'] - 1\n",
                "    df['sigmaE_window_start_year'] = df['year'] - 1\n",
                "    df['sigma_E_method'] = 'unknown'\n",
                "    df['sigma_E_window_months'] = 0\n",
                "\n",
                "# 5.8 Create time-tagged columns for solver\n",
                "print('[INFO] Creating time-tagged columns...')\n",
                "\n",
                "df['E_t'] = df['market_cap']  # Equity value at time t\n",
                "df['F_t'] = df['F']  # Face value of debt\n",
                "df['rf_t'] = df['rf']  # Risk-free rate\n",
                "df['T'] = 1.0  # Time horizon\n",
                "df['sigma_E_tminus1'] = df['equity_volatility']  # From file, already at t-1\n",
                "\n",
                "print(f'  E_t: {df[\"E_t\"].notna().sum()} values')\n",
                "print(f'  F_t: {df[\"F_t\"].notna().sum()} values')\n",
                "print(f'  rf_t: {df[\"rf_t\"].notna().sum()} values')\n",
                "print(f'  sigma_E_tminus1: {df[\"sigma_E_tminus1\"].notna().sum()} values')\n",
                "print(f'  equity_vol: {df[\"equity_vol\"].notna().sum()} values')\n"
            ]
            
            cell['source'] = complete_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Replaced with COMPLETE equity volatility code")
            break

with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)

print("✅ Saved fixed notebook")
print("\n" + "="*80)
print("COMPLETE FIX APPLIED:")
print("1. Load equity_volatility_by_year.csv")
print("2. Rename columns (ticker_base → ticker_prefix, sigma_E → equity_volatility)")
print("3. Merge into main DataFrame")
print("4. Validate required columns")
print("5. Create equity_vol column")
print("6. Add provenance columns")
print("7. Create time-tagged columns")
print("\nAll steps now included in single cell!")
print("="*80)
print("NEXT: Restart kernel and re-run dd_pd_market.ipynb")
print("="*80)
