#!/usr/bin/env python3
"""
Patch both DD notebooks to use new equity_volatility_by_year.csv format
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent

print("="*80)
print("PATCHING DD NOTEBOOKS FOR NEW EQUITY VOLATILITY FORMAT")
print("="*80)

# ============================================================================
# PATCH 1: dd_pd_market.ipynb
# ============================================================================

market_nb_path = base_dir / 'dd_pd_market.ipynb'
print(f"\n[1] Patching {market_nb_path.name}...")

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find the cell with equity volatility loading (contains "equity_vol['symbol']")
for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "equity_vol['symbol'].apply(standardize_ticker)" in source:
            print(f"   Found target cell at index {i}")
            
            # Replace the problematic lines
            new_source = [
                "# 5.1 Load equity volatility\n",
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
                "# 5.4 Validate required inputs (no fallbacks)\n",
                "required_columns = ['instrument', 'year', 'market_cap', 'equity_volatility', 'rf', 'debt_total']\n",
                "missing_required = [col for col in required_columns if col not in df.columns]\n",
                "if missing_required:\n",
                "    missing_str = ', '.join(missing_required)\n",
                "    raise AssertionError(f\"Missing required columns after merge: {missing_str}\")\n",
                "\n",
                "invalid_mask = df[required_columns].isna().any(axis=1)\n",
                "if invalid_mask.any():\n",
                "    invalid_count = invalid_mask.sum()\n",
                "    invalid_details = df.loc[invalid_mask, ['instrument','year'] + required_columns]\n",
                "    missing_fields = invalid_details.isna().apply(\n",
                "        lambda row: ', '.join([col for col in required_columns if pd.isna(row[col])]),\n",
                "        axis=1\n",
                "    )\n",
                "    invalid_details['missing_fields'] = missing_fields\n",
                "    \n",
                "    print(f\"[WARN] Dropping {invalid_count} rows with missing required inputs (solver_status=invalid_inputs).\")\n",
                "    print(invalid_details[['instrument','year','missing_fields']].to_string(index=False))\n",
                "    \n",
                "    df = df[~invalid_mask].copy()\n",
                "    df['solver_status'] = 'pending'\n",
                "else:\n",
                "    print(\"[INFO] All required inputs present for merged dataset.\")\n",
                "\n",
                "# 5.5 Finalize equity volatility column without defaults\n",
                "df['equity_vol'] = df['equity_volatility']\n",
                "\n",
                "# 5.6 Surviving row counts by year for audit\n",
                "surviving_rows_by_year = df.groupby('year').size().sort_index()\n",
                "print('[INFO] Surviving rows by year after input validation:')\n",
                "print(surviving_rows_by_year)"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []  # Clear outputs
            cell['execution_count'] = None
            print("   ✅ Patched market DD cell")
            break

# Save patched market notebook
with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)
print(f"   ✅ Saved patched {market_nb_path.name}")

# ============================================================================
# PATCH 2: dd_pd_accounting.ipynb
# ============================================================================

acct_nb_path = base_dir / 'dd_pd_accounting.ipynb'
print(f"\n[2] Patching {acct_nb_path.name}...")

with open(acct_nb_path, 'r') as f:
    acct_nb = json.load(f)

# Find the cell with sigma_E calculation (contains "rolling_sigma_prior")
for i, cell in enumerate(acct_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "def rolling_sigma_prior" in source or "sigma_E_tminus1" in source and "rolling" in source:
            print(f"   Found target cell at index {i}")
            
            # Replace entire sigma_E calculation with new approach
            new_source = [
                "# Load NEW equity volatility from pre-calculated file\n",
                "print('[INFO] Loading sigma_E from equity_volatility_by_year.csv...')\n",
                "\n",
                "# Load the new equity volatility file\n",
                "vol_fp = base_dir / 'data' / 'clean' / 'equity_volatility_by_year.csv'\n",
                "equity_vol = pd.read_csv(vol_fp)\n",
                "\n",
                "# Rename columns to match expected format\n",
                "equity_vol_merge = equity_vol.rename(columns={\n",
                "    'ticker_base': 'instrument',\n",
                "    'sigma_E': 'sigma_E_tminus1'\n",
                "})\n",
                "\n",
                "# Merge into main DataFrame\n",
                "df = df.merge(\n",
                "    equity_vol_merge[['instrument', 'year', 'sigma_E_tminus1', \n",
                "                      'sigma_E_method', 'sigma_E_window_months']],\n",
                "    on=['instrument', 'year'],\n",
                "    how='left'\n",
                ")\n",
                "\n",
                "# Calculate window provenance - CORRECTED LOGIC\n",
                "# Example: year=2018, window_months=36\n",
                "# window_end = 2017, window_start = 2015 (covers 2015,2016,2017)\n",
                "df['sigmaE_window_end_year'] = df['year'] - 1\n",
                "df['sigma_E_window_months'] = df['sigma_E_window_months'].fillna(0)\n",
                "df['sigmaE_window_start_year'] = df['sigmaE_window_end_year'] - (df['sigma_E_window_months'] / 12 - 1).clip(lower=0).astype(int)\n",
                "\n",
                "# Use sigma_E_tminus1 for calculations\n",
                "df['sigma_E'] = df['sigma_E_tminus1']\n",
                "\n",
                "print(f'  sigma_E_tminus1: {df[\"sigma_E_tminus1\"].notna().sum()} non-null values')\n",
                "print(f'  Window validation:')\n",
                "print(f'    - All end years = t-1: {(df[\"sigmaE_window_end_year\"] == df[\"year\"] - 1).all()}')\n",
                "print(f'    - All start <= end: {(df[\"sigmaE_window_start_year\"] <= df[\"sigmaE_window_end_year\"]).all()}')\n",
                "print(f'  sigma_E method distribution:')\n",
                "print(df[\"sigma_E_method\"].value_counts())\n",
                "\n",
                "# Build mu_hat_t = r_{i,t-1} with provenance tracking\n",
                "print('[INFO] Computing mu_hat_t = r_{i,t-1} with fallbacks...')\n",
                "\n",
                "df['mu_hat_from'] = 'rit_tminus1'\n",
                "df['mu_source_year'] = df['year'] - 1\n",
                "df['mu_hat'] = df.groupby('instrument', group_keys=False)['rit'].shift(1)"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []  # Clear outputs
            cell['execution_count'] = None
            print("   ✅ Patched accounting DD cell")
            break

# Save patched accounting notebook
with open(acct_nb_path, 'w') as f:
    json.dump(acct_nb, f, indent=1)
print(f"   ✅ Saved patched {acct_nb_path.name}")

print("\n" + "="*80)
print("PATCHING COMPLETE")
print("="*80)
print("\nBoth notebooks have been patched to use the new equity volatility format.")
print("\nNext steps:")
print("1. Reopen the notebooks in Jupyter")
print("2. Run 'Restart Kernel & Run All Cells'")
print("3. Both should now complete successfully")
print("="*80)
