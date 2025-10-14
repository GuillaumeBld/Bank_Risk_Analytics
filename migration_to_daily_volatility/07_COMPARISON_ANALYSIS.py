#!/usr/bin/env python3
"""
Comparison Analysis: Old (Annual) vs New (Daily) Volatility
============================================================

Generates comprehensive comparison between 3-year annual method
and new 252-day daily method.

Run this AFTER both notebooks have been updated and run.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'data/outputs/analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("COMPARISON ANALYSIS: OLD VS NEW VOLATILITY")
print("="*80)

# ============================================================================
# Load Data
# ============================================================================

print("\n[1] Loading data...")
print("-"*80)

# Load new daily volatility
vol_daily_path = BASE_DIR / 'data/clean/equity_volatility_by_year_DAILY.csv'
vol_daily = pd.read_csv(vol_daily_path)
print(f"✓ Daily volatility: {len(vol_daily)} rows")

# Load old annual volatility (if exists)
vol_annual_path = BASE_DIR / 'data/clean/equity_volatility_by_year.csv'
if vol_annual_path.exists():
    vol_annual = pd.read_csv(vol_annual_path)
    
    # Standardize column names
    if 'symbol' in vol_annual.columns:
        vol_annual = vol_annual.rename(columns={'symbol': 'ticker'})
    if 'equity_volatility' in vol_annual.columns:
        vol_annual = vol_annual.rename(columns={'equity_volatility': 'sigma_E'})
    
    print(f"✓ Annual volatility: {len(vol_annual)} rows")
    has_old = True
else:
    print("⚠️  No old volatility file found (OK for first migration)")
    has_old = False

# ============================================================================
# Volatility Comparison
# ============================================================================

if has_old:
    print("\n[2] Comparing volatility methods...")
    print("-"*80)
    
    # Standardize column names for merge
    vol_annual_merge = vol_annual.rename(columns={'ticker_base': 'ticker'})
    
    # Merge
    comparison = vol_daily.merge(
        vol_annual_merge[['ticker', 'year', 'sigma_E']],
        on=['ticker', 'year'],
        how='inner',
        suffixes=('_daily', '_annual')
    )
    
    print(f"\nOverlapping observations: {len(comparison)}")
    
    # Statistics
    comparison['delta'] = comparison['sigma_E_daily'] - comparison['sigma_E_annual']
    comparison['delta_pct'] = (comparison['delta'] / comparison['sigma_E_annual']) * 100
    comparison['higher_daily'] = comparison['sigma_E_daily'] > comparison['sigma_E_annual']
    
    print("\n" + "="*80)
    print("VOLATILITY COMPARISON STATISTICS")
    print("="*80)
    
    print("\n[Overall Statistics]")
    print(f"  Annual Method:")
    print(f"    Mean: {comparison['sigma_E_annual'].mean():.3f}")
    print(f"    Median: {comparison['sigma_E_annual'].median():.3f}")
    print(f"    Std: {comparison['sigma_E_annual'].std():.3f}")
    
    print(f"\n  Daily Method:")
    print(f"    Mean: {comparison['sigma_E_daily'].mean():.3f}")
    print(f"    Median: {comparison['sigma_E_daily'].median():.3f}")
    print(f"    Std: {comparison['sigma_E_daily'].std():.3f}")
    
    print(f"\n[Changes]")
    print(f"  Mean difference: {comparison['delta'].mean():.3f}")
    print(f"  Mean % change: {comparison['delta_pct'].mean():.1f}%")
    print(f"  Median % change: {comparison['delta_pct'].median():.1f}%")
    
    print(f"\n[Direction]")
    higher_pct = comparison['higher_daily'].mean() * 100
    print(f"  Daily higher: {comparison['higher_daily'].sum()} ({higher_pct:.1f}%)")
    print(f"  Daily lower: {(~comparison['higher_daily']).sum()} ({100-higher_pct:.1f}%)")
    
    print(f"\n[Correlation]")
    corr = comparison[['sigma_E_annual', 'sigma_E_daily']].corr().iloc[0, 1]
    print(f"  Pearson correlation: {corr:.4f}")
    
    # By year
    print("\n[Changes by Year]")
    year_stats = comparison.groupby('year').agg({
        'delta': 'mean',
        'delta_pct': 'mean',
        'higher_daily': lambda x: x.sum() / len(x) * 100
    })
    year_stats.columns = ['Avg Δ', 'Avg Δ%', '% Higher']
    print(year_stats.to_string())
    
    # ========================================================================
    # Visualizations
    # ========================================================================
    
    print("\n[3] Creating visualizations...")
    print("-"*80)
    
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # Plot 1: Scatter plot
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.scatter(comparison['sigma_E_annual'], comparison['sigma_E_daily'], 
                alpha=0.3, s=20)
    ax1.plot([0, 1], [0, 1], 'r--', label='45° line')
    ax1.set_xlabel('Annual Method (3-Year)')
    ax1.set_ylabel('Daily Method (252-Day)')
    ax1.set_title(f'Method Comparison\n(Correlation: {corr:.3f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Distribution comparison
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(comparison['sigma_E_annual'], bins=40, alpha=0.5, label='Annual', edgecolor='black')
    ax2.hist(comparison['sigma_E_daily'], bins=40, alpha=0.5, label='Daily', edgecolor='black')
    ax2.axvline(comparison['sigma_E_annual'].mean(), color='blue', linestyle='--', alpha=0.7)
    ax2.axvline(comparison['sigma_E_daily'].mean(), color='orange', linestyle='--', alpha=0.7)
    ax2.set_xlabel('Equity Volatility')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution Comparison')
    ax2.legend()
    
    # Plot 3: Difference distribution
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.hist(comparison['delta_pct'], bins=50, edgecolor='black', alpha=0.7)
    ax3.axvline(0, color='red', linestyle='--', label='No change')
    ax3.axvline(comparison['delta_pct'].median(), color='green', 
                linestyle='--', label=f'Median: {comparison["delta_pct"].median():.1f}%')
    ax3.set_xlabel('Percent Change (Daily vs Annual)')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Distribution of Changes')
    ax3.legend()
    
    # Plot 4: By year - Mean volatility
    ax4 = fig.add_subplot(gs[1, 0])
    year_vol = comparison.groupby('year')[['sigma_E_annual', 'sigma_E_daily']].mean()
    year_vol.plot(ax=ax4, marker='o')
    ax4.set_xlabel('Year')
    ax4.set_ylabel('Mean Equity Volatility')
    ax4.set_title('Mean Volatility Over Time')
    ax4.legend(['Annual', 'Daily'])
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: By year - Change
    ax5 = fig.add_subplot(gs[1, 1])
    year_change = comparison.groupby('year')['delta_pct'].mean()
    ax5.bar(year_change.index, year_change.values, edgecolor='black', alpha=0.7)
    ax5.axhline(0, color='red', linestyle='--')
    ax5.set_xlabel('Year')
    ax5.set_ylabel('Mean % Change')
    ax5.set_title('Average % Change by Year\n(Daily vs Annual)')
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Plot 6: By year - Direction
    ax6 = fig.add_subplot(gs[1, 2])
    year_direction = comparison.groupby('year')['higher_daily'].mean() * 100
    ax6.bar(year_direction.index, year_direction.values, edgecolor='black', alpha=0.7)
    ax6.axhline(50, color='red', linestyle='--', label='50%')
    ax6.set_xlabel('Year')
    ax6.set_ylabel('% of Banks')
    ax6.set_title('% Banks with Higher Daily Volatility')
    ax6.set_ylim([0, 100])
    ax6.grid(True, alpha=0.3, axis='y')
    ax6.legend()
    
    # Plot 7: Box plot by year
    ax7 = fig.add_subplot(gs[2, :])
    year_data = []
    labels = []
    for year in sorted(comparison['year'].unique()):
        year_subset = comparison[comparison['year'] == year]
        year_data.append(year_subset['delta_pct'].values)
        labels.append(str(year))
    
    bp = ax7.boxplot(year_data, labels=labels, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    ax7.axhline(0, color='red', linestyle='--', linewidth=1)
    ax7.set_xlabel('Year')
    ax7.set_ylabel('Percent Change (Daily vs Annual)')
    ax7.set_title('Distribution of % Changes by Year')
    ax7.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Volatility Method Comparison: Annual (3-Year) vs Daily (252-Day)', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    output_file = OUTPUT_DIR / 'volatility_comparison_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()
    
    # ========================================================================
    # Top Movers Analysis
    # ========================================================================
    
    print("\n[4] Identifying top movers...")
    print("-"*80)
    
    # Banks with largest absolute changes
    top_increases = comparison.nlargest(10, 'delta_pct')[['ticker', 'year', 'sigma_E_annual', 'sigma_E_daily', 'delta_pct']]
    top_decreases = comparison.nsmallest(10, 'delta_pct')[['ticker', 'year', 'sigma_E_annual', 'sigma_E_daily', 'delta_pct']]
    
    print("\n[Top 10 Increases (Daily > Annual)]")
    print(top_increases.to_string(index=False))
    
    print("\n[Top 10 Decreases (Daily < Annual)]")
    print(top_decreases.to_string(index=False))
    
    # ========================================================================
    # Save Comparison Data
    # ========================================================================
    
    comparison_file = OUTPUT_DIR / 'volatility_comparison_data.csv'
    comparison.to_csv(comparison_file, index=False)
    print(f"\n✓ Saved comparison data: {comparison_file}")

# ============================================================================
# Summary Report
# ============================================================================

print("\n" + "="*80)
print("SUMMARY REPORT")
print("="*80)

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

summary = f"""
Migration Analysis Report
Generated: {timestamp}

NEW METHOD (Daily 252-Day):
  Observations: {len(vol_daily)}
  Years: {vol_daily['year'].min()} - {vol_daily['year'].max()}
  Banks: {vol_daily['ticker'].nunique()}
  Mean volatility: {vol_daily['sigma_E'].mean():.3f}
  Median volatility: {vol_daily['sigma_E'].median():.3f}
  
  Method Distribution:
"""

for method, count in vol_daily['method'].value_counts().items():
    summary += f"    {method}: {count} ({count/len(vol_daily)*100:.1f}%)\n"

if has_old:
    summary += f"""
OLD METHOD (Annual 3-Year):
  Observations: {len(vol_annual)}
  Mean volatility: {vol_annual['sigma_E'].mean():.3f}
  Median volatility: {vol_annual['sigma_E'].median():.3f}

COMPARISON (Overlapping Observations: {len(comparison)}):
  Correlation: {corr:.4f}
  Mean % change: {comparison['delta_pct'].mean():.1f}%
  Daily higher in {comparison['higher_daily'].mean()*100:.1f}% of cases
  
INTERPRETATION:
  {'✓ High correlation (>0.70) - methods broadly agree' if corr > 0.70 else '⚠️ Lower correlation - methods differ significantly'}
  {'✓ Daily volatility generally higher - expected' if comparison['higher_daily'].mean() > 0.60 else '⚠️ Mixed results - investigate'}
  {'✓ Mean change reasonable (<30%)' if abs(comparison['delta_pct'].mean()) < 30 else '⚠️ Large mean change (>30%) - verify'}

"""

print(summary)

# Save summary
summary_file = OUTPUT_DIR / 'migration_summary_report.txt'
with open(summary_file, 'w') as f:
    f.write(summary)
print(f"✓ Saved summary: {summary_file}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print(f"\n✓ Outputs saved to: {OUTPUT_DIR}")
print("\nFiles created:")
print(f"  - volatility_comparison_analysis.png")
print(f"  - volatility_comparison_data.csv")
print(f"  - migration_summary_report.txt")

print("\n→ Review the visualizations and summary report")
print("→ If results look good, proceed with documentation updates")
