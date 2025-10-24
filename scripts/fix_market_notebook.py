#!/usr/bin/env python3
"""Fix market notebook with proper smart archiving import"""

import json
from pathlib import Path

# Load market notebook
nb_path = Path('dd_pd_market.ipynb')
with open(nb_path, 'r') as f:
    nb = json.load(f)

print(f'[INFO] Loaded {nb_path.name} with {len(nb["cells"])} cells')

# Find and remove the misplaced archiving cell (cell index 4)
cells_to_remove = []
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'archive_on_market_update' in source and i < 10:
            print(f'[INFO] Found misplaced archiving call at cell {i}')
            cells_to_remove.append(i)

# Remove in reverse order
for i in reversed(cells_to_remove):
    print(f'[INFO] Removing cell at index {i}')
    nb['cells'].pop(i)

# Find base_dir setup cell
setup_cell_index = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'def find_repo_root' in source and 'base_dir = find_repo_root' in source:
            setup_cell_index = i
            print(f'[INFO] Found base_dir setup at cell {i}')
            break

if setup_cell_index is not None:
    # Add import cell after base_dir setup
    import_cell = {
        'cell_type': 'code',
        'execution_count': None,
        'id': 'smart_archiving_import',
        'metadata': {},
        'outputs': [],
        'source': [
            '# Import smart archiving system\n',
            'import sys\n',
            'sys.path.insert(0, str(base_dir / "scripts"))\n',
            'from smart_archiving import (\n',
            '    archive_on_market_update,\n',
            '    setup_archiving\n',
            ')\n',
            '\n',
            '# Setup archiving paths\n',
            'output_dir, archive_dir = setup_archiving(base_dir)\n',
            'print(f"Output directory: {output_dir}")\n',
            'print(f"Archive directory: {archive_dir}")'
        ]
    }
    
    nb['cells'].insert(setup_cell_index + 1, import_cell)
    print(f'[INFO] Added import cell at index {setup_cell_index + 1}')
    
    # Find the export cell (near end) and add archiving before save
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'to_csv' in source and 'market' in source.lower() and i > 15:
                # Add archiving call at start of this cell
                lines = cell['source']
                new_lines = [
                    '# Archive old market files AND downstream merged/esg_dd_pd files\n',
                    '# (they become outdated when market changes)\n',
                    'archive_on_market_update(output_dir, archive_dir, max_keep=5)\n',
                    '\n'
                ] + lines
                cell['source'] = new_lines
                cell['outputs'] = []
                cell['execution_count'] = None
                print(f'[INFO] Added archiving call to export cell at index {i}')
                break

# Save updated notebook
with open(nb_path, 'w') as f:
    json.dump(nb, f, indent=1)

print(f'[SUCCESS] Updated {nb_path.name}')
print(f'[INFO] Total cells: {len(nb["cells"])}')
print('\n[NEXT] Restart kernel and run all cells in market notebook')
