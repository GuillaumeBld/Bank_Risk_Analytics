#!/usr/bin/env python3
"""
Update Jupyter notebooks to use daily-derived returns for drift calculation
"""

import json
from pathlib import Path

def find_repo_root(start: Path, marker: str = '.git') -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / marker).exists():
            return candidate
    return current

base_dir = find_repo_root(Path.cwd())

# Load accounting notebook
accounting_nb_path = base_dir / 'dd_pd_accounting.ipynb'
with open(accounting_nb_path, 'r') as f:
    accounting_nb = json.load(f)

print(f"[INFO] Loaded accounting notebook with {len(accounting_nb['cells'])} cells")

# Find cell 10 (after equity volatility load) and add new cell after it
# Cell 10 has id 'time_tagging_accounting'
new_cell_after_10 = {
    "cell_type": "code",
    "execution_count": None,
    "id": "load_annual_returns_daily",
    "metadata": {},
    "outputs": [],
    "source": [
        "# Load annual returns computed from daily data\n",
        "print('[INFO] Loading annual returns from daily data...')\n",
        "annual_returns_fp = base_dir / 'data' / 'clean' / 'annual_returns_from_daily.csv'\n",
        "annual_returns = pd.read_csv(annual_returns_fp)\n",
        "\n",
        "# Merge into main DataFrame\n",
        "df = df.merge(\n",
        "    annual_returns[['ticker', 'year', 'annual_return']],\n",
        "    left_on=['instrument', 'year'],\n",
        "    right_on=['ticker', 'year'],\n",
        "    how='left'\n",
        ")\n",
        "\n",
        "print(f'  Merged {df[\"annual_return\"].notna().sum()} annual returns from daily data')\n",
        "print(f'  Coverage: {df[\"annual_return\"].notna().sum() / len(df) * 100:.1f}%')"
    ]
}

# Find cell with id '9aa142b7' (cell 13 - drift calculation)
for i, cell in enumerate(accounting_nb['cells']):
    if cell.get('id') == '9aa142b7':
        print(f"[INFO] Found drift calculation cell at index {i}")
        # Replace the cell source
        cell['source'] = [
            "# Debt and asset volatility proxies\n",
            "df['sigma_D_hat'] = 0.05 + 0.25 * df['sigma_E']\n",
            "df['V_hat'] = df['E'] + df['F']\n",
            "valid_v = df['V_hat'] > 0\n",
            "\n",
            "sigma_V_components = np.where(\n",
            "    valid_v,\n",
            "    (df['E'] / df['V_hat']) * df['sigma_E'] + (df['F'] / df['V_hat']) * df['sigma_D_hat'],\n",
            "    np.nan\n",
            ")\n",
            "df['sigma_V_hat'] = sigma_V_components\n",
            "\n",
            "df['sigma_V_hat'] = df['sigma_V_hat'].clip(lower=1e-6)\n",
            "\n",
            "# Drift proxy using lagged DAILY-DERIVED annual returns (NOT rit)\n",
            "print('[INFO] Computing mu_hat from daily-derived annual returns...')\n",
            "\n",
            "# Use annual_return from daily data, lagged by 1 year\n",
            "lagged_annual_return = df.groupby('instrument', group_keys=False)['annual_return'].shift(1)\n",
            "\n",
            "# Fallback 1: firm-level expanding mean\n",
            "firm_mean = (\n",
            "    df.groupby('instrument', group_keys=False)['annual_return']\n",
            "      .apply(lambda s: s.expanding().mean().shift(1))\n",
            ")\n",
            "\n",
            "# Fallback 2: size bucket median\n",
            "df['mu_hat'] = lagged_annual_return\n",
            "mask_mu = df['mu_hat'].isna()\n",
            "df.loc[mask_mu, 'mu_hat'] = firm_mean[mask_mu]\n",
            "\n",
            "size_median_mu = df.groupby('size_bucket')['mu_hat'].transform('median')\n",
            "df['mu_hat'] = df['mu_hat'].fillna(size_median_mu)\n",
            "\n",
            "# Fallback 3: overall median\n",
            "df['mu_hat'] = df['mu_hat'].fillna(df['mu_hat'].median())\n",
            "\n",
            "# Update provenance tracking\n",
            "df['mu_hat_from'] = 'daily_annual_return_tminus1'\n",
            "df['mu_source_year'] = df['year'] - 1\n",
            "\n",
            "print(f'  mu_hat computed: {df[\"mu_hat\"].notna().sum()} values')\n",
            "print(f'  mu_hat range: [{df[\"mu_hat\"].min():.4f}, {df[\"mu_hat\"].max():.4f}]')\n",
            "print(df[['instrument', 'year', 'sigma_D_hat', 'sigma_V_hat', 'mu_hat']].head())"
        ]
        cell['outputs'] = []
        cell['execution_count'] = None
        
    # Update time integrity assertion cell
    if cell.get('id') == 'time_assertions_accounting':
        print(f"[INFO] Found time assertions cell at index {i}")
        source_text = ''.join(cell['source'])
        # Replace the assertion text
        updated_source = source_text.replace(
            "# Assertion 3: When using rit_tminus1, source year must be t-1\nuses_lag = df['mu_hat_from'].eq('rit_tminus1')",
            "# Assertion 3: When using daily_annual_return_tminus1, source year must be t-1\nuses_lag = df['mu_hat_from'].eq('daily_annual_return_tminus1')"
        )
        cell['source'] = updated_source.split('\n')
        # Add newline to each line except last
        cell['source'] = [line + '\n' if i < len(cell['source'])-1 else line 
                          for i, line in enumerate(cell['source'])]
        cell['outputs'] = []
        cell['execution_count'] = None
    
    # Insert new cell after cell 10
    if cell.get('id') == 'time_tagging_accounting':
        insert_index = i + 1
        print(f"[INFO] Will insert annual returns load cell at index {insert_index}")

# Insert the new cell
accounting_nb['cells'].insert(insert_index, new_cell_after_10)

# Save updated notebook
output_path = base_dir / 'dd_pd_accounting_UPDATED.ipynb'
with open(output_path, 'w') as f:
    json.dump(accounting_nb, f, indent=1)

print(f"\n[SUCCESS] Updated accounting notebook saved to: {output_path}")
print(f"[INFO] Total cells in updated notebook: {len(accounting_nb['cells'])}")
print("\n[NEXT STEPS]")
print("1. Review the updated notebook: dd_pd_accounting_UPDATED.ipynb")
print("2. If satisfied, replace the original:")
print("   mv dd_pd_accounting_UPDATED.ipynb dd_pd_accounting.ipynb")
print("3. Re-run the notebook to generate new DD_a/PD_a values")
