#!/usr/bin/env python3
"""
Fix the lambda function bug in dd_pd_market.ipynb
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
market_nb_path = base_dir / 'dd_pd_market.ipynb'

print("="*80)
print("FIXING LAMBDA BUG IN dd_pd_market.ipynb")
print("="*80)

with open(market_nb_path, 'r') as f:
    market_nb = json.load(f)

# Find the cell with the problematic lambda
for i, cell in enumerate(market_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if "missing_fields = invalid_details.isna().apply" in source:
            print(f"Found target cell at index {i}")
            
            # Replace with fixed version
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
                "    print(f\"[WARN] Dropping {invalid_count} rows with missing required inputs (solver_status=invalid_inputs).\")\n",
                "    \n",
                "    # Show which instruments/years are affected\n",
                "    invalid_summary = df.loc[invalid_mask, ['instrument','year']].copy()\n",
                "    print(invalid_summary.to_string(index=False))\n",
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
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Fixed lambda bug")
            break

with open(market_nb_path, 'w') as f:
    json.dump(market_nb, f, indent=1)

print("✅ Saved patched notebook")
print("="*80)
print("COMPLETE - Restart kernel and re-run the notebook")
print("="*80)
