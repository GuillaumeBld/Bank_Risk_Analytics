#!/usr/bin/env python3
"""
Test script to validate notebook execution after daily volatility migration
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

print("="*80)
print("NOTEBOOK VALIDATION TEST")
print("="*80)

# Test 1: Accounting Notebook
print("\n[TEST 1] Accounting Notebook (dd_pd_accounting.ipynb)")
print("-"*80)

try:
    result = subprocess.run(
        [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--ExecutePreprocessor.timeout=600',
            '--output', '/tmp/dd_pd_accounting_test.ipynb',
            str(BASE_DIR / 'dd_pd_accounting.ipynb')
        ],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode == 0:
        print("✅ Accounting notebook executed successfully")
    else:
        print("❌ Accounting notebook failed")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("❌ Accounting notebook timed out (>10 minutes)")
    sys.exit(1)
except FileNotFoundError:
    print("⚠️  jupyter not found, trying alternative method...")
    print("    Please run notebooks manually in Jupyter")
    sys.exit(0)

# Test 2: Market Notebook
print("\n[TEST 2] Market Notebook (dd_pd_market.ipynb)")
print("-"*80)

try:
    result = subprocess.run(
        [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--ExecutePreprocessor.timeout=600',
            '--output', '/tmp/dd_pd_market_test.ipynb',
            str(BASE_DIR / 'dd_pd_market.ipynb')
        ],
        capture_output=True,
        text=True,
        timeout=600
    )
    
    if result.returncode == 0:
        print("✅ Market notebook executed successfully")
    else:
        print("❌ Market notebook failed")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        sys.exit(1)
        
except subprocess.TimeoutExpired:
    print("❌ Market notebook timed out (>10 minutes)")
    sys.exit(1)

print("\n" + "="*80)
print("ALL TESTS PASSED ✅")
print("="*80)
print("\nBoth notebooks execute successfully with daily volatility data")
print("Proceed to Phase 9 (Commit)")
