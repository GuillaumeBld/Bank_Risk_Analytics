#!/usr/bin/env python3
"""
Fix duplicate rows in esg_0718.csv
Removes duplicate instrument-year combinations, keeping the first occurrence.
"""

import pandas as pd
from pathlib import Path

# Paths
data_dir = Path(__file__).parent / 'data/outputs/datasheet'
input_file = data_dir / 'esg_0718.csv'
output_file = data_dir / 'esg_0718.csv'
backup_file = data_dir / 'esg_0718_backup.csv'

print("="*80)
print("FIX DUPLICATES IN esg_0718.csv")
print("="*80)

# Load data
print(f"\n1. Loading: {input_file.name}")
df = pd.read_csv(input_file)
print(f"   Original rows: {len(df)}")

# Check for duplicates
duplicates_before = df.duplicated(subset=['instrument', 'year'], keep=False).sum()
print(f"   Duplicate rows: {duplicates_before}")

# Identify specific duplicates
if duplicates_before > 0:
    dup_groups = df[df.duplicated(subset=['instrument', 'year'], keep=False)]
    print(f"\n2. Duplicate instrument-year combinations:")
    for (inst, year), group in dup_groups.groupby(['instrument', 'year']):
        print(f"   {inst} {year}: {len(group)} rows")

# Backup original file
print(f"\n3. Creating backup: {backup_file.name}")
df.to_csv(backup_file, index=False)
print(f"   ✓ Backup saved")

# Remove duplicates (keep first occurrence)
print(f"\n4. Removing duplicates...")
df_clean = df.drop_duplicates(subset=['instrument', 'year'], keep='first')
rows_removed = len(df) - len(df_clean)
print(f"   Removed: {rows_removed} duplicate rows")
print(f"   Clean rows: {len(df_clean)}")

# Verify no duplicates remain
duplicates_after = df_clean.duplicated(subset=['instrument', 'year']).sum()
assert duplicates_after == 0, f"ERROR: {duplicates_after} duplicates still remain!"
print(f"   ✓ Verified: No duplicates remain")

# Save cleaned data
print(f"\n5. Saving cleaned data: {output_file.name}")
df_clean.to_csv(output_file, index=False)
print(f"   ✓ Saved successfully")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Original rows:    {len(df)}")
print(f"Duplicates found: {duplicates_before}")
print(f"Rows removed:     {rows_removed}")
print(f"Final rows:       {len(df_clean)}")
print(f"\nBackup saved to:  {backup_file}")
print(f"Clean data saved: {output_file}")
print("\n✓ COMPLETE - Dataset is now clean!")
print("="*80)
