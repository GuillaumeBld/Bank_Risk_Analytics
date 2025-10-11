#!/usr/bin/env python3
"""
Fix merging notebook to remove unnamed columns and ensure clean merges
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
merge_nb_path = base_dir / 'merging.ipynb'

print("="*80)
print("FIXING MERGING NOTEBOOK - REMOVING UNNAMED COLUMNS")
print("="*80)

with open(merge_nb_path, 'r') as f:
    merge_nb = json.load(f)

# Find the merge cell and add unnamed column cleanup
for i, cell in enumerate(merge_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Fix the main merge cell
        if "df_merged = pd.merge(" in source and "suffixes=('_a', '_m')" in source:
            print(f"Found merge cell at index {i}")
            
            new_source = [
                "# Merge datasets on instrument and year\n",
                "merge_keys = ['instrument', 'year']\n",
                "\n",
                "# Add prefixes to distinguish variables (except merge keys and final DD/PD)\n",
                "accounting_cols_to_prefix = [c for c in df_accounting.columns \n",
                "                             if c not in merge_keys + ['DD_a', 'PD_a']]\n",
                "market_cols_to_prefix = [c for c in df_market.columns \n",
                "                         if c not in merge_keys + ['DD_m', 'PD_m']]\n",
                "\n",
                "df_accounting_prefixed = df_accounting.rename(\n",
                "    columns={c: f'a_{c}' for c in accounting_cols_to_prefix}\n",
                ")\n",
                "df_market_prefixed = df_market.rename(\n",
                "    columns={c: f'm_{c}' for c in market_cols_to_prefix}\n",
                ")\n",
                "\n",
                "# Perform outer merge to keep all observations\n",
                "df_merged = pd.merge(\n",
                "    df_accounting_prefixed,\n",
                "    df_market_prefixed,\n",
                "    on=merge_keys,\n",
                "    how='outer',\n",
                "    suffixes=('_a', '_m')\n",
                ")\n",
                "\n",
                "# Clean up: Remove any unnamed columns\n",
                "unnamed_cols = [col for col in df_merged.columns if col.startswith('Unnamed')]\n",
                "if unnamed_cols:\n",
                "    print(f'[WARN] Dropping {len(unnamed_cols)} unnamed columns: {unnamed_cols[:5]}...')\n",
                "    df_merged = df_merged.drop(columns=unnamed_cols)\n",
                "\n",
                "# Remove duplicate columns (keep first occurrence)\n",
                "df_merged = df_merged.loc[:, ~df_merged.columns.duplicated()]\n",
                "\n",
                "print(f\"Merged dataset: {len(df_merged)} rows\")\n",
                "print(f\"\\nColumn count:\")\n",
                "print(f\"  Accounting: {len(df_accounting.columns)}\")\n",
                "print(f\"  Market: {len(df_market.columns)}\")\n",
                "print(f\"  Merged: {len(df_merged.columns)}\")\n",
                "\n",
                "# Show sample\n",
                "print(f\"\\nSample merged data:\")\n",
                "display(df_merged[['instrument', 'year', 'DD_a', 'PD_a', 'DD_m', 'PD_m']].head(10))\n"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added unnamed column cleanup to merge cell")
            
        # Fix the ESG merge cell
        elif "df_esg_dd = pd.merge(" in source and "df_esg," in source:
            print(f"Found ESG merge cell at index {i}")
            
            new_source = [
                "# Create ESG dataset with DD/PD columns appended\n",
                "print('[INFO] Creating ESG dataset with DD/PD columns...')\n",
                "\n",
                "# Load ESG data\n",
                "esg_file = base_dir / 'data' / 'outputs' / 'datasheet' / 'esg_0718.csv'\n",
                "if not esg_file.exists():\n",
                "    # Try alternate location\n",
                "    esg_file = base_dir / 'data' / 'esg_0718.csv'\n",
                "\n",
                "if not esg_file.exists():\n",
                "    print(f'[ERROR] ESG file not found: {esg_file}')\n",
                "else:\n",
                "    df_esg = pd.read_csv(esg_file)\n",
                "    \n",
                "    # Clean up ESG file: remove any unnamed columns\n",
                "    unnamed_cols = [col for col in df_esg.columns if col.startswith('Unnamed')]\n",
                "    if unnamed_cols:\n",
                "        print(f'  [WARN] Dropping {len(unnamed_cols)} unnamed columns from ESG file')\n",
                "        df_esg = df_esg.drop(columns=unnamed_cols)\n",
                "    \n",
                "    print(f'  Loaded ESG data: {len(df_esg)} rows, {len(df_esg.columns)} columns')\n",
                "    \n",
                "    # Extract DD/PD columns from merged dataset\n",
                "    dd_pd_data = df_merged[['instrument', 'year', 'DD_a', 'PD_a', 'DD_m', 'PD_m']].copy()\n",
                "    \n",
                "    # Merge ESG data with DD/PD\n",
                "    df_esg_dd = pd.merge(\n",
                "        df_esg,\n",
                "        dd_pd_data,\n",
                "        on=['instrument', 'year'],\n",
                "        how='left'\n",
                "    )\n",
                "    \n",
                "    # Final cleanup: remove any unnamed columns that appeared during merge\n",
                "    unnamed_cols = [col for col in df_esg_dd.columns if col.startswith('Unnamed')]\n",
                "    if unnamed_cols:\n",
                "        print(f'  [WARN] Dropping {len(unnamed_cols)} unnamed columns after merge')\n",
                "        df_esg_dd = df_esg_dd.drop(columns=unnamed_cols)\n",
                "    \n",
                "    # Remove duplicate columns (keep first)\n",
                "    df_esg_dd = df_esg_dd.loc[:, ~df_esg_dd.columns.duplicated()]\n",
                "    \n",
                "    print(f'  Merged ESG+DD/PD: {len(df_esg_dd)} rows, {len(df_esg_dd.columns)} columns')\n",
                "    print(f'  New columns: DD_a, PD_a, DD_m, PD_m')\n",
                "    \n",
                "    # Archive old ESG+DD files\n",
                "    archive_old_files(output_dir, archive_dir, 'esg_dd_pd', max_keep=5)\n",
                "    \n",
                "    # Save with timestamp\n",
                "    esg_output = output_dir / f'esg_dd_pd_{timestamp}.csv'\n",
                "    df_esg_dd.to_csv(esg_output, index=False)\n",
                "    \n",
                "    print(f'\\n[INFO] ESG+DD/PD dataset saved to: {esg_output}')\n",
                "    print(f'[INFO] Sample data:')\n",
                "    display(df_esg_dd[['instrument', 'year', 'lnta', 'esg_score', 'DD_a', 'PD_a', 'DD_m', 'PD_m']].head(10))\n"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Added unnamed column cleanup to ESG merge cell")

with open(merge_nb_path, 'w') as f:
    json.dump(merge_nb, f, indent=1)

print("\n✅ Saved fixed merging notebook")
print("\n" + "="*80)
print("FIXES APPLIED:")
print("1. Remove 'Unnamed' columns after main merge")
print("2. Remove duplicate columns")
print("3. Clean ESG file before merging")
print("4. Remove 'Unnamed' columns after ESG merge")
print("\n" + "="*80)
print("NEXT: Re-run merging.ipynb after DD notebooks complete")
print("="*80)
