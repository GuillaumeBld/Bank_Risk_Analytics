#!/usr/bin/env python3
"""
Clean up datasheet directory
Keep only essential files, archive timestamped runs
"""

import shutil
from pathlib import Path
from datetime import datetime

datasheet_dir = Path('/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank/data/outputs/datasheet')
archive_dir = Path('/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank/archive/data_archive')

print('='*80)
print('CLEANING UP DATASHEET DIRECTORY')
print('='*80)
print()

# Create archive directory if needed
archive_dir.mkdir(parents=True, exist_ok=True)

# Essential files to keep
essential_files = [
    'accounting.csv',
    'market.csv', 
    'merged.csv',
    'esg_0718.csv'
]

# Files to archive
files_to_archive = []
files_to_remove = []

for f in datasheet_dir.glob('*'):
    if f.name not in essential_files:
        if '_2025' in f.name:
            # Old timestamped runs - archive
            files_to_archive.append(f)
        elif f.name.endswith('_backup.csv'):
            # Keep backup for now (from recent duplicate fix)
            print(f'  Keeping backup: {f.name} (recent fix)')
        elif f.name.endswith('.json'):
            # Keep config files
            print(f'  Keeping config: {f.name}')
        else:
            files_to_remove.append(f)

# Archive old files
print(f'\n1. Archiving old timestamped files: {len(files_to_archive)}')
print('-'*80)
for f in files_to_archive:
    dest = archive_dir / f.name
    print(f'   {f.name} → archive/data_archive/')
    shutil.move(str(f), str(dest))

print(f'\n   ✓ Archived {len(files_to_archive)} files')

# Summary
print()
print('='*80)
print('DATASHEET DIRECTORY STATUS')
print('='*80)
print()
print('Essential files (kept):')
for f in essential_files:
    if (datasheet_dir / f).exists():
        size = (datasheet_dir / f).stat().st_size / 1024
        print(f'  ✓ {f:<30} {size:>8.1f} KB')

print()
remaining = list(datasheet_dir.glob('*'))
print(f'Total files in directory: {len(remaining)}')
print()
print('Directory is now clean and organized!')
print('='*80)
