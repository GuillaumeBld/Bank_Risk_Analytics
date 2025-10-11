"""
Winsorization utilities for DD/PD analysis

This module provides functions for winsorizing Distance-to-Default (DD) and 
Probability-of-Default (PD) variables by year and size category to handle 
extreme values while preserving distributional properties within groups.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional


def trim_by_year_size(
    df: pd.DataFrame,
    dd_cols: List[str],
    year_col: str = 'year',
    size_col: str = 'dummylarge',
    percentiles: Tuple[float, float] = (0.01, 0.99),
    report: bool = True
) -> pd.DataFrame:
    """
    Trim (exclude) extreme DD values by year and size category.
    
    This approach REMOVES observations beyond the percentile thresholds,
    rather than clipping them. The original DD columns are preserved,
    but extreme observations are excluded from the dataset.
    
    This approach is superior to overall trimming because:
    1. Controls for time-varying risk (different years have different risk profiles)
    2. Controls for size effects (large banks have different DD distributions)
    3. Prevents cross-contamination between groups
    4. More conservative treatment of extremes
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with DD variables
    dd_cols : List[str]
        List of DD column names to trim (e.g., ['DD_a', 'DD_m'])
    year_col : str, default='year'
        Column name for year
    size_col : str, default='dummylarge'
        Column name for size category (1=large, 0=small/mid)
    percentiles : Tuple[float, float], default=(0.01, 0.99)
        Lower and upper percentiles for trimming
    report : bool, default=True
        Whether to print detailed trimming summary
        
    Returns
    -------
    pd.DataFrame
        DataFrame with extreme observations removed
        
    Examples
    --------
    >>> df_trimmed = trim_by_year_size(df, ['DD_a', 'DD_m'], percentiles=(0.01, 0.99))
    >>> # Use original DD variables in regressions (extremes removed)
    >>> model = smf.ols('DD_m ~ ESG + controls', data=df_trimmed).fit()
    """
    
    df = df.copy()
    
    if report:
        print("=" * 80)
        print("TRIMMING BY YEAR AND SIZE CATEGORY")
        print("=" * 80)
        print(f"Method: Percentile-based exclusion ({percentiles[0]*100:.0f}%, {percentiles[1]*100:.0f}%)")
        print(f"Grouping: {year_col} × {size_col}")
        print(f"Action: REMOVE observations beyond thresholds")
        print()
    
    # Track which observations to keep
    keep_mask = pd.Series(True, index=df.index)
    
    for col in dd_cols:
        if col not in df.columns:
            if report:
                print(f"⚠️  Column '{col}' not found in dataframe. Skipping.")
            continue
        
        # Track statistics
        total_obs = df[col].notna().sum()
        total_excluded = 0
        group_stats = []
        
        # Identify extremes within each year-size group
        for year in sorted(df[year_col].unique()):
            for size in sorted(df[size_col].unique()):
                # Get group mask
                mask = (df[year_col] == year) & (df[size_col] == size) & df[col].notna()
                group_data = df.loc[mask, col]
                
                if len(group_data) < 10:  # Skip groups with too few observations
                    continue
                
                # Calculate percentiles for this group
                p_low = group_data.quantile(percentiles[0])
                p_high = group_data.quantile(percentiles[1])
                
                # Mark observations outside bounds for exclusion
                extreme_mask = mask & ((df[col] < p_low) | (df[col] > p_high))
                keep_mask &= ~extreme_mask
                
                # Count excluded observations
                n_lower = (group_data < p_low).sum()
                n_upper = (group_data > p_high).sum()
                n_excluded = n_lower + n_upper
                total_excluded += n_excluded
                
                # Store group statistics
                size_label = 'Large' if size == 1 else 'Small/Mid'
                group_stats.append({
                    'year': year,
                    'size': size_label,
                    'n_obs': len(group_data),
                    'n_excluded': n_excluded,
                    'pct_excluded': n_excluded / len(group_data) * 100 if len(group_data) > 0 else 0,
                    'p_low': p_low,
                    'p_high': p_high,
                    'original_min': group_data.min(),
                    'original_max': group_data.max()
                })
        
        if report:
            print(f"\n{col}:")
            print(f"  Total observations: {total_obs}")
            print(f"  Total excluded: {total_excluded} ({total_excluded/total_obs*100:.1f}%)")
            print(f"  Remaining: {total_obs - total_excluded}")
            
            # Show detailed group statistics
            if group_stats:
                stats_df = pd.DataFrame(group_stats)
                print(f"\n  Group-level statistics:")
                print(f"  {'Year':<6} {'Size':<10} {'N':<6} {'Excluded':<9} {'%':<6} {'Bounds':<30}")
                print(f"  {'-'*70}")
                for _, row in stats_df.iterrows():
                    bounds = f"[{row['p_low']:.2f}, {row['p_high']:.2f}]"
                    print(f"  {int(row['year']):<6} {row['size']:<10} {row['n_obs']:<6} "
                          f"{row['n_excluded']:<9} {row['pct_excluded']:<6.1f} {bounds:<30}")
    
    # Apply the exclusion
    df_trimmed = df[keep_mask].copy()
    
    if report:
        print("\n" + "=" * 80)
        print(f"✓ Trimming complete.")
        print(f"  Original sample: {len(df)} observations")
        print(f"  Trimmed sample: {len(df_trimmed)} observations")
        print(f"  Excluded: {len(df) - len(df_trimmed)} observations ({(len(df) - len(df_trimmed))/len(df)*100:.1f}%)")
        print("=" * 80)
    
    return df_trimmed


def winsorize_overall(
    df: pd.DataFrame,
    dd_cols: List[str],
    percentiles: Tuple[float, float] = (0.01, 0.99),
    report: bool = True
) -> pd.DataFrame:
    """
    Winsorize DD variables using overall percentiles (simpler approach).
    
    This is a fallback method when year-size winsorization is not appropriate.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe
    dd_cols : List[str]
        List of DD column names
    percentiles : Tuple[float, float]
        Lower and upper percentiles
    report : bool
        Whether to print summary
        
    Returns
    -------
    pd.DataFrame
        DataFrame with winsorized columns
    """
    
    df = df.copy()
    
    if report:
        print("=" * 80)
        print("OVERALL WINSORIZATION (NOT GROUPED)")
        print("=" * 80)
        print(f"Method: Percentile-based ({percentiles[0]*100:.0f}%, {percentiles[1]*100:.0f}%)")
        print()
    
    for col in dd_cols:
        if col not in df.columns:
            continue
            
        valid_data = df[col].dropna()
        
        if len(valid_data) > 0:
            p_low = valid_data.quantile(percentiles[0])
            p_high = valid_data.quantile(percentiles[1])
            
            df[f'{col}_wins_overall'] = df[col].clip(lower=p_low, upper=p_high)
            
            n_lower = (df[col] < p_low).sum()
            n_upper = (df[col] > p_high).sum()
            n_total = n_lower + n_upper
            
            if report:
                print(f"{col}:")
                print(f"  Original range: [{valid_data.min():.2f}, {valid_data.max():.2f}]")
                print(f"  Winsorized at: [{p_low:.2f}, {p_high:.2f}]")
                print(f"  Lower tail clipped: {n_lower} obs")
                print(f"  Upper tail clipped: {n_upper} obs")
                print(f"  Total affected: {n_total} ({n_total/len(valid_data)*100:.1f}%)")
                print(f"  Mean change: {df[col].mean():.3f} → {df[f'{col}_wins_overall'].mean():.3f}")
                print()
    
    if report:
        print("=" * 80)
    
    return df


def compare_winsorization_methods(
    df: pd.DataFrame,
    dd_col: str,
    year_col: str = 'year',
    size_col: str = 'dummylarge'
) -> pd.DataFrame:
    """
    Compare year-size winsorization vs overall winsorization.
    
    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with both winsorized versions
    dd_col : str
        DD column name
    year_col : str
        Year column name
    size_col : str
        Size category column name
        
    Returns
    -------
    pd.DataFrame
        Comparison statistics
    """
    
    if f'{dd_col}_wins' not in df.columns or f'{dd_col}_wins_overall' not in df.columns:
        raise ValueError("Both winsorized versions must exist in dataframe")
    
    comparison = []
    
    for year in sorted(df[year_col].unique()):
        for size in sorted(df[size_col].unique()):
            mask = (df[year_col] == year) & (df[size_col] == size)
            group_df = df[mask]
            
            if len(group_df) == 0:
                continue
            
            size_label = 'Large' if size == 1 else 'Small/Mid'
            
            comparison.append({
                'year': year,
                'size': size_label,
                'n_obs': len(group_df),
                'original_mean': group_df[dd_col].mean(),
                'year_size_wins_mean': group_df[f'{dd_col}_wins'].mean(),
                'overall_wins_mean': group_df[f'{dd_col}_wins_overall'].mean(),
                'year_size_std': group_df[f'{dd_col}_wins'].std(),
                'overall_std': group_df[f'{dd_col}_wins_overall'].std()
            })
    
    return pd.DataFrame(comparison)


def export_winsorization_report(
    df: pd.DataFrame,
    dd_cols: List[str],
    output_path: str,
    year_col: str = 'year',
    size_col: str = 'dummylarge'
) -> None:
    """
    Export detailed winsorization report to CSV.
    
    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with winsorized columns
    dd_cols : List[str]
        List of DD columns
    output_path : str
        Path to save report
    year_col : str
        Year column name
    size_col : str
        Size category column name
    """
    
    report_data = []
    
    for col in dd_cols:
        if col not in df.columns or f'{col}_wins' not in df.columns:
            continue
        
        # Find winsorized observations
        winsorized = df[df[col] != df[f'{col}_wins']].copy()
        
        for _, row in winsorized.iterrows():
            size_label = 'Large' if row[size_col] == 1 else 'Small/Mid'
            report_data.append({
                'variable': col,
                'instrument': row.get('instrument', 'Unknown'),
                'year': row[year_col],
                'size_category': size_label,
                'original_value': row[col],
                'winsorized_value': row[f'{col}_wins'],
                'change': row[f'{col}_wins'] - row[col],
                'direction': 'upper' if row[col] > row[f'{col}_wins'] else 'lower'
            })
    
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(output_path, index=False)
    print(f"✓ Winsorization report saved to: {output_path}")
    print(f"  Total winsorized observations: {len(report_df)}")
