#!/usr/bin/env python3
"""
Update all three notebooks with smart archiving system
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

# Smart archiving import code to add after base imports
smart_archiving_import = [
    "# Import smart archiving system\n",
    "import sys\n",
    "from pathlib import Path\n",
    "sys.path.insert(0, str(Path.cwd() / 'scripts'))\n",
    "from smart_archiving import (\n",
    "    archive_on_accounting_update,\n",
    "    archive_on_market_update,\n",
    "    archive_on_merge_update,\n",
    "    setup_archiving\n",
    ")\n",
    "\n",
    "# Setup archiving paths\n",
    "output_dir, archive_dir = setup_archiving(base_dir)\n"
]

def update_accounting_notebook():
    """Update dd_pd_accounting.ipynb with smart archiving"""
    nb_path = base_dir / 'dd_pd_accounting.ipynb'
    
    with open(nb_path, 'r') as f:
        nb = json.load(f)
    
    print(f"[INFO] Updating {nb_path.name}...")
    
    # Find the cell that saves output (cell with 'archive_old_files')
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Replace archive_old_files call
            if 'archive_old_files(output_dir, archive_dir, \'accounting\'' in source:
                print(f"  Found archiving cell at index {i}")
                
                # Replace the archiving line
                new_source = source.replace(
                    "archive_old_files(output_dir, archive_dir, 'accounting', max_keep=5)",
                    "# Archive old accounting files AND downstream merged/esg_dd_pd files\n"
                    "# (they become outdated when accounting changes)\n"
                    "archive_on_accounting_update(output_dir, archive_dir, max_keep=5)"
                )
                
                cell['source'] = new_source.split('\n')
                cell['source'] = [line + '\n' if i < len(cell['source'])-1 else line 
                                  for i, line in enumerate(cell['source'])]
                cell['outputs'] = []
                cell['execution_count'] = None
                print("  Updated archiving call")
    
    # Save updated notebook
    with open(nb_path, 'w') as f:
        json.dump(nb, f, indent=1)
    
    print(f"[SUCCESS] Updated {nb_path.name}")

def update_market_notebook():
    """Update dd_pd_market.ipynb with smart archiving"""
    nb_path = base_dir / 'dd_pd_market.ipynb'
    
    if not nb_path.exists():
        print(f"[SKIP] {nb_path.name} not found")
        return
    
    with open(nb_path, 'r') as f:
        nb = json.load(f)
    
    print(f"\n[INFO] Updating {nb_path.name}...")
    
    # Find archiving cells
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Look for archiving code (might be different patterns)
            if 'archive_old_files' in source or ('archive' in source and 'market' in source):
                print(f"  Found potential archiving cell at index {i}")
                
                # Replace with smart archiving
                if 'market' in source.lower():
                    new_source = (
                        "# Archive old market files AND downstream merged/esg_dd_pd files\n"
                        "# (they become outdated when market changes)\n"
                        "archive_on_market_update(output_dir, archive_dir, max_keep=5)\n"
                    )
                    
                    cell['source'] = new_source.split('\n')
                    cell['source'] = [line + '\n' if i < len(cell['source'])-1 else line 
                                      for i, line in enumerate(cell['source'])]
                    cell['outputs'] = []
                    cell['execution_count'] = None
                    print("  Updated archiving call")
    
    # Save updated notebook
    with open(nb_path, 'w') as f:
        json.dump(nb, f, indent=1)
    
    print(f"[SUCCESS] Updated {nb_path.name}")

def update_merging_notebook():
    """Update merging.ipynb with smart archiving"""
    nb_path = base_dir / 'merging.ipynb'
    
    with open(nb_path, 'r') as f:
        nb = json.load(f)
    
    print(f"\n[INFO] Updating {nb_path.name}...")
    
    # Find archiving cells
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Replace merged archiving
            if 'archive_old_files(output_dir, archive_dir, \'merged\'' in source:
                print(f"  Found merged archiving cell at index {i}")
                
                new_source = source.replace(
                    "archive_old_files(output_dir, archive_dir, 'merged', max_keep=5)",
                    "# Archive old merged and esg_dd_pd files\n"
                    "# (accounting/market files are unchanged)\n"
                    "archive_on_merge_update(output_dir, archive_dir, max_keep=5)"
                )
                
                cell['source'] = new_source.split('\n')
                cell['source'] = [line + '\n' if i < len(cell['source'])-1 else line 
                                  for i, line in enumerate(cell['source'])]
                cell['outputs'] = []
                cell['execution_count'] = None
                print("  Updated merged archiving")
            
            # Remove separate esg_dd_pd archiving (now handled by archive_on_merge_update)
            if 'archive_old_files(output_dir, archive_dir, \'esg_dd_pd\'' in source:
                print(f"  Found esg_dd_pd archiving cell at index {i}")
                
                new_source = source.replace(
                    "archive_old_files(output_dir, archive_dir, 'esg_dd_pd', max_keep=5)",
                    "# (Already archived by archive_on_merge_update above)"
                )
                
                cell['source'] = new_source.split('\n')
                cell['source'] = [line + '\n' if i < len(cell['source'])-1 else line 
                                  for i, line in enumerate(cell['source'])]
                cell['outputs'] = []
                cell['execution_count'] = None
                print("  Removed redundant esg_dd_pd archiving")
    
    # Save updated notebook
    with open(nb_path, 'w') as f:
        json.dump(nb, f, indent=1)
    
    print(f"[SUCCESS] Updated {nb_path.name}")

if __name__ == '__main__':
    print("=" * 60)
    print("UPDATING NOTEBOOKS WITH SMART ARCHIVING SYSTEM")
    print("=" * 60)
    
    update_accounting_notebook()
    update_market_notebook()
    update_merging_notebook()
    
    print("\n" + "=" * 60)
    print("ALL NOTEBOOKS UPDATED")
    print("=" * 60)
    print("\n[NEXT STEPS]")
    print("1. Review the updated notebooks")
    print("2. Re-run accounting notebook → archives old accounting + merged + esg_dd_pd")
    print("3. Re-run merging notebook → archives old merged + esg_dd_pd")
    print("4. Old files automatically archived, no manual cleanup needed!")
