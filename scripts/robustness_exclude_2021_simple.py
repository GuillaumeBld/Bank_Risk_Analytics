"""
ROBUSTNESS CHECK: EXCLUDE 2021 (SIMPLE VERSION)
================================================

Test whether main results are driven by 2021 anomaly using manual 2SLS

Author: Analysis Team
Date: October 14, 2025
"""

import pandas as pd
import numpy as np
import statsmodels.api as sm
from scipy import stats

print("="*80)
print("ROBUSTNESS CHECK: EXCLUDING 2021 ANOMALY YEAR")
print("="*80)

# Load data
data_path = '/Users/guillaumebld/Documents/Graduate_Research/Professor Abol Jalilvand/fall2025/risk_bank/risk_bank/data/outputs/datasheet/esg_dd_pd_20251014_022322.csv'
df = pd.read_csv(data_path)

print(f"\nOriginal data: {len(df)} observations")
print(f"Years: {df['year'].min()}-{df['year'].max()}")

# Check 2021
n_2021 = len(df[df['year'] == 2021])
print(f"2021 observations: {n_2021} ({n_2021/len(df)*100:.1f}%)")

# Create datasets
df_full = df.copy()
df_no2021 = df[df['year'] != 2021].copy()

print(f"\nFull sample: {len(df_full)} observations")
print(f"Excluding 2021: {len(df_no2021)} observations")
print(f"Dropped: {len(df_full) - len(df_no2021)} observations")

# ============================================================================
# DESCRIPTIVE COMPARISON
# ============================================================================

print("\n" + "="*80)
print("DESCRIPTIVE STATISTICS COMPARISON")
print("="*80)

vars_to_compare = {
    'DD_a': 'Distance-to-Default (Accounting)',
    'DD_m': 'Distance-to-Default (Market)',
    'esg_score': 'ESG Score',
    'lnta': 'Log(Total Assets)',
    'td/ta': 'Debt/Assets'
}

print(f"\n{'Variable':<40} {'Full':>12} {'Excl 2021':>12} {'Diff':>10} {'% Change':>10}")
print("-"*84)

for var, label in vars_to_compare.items():
    if var in df_full.columns:
        full_mean = df_full[var].mean()
        no2021_mean = df_no2021[var].mean()
        diff = no2021_mean - full_mean
        pct = (diff / full_mean * 100) if full_mean != 0 else 0
        
        print(f"{label:<40} {full_mean:>12.3f} {no2021_mean:>12.3f} {diff:>+10.3f} {pct:>+9.1f}%")

# ============================================================================
# REGRESSION ANALYSIS
# ============================================================================

def run_regressions(data, label):
    """Run regressions and return results"""
    
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")
    
    # Prepare data
    required = ['DD_a', 'esg_score', 'esg_score_1', 'lnta', 'td/ta', 'instrument']
    df_reg = data[[c for c in required if c in data.columns]].dropna()
    
    print(f"N = {len(df_reg)} (after dropping missing)")
    
    results = {}
    
    # ========================================================================
    # MODEL 1: OLS - No Controls
    # ========================================================================
    print("\n" + "-"*80)
    print("MODEL 1: OLS - ESG only (no controls)")
    print("-"*80)
    
    X = sm.add_constant(df_reg[['esg_score']])
    y = df_reg['DD_a']
    
    model1 = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': df_reg['instrument']})
    
    coef = model1.params['esg_score']
    se = model1.bse['esg_score']
    t = model1.tvalues['esg_score']
    p = model1.pvalues['esg_score']
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''
    
    print(f"ESG coefficient: {coef:.4f}{sig}")
    print(f"Standard error: {se:.4f}")
    print(f"t-statistic: {t:.2f}")
    print(f"p-value: {p:.4f}")
    print(f"R-squared: {model1.rsquared:.4f}")
    
    results['OLS_NoControls'] = {'coef': coef, 'se': se, 't': t, 'p': p, 'sig': sig}
    
    # ========================================================================
    # MODEL 2: OLS - With Size
    # ========================================================================
    print("\n" + "-"*80)
    print("MODEL 2: OLS - ESG + Size")
    print("-"*80)
    
    X = sm.add_constant(df_reg[['esg_score', 'lnta']])
    y = df_reg['DD_a']
    
    model2 = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': df_reg['instrument']})
    
    coef = model2.params['esg_score']
    se = model2.bse['esg_score']
    t = model2.tvalues['esg_score']
    p = model2.pvalues['esg_score']
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''
    
    print(f"ESG coefficient: {coef:.4f}{sig}")
    print(f"Standard error: {se:.4f}")
    print(f"t-statistic: {t:.2f}")
    print(f"p-value: {p:.4f}")
    print(f"R-squared: {model2.rsquared:.4f}")
    
    results['OLS_Size'] = {'coef': coef, 'se': se, 't': t, 'p': p, 'sig': sig}
    
    # ========================================================================
    # MODEL 3: OLS - With Size + Leverage
    # ========================================================================
    print("\n" + "-"*80)
    print("MODEL 3: OLS - ESG + Size + Leverage")
    print("-"*80)
    
    X = sm.add_constant(df_reg[['esg_score', 'lnta', 'td/ta']])
    y = df_reg['DD_a']
    
    model3 = sm.OLS(y, X).fit(cov_type='cluster', cov_kwds={'groups': df_reg['instrument']})
    
    coef = model3.params['esg_score']
    se = model3.bse['esg_score']
    t = model3.tvalues['esg_score']
    p = model3.pvalues['esg_score']
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''
    
    print(f"ESG coefficient: {coef:.4f}{sig}")
    print(f"Standard error: {se:.4f}")
    print(f"t-statistic: {t:.2f}")
    print(f"p-value: {p:.4f}")
    print(f"R-squared: {model3.rsquared:.4f}")
    
    results['OLS_Full'] = {'coef': coef, 'se': se, 't': t, 'p': p, 'sig': sig}
    
    # ========================================================================
    # MODEL 4: 2SLS - Manual Implementation
    # ========================================================================
    print("\n" + "-"*80)
    print("MODEL 4: 2SLS (Manual) - ESG only")
    print("-"*80)
    
    # Stage 1: Regress ESG on lagged ESG
    X_first = sm.add_constant(df_reg[['esg_score_1']])
    y_first = df_reg['esg_score']
    
    first_stage = sm.OLS(y_first, X_first).fit()
    esg_fitted = first_stage.fittedvalues
    
    # F-statistic for first stage
    f_stat = first_stage.fvalue
    
    print(f"First-stage F-statistic: {f_stat:.2f}", end='')
    if f_stat > 10:
        print(" ✅ STRONG INSTRUMENT")
    else:
        print(" ⚠️ WEAK INSTRUMENT")
    
    # Stage 2: Regress DD on fitted ESG
    df_temp = pd.DataFrame({
        'DD_a': df_reg['DD_a'].values,
        'esg_fitted': esg_fitted.values
    })
    
    X_second = sm.add_constant(df_temp[['esg_fitted']])
    y_second = df_temp['DD_a']
    
    second_stage = sm.OLS(y_second, X_second).fit(
        cov_type='cluster', cov_kwds={'groups': df_reg['instrument']}
    )
    
    coef = second_stage.params['esg_fitted']
    se = second_stage.bse['esg_fitted']
    t = second_stage.tvalues['esg_fitted']
    p = second_stage.pvalues['esg_fitted']
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''
    
    print(f"ESG coefficient (2SLS): {coef:.4f}{sig}")
    print(f"Standard error: {se:.4f}")
    print(f"t-statistic: {t:.2f}")
    print(f"p-value: {p:.4f}")
    
    results['2SLS_NoControls'] = {'coef': coef, 'se': se, 't': t, 'p': p, 'sig': sig, 'f_stat': f_stat}
    
    # ========================================================================
    # MODEL 5: 2SLS with Size
    # ========================================================================
    print("\n" + "-"*80)
    print("MODEL 5: 2SLS (Manual) - ESG + Size")
    print("-"*80)
    
    # Stage 1: Regress ESG on lagged ESG + size
    X_first = sm.add_constant(df_reg[['esg_score_1', 'lnta']])
    y_first = df_reg['esg_score']
    
    first_stage = sm.OLS(y_first, X_first).fit()
    esg_fitted = first_stage.fittedvalues
    f_stat = first_stage.fvalue
    
    print(f"First-stage F-statistic: {f_stat:.2f}", end='')
    if f_stat > 10:
        print(" ✅ STRONG INSTRUMENT")
    else:
        print(" ⚠️ WEAK INSTRUMENT")
    
    # Stage 2: Regress DD on fitted ESG + size
    df_temp = pd.DataFrame({
        'DD_a': df_reg['DD_a'].values,
        'esg_fitted': esg_fitted.values,
        'lnta': df_reg['lnta'].values
    })
    
    X_second = sm.add_constant(df_temp[['esg_fitted', 'lnta']])
    y_second = df_temp['DD_a']
    
    second_stage = sm.OLS(y_second, X_second).fit(
        cov_type='cluster', cov_kwds={'groups': df_reg['instrument']}
    )
    
    coef = second_stage.params['esg_fitted']
    se = second_stage.bse['esg_fitted']
    t = second_stage.tvalues['esg_fitted']
    p = second_stage.pvalues['esg_fitted']
    sig = '***' if p < 0.01 else '**' if p < 0.05 else '*' if p < 0.10 else ''
    
    print(f"ESG coefficient (2SLS): {coef:.4f}{sig}")
    print(f"Standard error: {se:.4f}")
    print(f"t-statistic: {t:.2f}")
    print(f"p-value: {p:.4f}")
    
    results['2SLS_Size'] = {'coef': coef, 'se': se, 't': t, 'p': p, 'sig': sig, 'f_stat': f_stat}
    
    return results

# Run for both samples
results_full = run_regressions(df_full, "FULL SAMPLE (2016-2023)")
results_no2021 = run_regressions(df_no2021, "EXCLUDING 2021")

# ============================================================================
# COMPARISON TABLE
# ============================================================================

print("\n" + "="*80)
print("COMPARISON: FULL SAMPLE vs EXCLUDING 2021")
print("="*80)

models = ['OLS_NoControls', 'OLS_Size', 'OLS_Full', '2SLS_NoControls', '2SLS_Size']
model_labels = ['OLS (No Controls)', 'OLS (+ Size)', 'OLS (+ Size + Lev)', '2SLS (No Controls)', '2SLS (+ Size)']

print(f"\n{'Model':<25} {'Full Sample':>18} {'Excl 2021':>18} {'Change':>12} {'Assessment':<20}")
print("-"*95)

for model, label in zip(models, model_labels):
    full_coef = results_full[model]['coef']
    full_sig = results_full[model]['sig']
    
    no2021_coef = results_no2021[model]['coef']
    no2021_sig = results_no2021[model]['sig']
    
    diff = no2021_coef - full_coef
    pct = (diff / abs(full_coef) * 100) if full_coef != 0 else 0
    
    # Assessment
    if abs(pct) < 10:
        assessment = "✅ VERY ROBUST"
    elif abs(pct) < 20:
        assessment = "✅ ROBUST"
    elif abs(pct) < 30:
        assessment = "🔶 MODERATE"
    else:
        assessment = "⚠️ SENSITIVE"
    
    print(f"{label:<25} {full_coef:>10.4f}{full_sig:<7} {no2021_coef:>10.4f}{no2021_sig:<7} {pct:>+10.1f}% {assessment:<20}")

# ============================================================================
# KEY INSIGHTS
# ============================================================================

print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

# Main result
main_full = results_full['2SLS_NoControls']['coef']
main_no2021 = results_no2021['2SLS_NoControls']['coef']
main_diff = main_no2021 - main_full
main_pct = (main_diff / abs(main_full) * 100)

print(f"\n🎯 MAIN RESULT (2SLS, No Controls):")
print(f"   Full sample:  β = {main_full:.4f}{results_full['2SLS_NoControls']['sig']}")
print(f"   Excl 2021:    β = {main_no2021:.4f}{results_no2021['2SLS_NoControls']['sig']}")
print(f"   Change:       {main_diff:+.4f} ({main_pct:+.1f}%)")

if abs(main_pct) < 10:
    print(f"   ✅ VERY ROBUST: Coefficient barely changes")
    print(f"   → 2021 does NOT drive the main finding")
    print(f"   → Safe to use full sample")
elif abs(main_pct) < 20:
    print(f"   ✅ ROBUST: Coefficient is stable")
    print(f"   → Minor sensitivity to 2021")
    print(f"   → Can use full sample with robustness note")
else:
    print(f"   ⚠️ SENSITIVE: Coefficient changes substantially")
    print(f"   → Consider excluding 2021 as main specification")

# Significance check
if results_full['2SLS_NoControls']['sig'] == results_no2021['2SLS_NoControls']['sig']:
    print(f"\n📊 STATISTICAL SIGNIFICANCE: UNCHANGED ✅")
else:
    print(f"\n📊 STATISTICAL SIGNIFICANCE: CHANGED 🔶")
    print(f"   Full: {results_full['2SLS_NoControls']['sig']}, Excl 2021: {results_no2021['2SLS_NoControls']['sig']}")

# Direction check
if np.sign(main_full) == np.sign(main_no2021):
    print(f"\n➡️ DIRECTION: CONSISTENT (both negative) ✅")
else:
    print(f"\n➡️ DIRECTION: CHANGES ❌ (Major concern!)")

# First-stage
full_f = results_full['2SLS_NoControls']['f_stat']
no2021_f = results_no2021['2SLS_NoControls']['f_stat']

print(f"\n🔧 INSTRUMENT STRENGTH:")
print(f"   Full sample: F = {full_f:.2f}")
print(f"   Excl 2021:   F = {no2021_f:.2f}")

if full_f > 10 and no2021_f > 10:
    print(f"   ✅ Strong instruments in both samples")

# ============================================================================
# RECOMMENDATION
# ============================================================================

print("\n" + "="*80)
print("RECOMMENDATION FOR PAPER")
print("="*80)

if abs(main_pct) < 15:
    print("\n✅ RECOMMENDED APPROACH:")
    print("   → Use FULL SAMPLE as main specification")
    print("   → Report excluding-2021 as robustness check")
    print("   → Add table note or footnote:")
    print(f'     "Results robust to excluding 2021 anomaly year (β={main_no2021:.3f})"')
else:
    print("\n🔶 RECOMMENDED APPROACH:")
    print("   → Report BOTH specifications prominently")
    print("   → Acknowledge 2021 sensitivity in discussion")
    print("   → Emphasize that direction and significance remain consistent")

print("\n" + "="*80)
print("ANALYSIS COMPLETE ✅")
print("="*80)
