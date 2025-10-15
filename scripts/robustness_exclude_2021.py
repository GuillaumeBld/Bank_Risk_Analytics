"""
ROBUSTNESS CHECK: EXCLUDE 2021 (ANOMALY YEAR)
==============================================

Purpose: Test whether main results are driven by 2021 anomaly
- 2021 shows DD_a = 5.36 (vs ~12-14 in other years)
- Possible data quality issue or post-COVID market anomaly
- Compare full sample vs excluding 2021

Author: Analysis Team
Date: October 14, 2025
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from linearmodels.iv import IV2SLS
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("ROBUSTNESS CHECK: EXCLUDING 2021 ANOMALY YEAR")
print("="*80)

# ============================================================================
# LOAD DATA
# ============================================================================

data_path = '/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank/data/outputs/datasheet/esg_dd_pd_20251014_022322.csv'
df = pd.read_csv(data_path)

print(f"\nOriginal data: {len(df)} observations")
print(f"Years: {df['year'].min()}-{df['year'].max()}")

# Check 2021 observations
n_2021 = len(df[df['year'] == 2021])
print(f"2021 observations: {n_2021} ({n_2021/len(df)*100:.1f}%)")

# Create datasets
df_full = df.copy()
df_no2021 = df[df['year'] != 2021].copy()

print(f"Full sample: {len(df_full)} observations")
print(f"Excluding 2021: {len(df_no2021)} observations")
print(f"Dropped: {len(df_full) - len(df_no2021)} observations")

# ============================================================================
# DESCRIPTIVE COMPARISON
# ============================================================================

print("\n" + "="*80)
print("DESCRIPTIVE STATISTICS: FULL vs EXCLUDING 2021")
print("="*80)

# Key variables
key_vars = ['DD_a', 'DD_m', 'esg_score', 'lnta', 'td/ta', 'd/e']
var_labels = ['DD_a', 'DD_m', 'ESG Score', 'Log(Assets)', 'Debt/Assets', 'Debt/Equity']

comparison = []
for var, label in zip(key_vars, var_labels):
    if var in df_full.columns:
        full_mean = df_full[var].mean()
        full_std = df_full[var].std()
        no2021_mean = df_no2021[var].mean()
        no2021_std = df_no2021[var].std()
        
        # Calculate difference
        diff = no2021_mean - full_mean
        pct_change = (diff / full_mean * 100) if full_mean != 0 else 0
        
        comparison.append({
            'Variable': label,
            'Full Sample Mean': f"{full_mean:.2f}",
            'Excl 2021 Mean': f"{no2021_mean:.2f}",
            'Difference': f"{diff:+.2f}",
            'Change %': f"{pct_change:+.1f}%"
        })

comp_df = pd.DataFrame(comparison)
print("\n" + comp_df.to_string(index=False))

# Specific focus on DD_a
print("\n" + "-"*80)
print("DD_a DISTRIBUTION COMPARISON:")
print("-"*80)

dd_stats = pd.DataFrame({
    'Statistic': ['N', 'Mean', 'Std Dev', 'Min', 'Median', 'Max'],
    'Full Sample': [
        df_full['DD_a'].notna().sum(),
        df_full['DD_a'].mean(),
        df_full['DD_a'].std(),
        df_full['DD_a'].min(),
        df_full['DD_a'].median(),
        df_full['DD_a'].max()
    ],
    'Excluding 2021': [
        df_no2021['DD_a'].notna().sum(),
        df_no2021['DD_a'].mean(),
        df_no2021['DD_a'].std(),
        df_no2021['DD_a'].min(),
        df_no2021['DD_a'].median(),
        df_no2021['DD_a'].max()
    ]
})

print("\n" + dd_stats.to_string(index=False))

# ============================================================================
# REGRESSION FUNCTION
# ============================================================================

def run_regression_suite(data, label):
    """Run full suite of regressions on given dataset"""
    
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    
    results = {}
    
    # Prepare data
    analysis_vars = ['DD_a', 'esg_score', 'esg_score_1', 'lnta', 'td/ta', 'instrument', 'd/e']
    df_reg = data[[v for v in analysis_vars if v in data.columns]].dropna()
    
    print(f"\nN = {len(df_reg)} observations (after dropping missing)")
    
    # Model 1: OLS Baseline (no controls)
    print("\n" + "-"*80)
    print("MODEL 1: OLS - No Controls")
    print("-"*80)
    
    formula1 = 'DD_a ~ esg_score'
    model1 = sm.OLS.from_formula(formula1, data=df_reg).fit(
        cov_type='cluster', cov_kwds={'groups': df_reg['instrument']}
    )
    
    coef1 = model1.params['esg_score']
    se1 = model1.bse['esg_score']
    t1 = model1.tvalues['esg_score']
    p1 = model1.pvalues['esg_score']
    sig1 = '***' if p1 < 0.01 else '**' if p1 < 0.05 else '*' if p1 < 0.10 else ''
    
    print(f"ESG coefficient: {coef1:.4f}{sig1} (SE={se1:.4f}, t={t1:.2f}, p={p1:.4f})")
    print(f"R-squared: {model1.rsquared:.4f}")
    
    results['Model 1 (OLS)'] = {
        'coef': coef1, 'se': se1, 't': t1, 'p': p1, 'sig': sig1, 'r2': model1.rsquared
    }
    
    # Model 2: OLS with Size Control
    print("\n" + "-"*80)
    print("MODEL 2: OLS - With Size Control")
    print("-"*80)
    
    formula2 = 'DD_a ~ esg_score + lnta'
    model2 = sm.OLS.from_formula(formula2, data=df_reg).fit(
        cov_type='cluster', cov_kwds={'groups': df_reg['instrument']}
    )
    
    coef2 = model2.params['esg_score']
    se2 = model2.bse['esg_score']
    t2 = model2.tvalues['esg_score']
    p2 = model2.pvalues['esg_score']
    sig2 = '***' if p2 < 0.01 else '**' if p2 < 0.05 else '*' if p2 < 0.10 else ''
    
    print(f"ESG coefficient: {coef2:.4f}{sig2} (SE={se2:.4f}, t={t2:.2f}, p={p2:.4f})")
    print(f"R-squared: {model2.rsquared:.4f}")
    
    results['Model 2 (OLS+Size)'] = {
        'coef': coef2, 'se': se2, 't': t2, 'p': p2, 'sig': sig2, 'r2': model2.rsquared
    }
    
    # Model 3: OLS with Size + Leverage
    print("\n" + "-"*80)
    print("MODEL 3: OLS - With Size + Leverage Controls")
    print("-"*80)
    
    formula3 = 'DD_a ~ esg_score + lnta + Q("td/ta")'
    model3 = sm.OLS.from_formula(formula3, data=df_reg).fit(
        cov_type='cluster', cov_kwds={'groups': df_reg['instrument']}
    )
    
    coef3 = model3.params['esg_score']
    se3 = model3.bse['esg_score']
    t3 = model3.tvalues['esg_score']
    p3 = model3.pvalues['esg_score']
    sig3 = '***' if p3 < 0.01 else '**' if p3 < 0.05 else '*' if p3 < 0.10 else ''
    
    print(f"ESG coefficient: {coef3:.4f}{sig3} (SE={se3:.4f}, t={t3:.2f}, p={p3:.4f})")
    print(f"R-squared: {model3.rsquared:.4f}")
    
    results['Model 3 (OLS+Size+Lev)'] = {
        'coef': coef3, 'se': se3, 't': t3, 'p': p3, 'sig': sig3, 'r2': model3.rsquared
    }
    
    # Model 4: 2SLS Baseline
    print("\n" + "-"*80)
    print("MODEL 4: 2SLS - No Controls")
    print("-"*80)
    
    try:
        formula4 = 'DD_a ~ 1 + [esg_score ~ esg_score_1]'
        model4 = IV2SLS.from_formula(formula4, data=df_reg).fit(
            cov_type='clustered', cov_kwds={'clusters': df_reg['instrument']}
        )
        
        coef4 = model4.params['esg_score']
        se4 = model4.std_errors['esg_score']
        t4 = model4.tstats['esg_score']
        p4 = model4.pvalues['esg_score']
        sig4 = '***' if p4 < 0.01 else '**' if p4 < 0.05 else '*' if p4 < 0.10 else ''
        f_stat = model4.first_stage.diagnostics['f.stat']
        
        print(f"ESG coefficient: {coef4:.4f}{sig4} (SE={se4:.4f}, t={t4:.2f}, p={p4:.4f})")
        print(f"First-stage F: {f_stat:.2f} {'✅ STRONG' if f_stat > 10 else '⚠️ WEAK'}")
        print(f"R-squared: {model4.rsquared:.4f}")
        
        results['Model 4 (2SLS)'] = {
            'coef': coef4, 'se': se4, 't': t4, 'p': p4, 'sig': sig4, 
            'f_stat': f_stat, 'r2': model4.rsquared
        }
    except Exception as e:
        print(f"⚠️ 2SLS failed: {e}")
        results['Model 4 (2SLS)'] = {
            'coef': np.nan, 'se': np.nan, 't': np.nan, 'p': np.nan, 
            'sig': '', 'f_stat': np.nan, 'r2': np.nan
        }
    
    # Model 5: 2SLS with Size Control
    print("\n" + "-"*80)
    print("MODEL 5: 2SLS - With Size Control")
    print("-"*80)
    
    try:
        formula5 = 'DD_a ~ 1 + [esg_score ~ esg_score_1] + lnta'
        model5 = IV2SLS.from_formula(formula5, data=df_reg).fit(
            cov_type='clustered', cov_kwds={'clusters': df_reg['instrument']}
        )
        
        coef5 = model5.params['esg_score']
        se5 = model5.std_errors['esg_score']
        t5 = model5.tstats['esg_score']
        p5 = model5.pvalues['esg_score']
        sig5 = '***' if p5 < 0.01 else '**' if p5 < 0.05 else '*' if p5 < 0.10 else ''
        f_stat5 = model5.first_stage.diagnostics['f.stat']
        
        print(f"ESG coefficient: {coef5:.4f}{sig5} (SE={se5:.4f}, t={t5:.2f}, p={p5:.4f})")
        print(f"First-stage F: {f_stat5:.2f} {'✅ STRONG' if f_stat5 > 10 else '⚠️ WEAK'}")
        print(f"R-squared: {model5.rsquared:.4f}")
        
        results['Model 5 (2SLS+Size)'] = {
            'coef': coef5, 'se': se5, 't': t5, 'p': p5, 'sig': sig5,
            'f_stat': f_stat5, 'r2': model5.rsquared
        }
    except Exception as e:
        print(f"⚠️ 2SLS failed: {e}")
        results['Model 5 (2SLS+Size)'] = {
            'coef': np.nan, 'se': np.nan, 't': np.nan, 'p': np.nan,
            'sig': '', 'f_stat': np.nan, 'r2': np.nan
        }
    
    return results

# ============================================================================
# RUN REGRESSIONS FOR BOTH SAMPLES
# ============================================================================

print("\n" + "="*80)
print("REGRESSION ANALYSIS")
print("="*80)

# Full sample
results_full = run_regression_suite(df_full, "FULL SAMPLE (2016-2023)")

# Excluding 2021
results_no2021 = run_regression_suite(df_no2021, "EXCLUDING 2021 (2016-2020, 2022-2023)")

# ============================================================================
# COMPARISON TABLE
# ============================================================================

print("\n" + "="*80)
print("COMPARISON: FULL SAMPLE vs EXCLUDING 2021")
print("="*80)

comparison_rows = []

for model_name in ['Model 1 (OLS)', 'Model 2 (OLS+Size)', 'Model 3 (OLS+Size+Lev)', 
                   'Model 4 (2SLS)', 'Model 5 (2SLS+Size)']:
    
    full_coef = results_full.get(model_name, {}).get('coef', np.nan)
    full_sig = results_full.get(model_name, {}).get('sig', '')
    full_se = results_full.get(model_name, {}).get('se', np.nan)
    
    no2021_coef = results_no2021.get(model_name, {}).get('coef', np.nan)
    no2021_sig = results_no2021.get(model_name, {}).get('sig', '')
    no2021_se = results_no2021.get(model_name, {}).get('se', np.nan)
    
    # Calculate change
    if not np.isnan(full_coef) and not np.isnan(no2021_coef):
        diff = no2021_coef - full_coef
        pct_change = (diff / abs(full_coef) * 100) if full_coef != 0 else 0
        
        # Assess robustness
        if abs(pct_change) < 10:
            robust = "✅ VERY ROBUST"
        elif abs(pct_change) < 20:
            robust = "✅ ROBUST"
        elif abs(pct_change) < 30:
            robust = "🔶 MODERATE"
        else:
            robust = "⚠️ SENSITIVE"
    else:
        diff = np.nan
        pct_change = np.nan
        robust = "N/A"
    
    comparison_rows.append({
        'Model': model_name,
        'Full Sample': f"{full_coef:.4f}{full_sig}" if not np.isnan(full_coef) else "N/A",
        'Excl 2021': f"{no2021_coef:.4f}{no2021_sig}" if not np.isnan(no2021_coef) else "N/A",
        'Difference': f"{diff:+.4f}" if not np.isnan(diff) else "N/A",
        'Change %': f"{pct_change:+.1f}%" if not np.isnan(pct_change) else "N/A",
        'Assessment': robust
    })

comparison_table = pd.DataFrame(comparison_rows)
print("\n" + comparison_table.to_string(index=False))

# ============================================================================
# KEY INSIGHTS
# ============================================================================

print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

# Focus on main result (2SLS baseline - Model 4)
full_2sls = results_full.get('Model 4 (2SLS)', {}).get('coef', np.nan)
no2021_2sls = results_no2021.get('Model 4 (2SLS)', {}).get('coef', np.nan)

if not np.isnan(full_2sls) and not np.isnan(no2021_2sls):
    diff_2sls = no2021_2sls - full_2sls
    pct_change_2sls = (diff_2sls / abs(full_2sls) * 100)
    
    print(f"\n1️⃣ MAIN RESULT (2SLS, Model 4):")
    print(f"   Full sample: β = {full_2sls:.4f}")
    print(f"   Excl 2021:   β = {no2021_2sls:.4f}")
    print(f"   Change:      {diff_2sls:+.4f} ({pct_change_2sls:+.1f}%)")
    
    if abs(pct_change_2sls) < 10:
        print(f"   ✅ VERY ROBUST: Result barely changes (<10% change)")
    elif abs(pct_change_2sls) < 20:
        print(f"   ✅ ROBUST: Result is stable (<20% change)")
    else:
        print(f"   ⚠️ CAUTION: Result changes by {abs(pct_change_2sls):.1f}%")
    
    # Direction check
    if np.sign(full_2sls) == np.sign(no2021_2sls):
        print(f"   ✅ Direction CONSISTENT (both negative)")
    else:
        print(f"   ❌ Direction CHANGES - major concern!")

print(f"\n2️⃣ STATISTICAL SIGNIFICANCE:")

# Check if significance changes
for model_name in ['Model 4 (2SLS)', 'Model 5 (2SLS+Size)']:
    full_sig = results_full.get(model_name, {}).get('sig', '')
    no2021_sig = results_no2021.get(model_name, {}).get('sig', '')
    
    if full_sig and no2021_sig:
        if full_sig == no2021_sig:
            print(f"   {model_name}: {full_sig} → {no2021_sig} ✅ UNCHANGED")
        else:
            print(f"   {model_name}: {full_sig} → {no2021_sig} 🔶 CHANGED")

print(f"\n3️⃣ FIRST-STAGE STRENGTH:")

full_f = results_full.get('Model 4 (2SLS)', {}).get('f_stat', np.nan)
no2021_f = results_no2021.get('Model 4 (2SLS)', {}).get('f_stat', np.nan)

if not np.isnan(full_f) and not np.isnan(no2021_f):
    print(f"   Full sample: F = {full_f:.2f}")
    print(f"   Excl 2021:   F = {no2021_f:.2f}")
    
    if full_f > 10 and no2021_f > 10:
        print(f"   ✅ STRONG instruments in both samples")
    else:
        print(f"   ⚠️ Weak instrument concern in one or both samples")

print(f"\n4️⃣ OVERALL ASSESSMENT:")

# Count how many models are robust
robust_count = sum(1 for row in comparison_rows 
                  if "ROBUST" in row['Assessment'] or "VERY ROBUST" in row['Assessment'])
total_models = len([r for r in comparison_rows if r['Assessment'] != "N/A"])

print(f"   {robust_count}/{total_models} models show robust results (change <20%)")

if robust_count >= 4:
    print(f"\n   ✅ CONCLUSION: Results are ROBUST to excluding 2021")
    print(f"   → 2021 anomaly does NOT drive main findings")
    print(f"   → Can proceed with full sample confidently")
elif robust_count >= 2:
    print(f"\n   🔶 CONCLUSION: Results are MODERATELY robust")
    print(f"   → Consider reporting both specifications")
    print(f"   → Mention 2021 as potential concern")
else:
    print(f"\n   ⚠️ CONCLUSION: Results are SENSITIVE to 2021")
    print(f"   → Should use excluding-2021 as main specification")
    print(f"   → Investigate 2021 data quality further")

# ============================================================================
# RECOMMENDATIONS
# ============================================================================

print("\n" + "="*80)
print("RECOMMENDATIONS FOR PAPER")
print("="*80)

print("\n📝 If results are ROBUST (change <10%):")
print("   → Use full sample as main specification")
print("   → Report excluding-2021 as robustness check")
print("   → Mention in footnote: 'Results unchanged when excluding 2021'")

print("\n📝 If results are MODERATELY robust (change 10-20%):")
print("   → Report both specifications in main table")
print("   → Add note: 'Coefficients slightly smaller/larger excluding 2021 anomaly'")
print("   → Emphasize that direction and significance remain consistent")

print("\n📝 If results are SENSITIVE (change >20%):")
print("   → Investigate 2021 data quality issue FIRST")
print("   → Consider using excluding-2021 as main specification")
print("   → Be transparent about sensitivity in paper")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\n✅ Next steps:")
print("   1. Review comparison table above")
print("   2. Check if main result (Model 4) is robust")
print("   3. Decide on reporting strategy based on recommendations")
print("   4. Update paper with robustness check table/footnote")
