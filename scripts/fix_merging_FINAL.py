#!/usr/bin/env python3
"""
FINAL FIX: Clean ESG file, prevent duplicates, rename columns properly
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
merge_nb_path = base_dir / 'merging.ipynb'

print("="*80)
print("FINAL MERGING NOTEBOOK FIX")
print("="*80)

with open(merge_nb_path, 'r') as f:
    merge_nb = json.load(f)

# Find the ESG merge cell and replace it completely
for i, cell in enumerate(merge_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the ESG merge cell
        if "df_esg_dd = pd.merge(" in source and "df_esg," in source:
            print(f"Found ESG merge cell at index {i}")
            
            # Replace with complete clean version
            new_source = [
                "# Create ESG dataset with DD/PD columns appended\n",
                "print('[INFO] Creating ESG dataset with DD/PD columns...')\n",
                "\n",
                "# Load ESG data\n",
                "esg_file = base_dir / 'data' / 'outputs' / 'datasheet' / 'esg_0718.csv'\n",
                "if not esg_file.exists():\n",
                "    esg_file = base_dir / 'data' / 'esg_0718.csv'\n",
                "\n",
                "if not esg_file.exists():\n",
                "    print(f'[ERROR] ESG file not found: {esg_file}')\n",
                "else:\n",
                "    df_esg = pd.read_csv(esg_file)\n",
                "    \n",
                "    # CRITICAL: Remove old DD/PD columns from ESG file if they exist\n",
                "    old_cols = ['DD_a', 'PD_a', 'DD_m', 'PD_m', 'status']\n",
                "    old_cols_found = [col for col in old_cols if col in df_esg.columns]\n",
                "    if old_cols_found:\n",
                "        print(f'  [WARN] Removing old DD/PD columns from ESG: {old_cols_found}')\n",
                "        df_esg = df_esg.drop(columns=old_cols_found)\n",
                "    \n",
                "    # Clean up any unnamed columns\n",
                "    unnamed_cols = [col for col in df_esg.columns if col.startswith('Unnamed')]\n",
                "    if unnamed_cols:\n",
                "        print(f'  [WARN] Dropping {len(unnamed_cols)} unnamed columns from ESG')\n",
                "        df_esg = df_esg.drop(columns=unnamed_cols)\n",
                "    \n",
                "    print(f'  Loaded ESG data: {len(df_esg)} rows, {len(df_esg.columns)} columns')\n",
                "    \n",
                "    # Extract DD/PD columns from merged dataset\n",
                "    dd_pd_data = df_merged[['instrument', 'year', 'DD_a', 'PD_a', 'DD_m', 'PD_m']].copy()\n",
                "    \n",
                "    # Remove duplicates from DD/PD data (keep first occurrence)\n",
                "    before_dedup = len(dd_pd_data)\n",
                "    dd_pd_data = dd_pd_data.drop_duplicates(subset=['instrument', 'year'], keep='first')\n",
                "    after_dedup = len(dd_pd_data)\n",
                "    if before_dedup > after_dedup:\n",
                "        print(f'  [INFO] Removed {before_dedup - after_dedup} duplicate DD/PD rows')\n",
                "    \n",
                "    # Merge ESG data with DD/PD (now clean, no conflicts)\n",
                "    df_esg_dd = pd.merge(\n",
                "        df_esg,\n",
                "        dd_pd_data,\n",
                "        on=['instrument', 'year'],\n",
                "        how='left'\n",
                "    )\n",
                "    \n",
                "    # Final cleanup: remove any unnamed columns\n",
                "    unnamed_cols = [col for col in df_esg_dd.columns if col.startswith('Unnamed')]\n",
                "    if unnamed_cols:\n",
                "        print(f'  [WARN] Dropping {len(unnamed_cols)} unnamed columns after merge')\n",
                "        df_esg_dd = df_esg_dd.drop(columns=unnamed_cols)\n",
                "    \n",
                "    # Remove duplicate rows (keep first)\n",
                "    before_dedup = len(df_esg_dd)\n",
                "    df_esg_dd = df_esg_dd.drop_duplicates(subset=['instrument', 'year'], keep='first')\n",
                "    after_dedup = len(df_esg_dd)\n",
                "    if before_dedup > after_dedup:\n",
                "        print(f'  [INFO] Removed {before_dedup - after_dedup} duplicate rows from final dataset')\n",
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
                "    \n",
                "    # Display only columns that exist\n",
                "    display_cols = ['instrument', 'year']\n",
                "    for col in ['lnta', 'esg_score', 'DD_a', 'PD_a', 'DD_m', 'PD_m']:\n",
                "        if col in df_esg_dd.columns:\n",
                "            display_cols.append(col)\n",
                "    display(df_esg_dd[display_cols].head(10))\n"
            ]
            
            cell['source'] = new_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Replaced ESG merge cell with clean version")
            break

with open(merge_nb_path, 'w') as f:
    json.dump(merge_nb, f, indent=1)

print("✅ Saved fixed merging notebook")
print("\n" + "="*80)
print("FINAL FIX APPLIED:")
print("1. Remove old DD/PD columns from ESG file BEFORE merge")
print("2. Remove duplicates from DD/PD data")
print("3. Merge cleanly (no _x/_y suffixes)")
print("4. Remove duplicate rows from final result")
print("5. Columns named: DD_a, PD_a, DD_m, PD_m (clean names!)")
print("\n" + "="*80)
print("NEXT: Re-run merging.ipynb")
print("Expected: Clean output with DD_a, DD_m, PD_a, PD_m columns")
print("No _x/_y suffixes, no duplicates!")
print("="*80)
