#!/usr/bin/env python3
"""
Smart Archiving System for DD/PD Datasets

Automatically archives old files when new ones are created, with dependency tracking:
- When accounting is updated → archive old accounting files AND old merged/esg_dd_pd files
- When market is updated → archive old market files AND old merged/esg_dd_pd files
- When merging is run → archive old merged/esg_dd_pd files only

This ensures downstream files are always regenerated when upstream data changes.
"""

import shutil
import glob
import os
from pathlib import Path
from datetime import datetime
import pytz

def get_timestamp_cdt():
    """Generate timestamp in YYYYMMDD_HHMMSS format (CDT timezone)"""
    cdt = pytz.timezone('America/Chicago')
    return datetime.now(cdt).strftime('%Y%m%d_%H%M%S')

def archive_files_by_pattern(output_dir, archive_dir, pattern, max_keep=5, reason=""):
    """
    Archive all files matching pattern, keeping only max_keep most recent in archive.
    
    Args:
        output_dir: Directory containing active files
        pattern: Glob pattern (e.g., "accounting_*.csv")
        max_keep: Maximum number of files to keep in archive
        reason: Reason for archiving (for logging)
    """
    full_pattern = str(output_dir / pattern)
    files = sorted(glob.glob(full_pattern), key=lambda x: os.path.getmtime(x), reverse=True)
    
    if not files:
        return 0
    
    archived_count = 0
    reason_msg = f" ({reason})" if reason else ""
    
    # Move all matching files to archive
    for file_path in files:
        filename = os.path.basename(file_path)
        archive_path = archive_dir / filename
        
        # If file already exists in archive, add timestamp to avoid overwrite
        if archive_path.exists():
            base = archive_path.stem
            ext = archive_path.suffix
            archive_path = archive_dir / f"{base}_archived_{get_timestamp_cdt()}{ext}"
        
        shutil.move(file_path, str(archive_path))
        print(f"[ARCHIVE] {filename} → archive/{reason_msg}")
        archived_count += 1
    
    # Clean up archive to keep only max_keep files
    archive_pattern = str(archive_dir / pattern)
    archive_files = sorted(glob.glob(archive_pattern), key=lambda x: os.path.getmtime(x), reverse=True)
    
    for old_file in archive_files[max_keep:]:
        os.remove(old_file)
        print(f"[CLEANUP] Removed old archive: {os.path.basename(old_file)}")
    
    return archived_count

def archive_on_accounting_update(output_dir, archive_dir, max_keep=5):
    """
    Archive old files when accounting dataset is updated.
    Archives: old accounting files AND all downstream merged/esg_dd_pd files
    """
    print("\n[INFO] Archiving due to accounting update...")
    
    # Archive old accounting files
    count = archive_files_by_pattern(
        output_dir, archive_dir, 
        "accounting_*.csv", 
        max_keep, 
        "old accounting"
    )
    
    # Archive ALL merged files (they're now outdated)
    count += archive_files_by_pattern(
        output_dir, archive_dir,
        "merged_*.csv",
        max_keep,
        "outdated - accounting changed"
    )
    
    # Archive ALL esg_dd_pd files (they're now outdated)
    count += archive_files_by_pattern(
        output_dir, archive_dir,
        "esg_dd_pd_*.csv",
        max_keep,
        "outdated - accounting changed"
    )
    
    print(f"[INFO] Archived {count} files total")
    return count

def archive_on_market_update(output_dir, archive_dir, max_keep=5):
    """
    Archive old files when market dataset is updated.
    Archives: old market files AND all downstream merged/esg_dd_pd files
    """
    print("\n[INFO] Archiving due to market update...")
    
    # Archive old market files
    count = archive_files_by_pattern(
        output_dir, archive_dir,
        "market_*.csv",
        max_keep,
        "old market"
    )
    
    # Archive ALL merged files (they're now outdated)
    count += archive_files_by_pattern(
        output_dir, archive_dir,
        "merged_*.csv",
        max_keep,
        "outdated - market changed"
    )
    
    # Archive ALL esg_dd_pd files (they're now outdated)
    count += archive_files_by_pattern(
        output_dir, archive_dir,
        "esg_dd_pd_*.csv",
        max_keep,
        "outdated - market changed"
    )
    
    print(f"[INFO] Archived {count} files total")
    return count

def archive_on_merge_update(output_dir, archive_dir, max_keep=5):
    """
    Archive old files when merged dataset is created.
    Archives: old merged and esg_dd_pd files only (accounting/market unchanged)
    """
    print("\n[INFO] Archiving due to merge update...")
    
    # Archive old merged files
    count = archive_files_by_pattern(
        output_dir, archive_dir,
        "merged_*.csv",
        max_keep,
        "old merged"
    )
    
    # Archive old esg_dd_pd files
    count += archive_files_by_pattern(
        output_dir, archive_dir,
        "esg_dd_pd_*.csv",
        max_keep,
        "old esg_dd_pd"
    )
    
    print(f"[INFO] Archived {count} files total")
    return count

# Convenience functions for notebook integration
def setup_archiving(base_dir):
    """Setup archive directory and return paths"""
    output_dir = Path(base_dir) / 'data' / 'outputs' / 'datasheet'
    archive_dir = Path(base_dir) / 'archive' / 'datasets'
    archive_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, archive_dir

if __name__ == '__main__':
    # Test the archiving system
    from pathlib import Path
    
    def find_repo_root(start: Path, marker: str = '.git') -> Path:
        current = start.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / marker).exists():
                return candidate
        return current
    
    base_dir = find_repo_root(Path.cwd())
    output_dir, archive_dir = setup_archiving(base_dir)
    
    print(f"Output directory: {output_dir}")
    print(f"Archive directory: {archive_dir}")
    print("\nCurrent files:")
    for f in sorted(output_dir.glob("*.csv")):
        print(f"  {f.name}")
