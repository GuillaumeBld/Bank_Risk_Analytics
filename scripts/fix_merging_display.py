#!/usr/bin/env python3
"""
Fix merging notebook to handle missing DD columns gracefully
"""

import json
from pathlib import Path

base_dir = Path(__file__).parent.parent
merge_nb_path = base_dir / 'merging.ipynb'

print("="*80)
print("FIXING MERGING NOTEBOOK DISPLAY")
print("="*80)

with open(merge_nb_path, 'r') as f:
    merge_nb = json.load(f)

# Find the ESG display cell
for i, cell in enumerate(merge_nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find the cell with ESG display
        if "display(df_esg_dd[['instrument', 'year', 'lnta', 'esg_score', 'DD_a', 'PD_a', 'DD_m', 'PD_m']]" in source:
            print(f"Found ESG display cell at index {i}")
            
            # Replace the display line with a safer version
            source_lines = cell['source']
            
            # Replace the problematic line
            new_source = []
            for line in source_lines:
                if "display(df_esg_dd[['instrument', 'year', 'lnta', 'esg_score', 'DD_a', 'PD_a', 'DD_m', 'PD_m']]" in line:
                    # Replace with safer version
                    new_source.append("    # Display sample (only columns that exist)\n")
                    new_source.append("    display_cols = ['instrument', 'year']\n")
                    new_source.append("    for col in ['lnta', 'esg_score', 'DD_a', 'PD_a', 'DD_m', 'PD_m']:\n")
                    new_source.append("        if col in df_esg_dd.columns:\n")
                    new_source.append("            display_cols.append(col)\n")
                    new_source.append("    display(df_esg_dd[display_cols].head(10))\n")
                else:
                    new_source.append(line)
            
            cell['source'] = new_source
            cell['outputs'] = []
            cell['execution_count'] = None
            print("✅ Fixed ESG display to handle missing columns")
            break

with open(merge_nb_path, 'w') as f:
    json.dump(merge_nb, f, indent=1)

print("✅ Saved fixed merging notebook")
print("\n" + "="*80)
print("FIX APPLIED:")
print("  - Display will now only show columns that exist")
print("  - Won't crash if DD columns are missing")
print("\n" + "="*80)
print("NOTE: This is a temporary fix.")
print("The real fix is to successfully run the DD notebooks first!")
print("="*80)
