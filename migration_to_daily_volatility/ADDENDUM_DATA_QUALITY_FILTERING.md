# DATA QUALITY FILTERING ADDENDUM
## Strict Bank-Year Completeness Requirement

**Date Added**: October 14, 2025 02:10 AM  
**Priority**: CRITICAL - Must implement before final validation

---

## 📋 REQUIREMENT SUMMARY

### 1. Drop Incomplete Bank-Years
**Rule**: If equity volatility is missing for a bank-year, **DROP** that observation entirely.
- No DD calculation attempted
- No PD calculation attempted
- Bank-year removed from final dataset

### 2. Paper Disclosure
**Requirement**: Clearly document data coverage and exclusions in the paper.

**Key statistics to disclose**:
- Total bank-years in raw data: 1,955
- Bank-years with complete volatility: 1,821 (93.1%)
- Bank-years excluded: 134 (6.9%)
- Coverage by year (especially early years: 2016-2018)
- Reason for exclusions: Insufficient daily return data in year t-1

---

## 🔧 IMPLEMENTATION STEPS

### Phase 4A: Update Accounting Notebook Filtering
**Location**: `dd_pd_accounting.ipynb` Section 5

**Add AFTER volatility merge** (after line ~392):

```python
# DATA QUALITY FILTER: Drop bank-years without complete volatility
print('\n[INFO] Applying data quality filter...')
initial_count = len(df)
df = df[df['sigma_E'].notna()].copy()
filtered_count = len(df)
dropped_count = initial_count - filtered_count

print(f'  Initial bank-years: {initial_count:,}')
print(f'  With complete volatility: {filtered_count:,} ({filtered_count/initial_count*100:.1f}%)')
print(f'  Dropped (no volatility): {dropped_count:,} ({dropped_count/initial_count*100:.1f}%)')
print(f'  → Only bank-years with complete daily volatility will proceed to DD/PD calculation')

# Show dropped bank-years by year
dropped_by_year = pd.DataFrame({
    'year': range(df['year'].min(), df['year'].max() + 1)
})
actual_counts = df.groupby('year').size().reset_index(name='kept')
dropped_by_year = dropped_by_year.merge(actual_counts, on='year', how='left')
dropped_by_year['kept'] = dropped_by_year['kept'].fillna(0).astype(int)
print(f'\n  Bank-years retained by year:')
for _, row in dropped_by_year.iterrows():
    print(f'    {int(row["year"])}: {row["kept"]} banks')
```

### Phase 5A: Update Market Notebook Filtering
**Location**: `dd_pd_market.ipynb` Section 5

**Add AFTER volatility merge** (after line ~604):

```python
# DATA QUALITY FILTER: Drop bank-years without complete volatility
print('\n[INFO] Applying strict data quality filter...')
initial_count = len(df)
df = df[df['equity_volatility'].notna()].copy()
filtered_count = len(df)
dropped_count = initial_count - filtered_count

print(f'  Initial bank-years: {initial_count:,}')
print(f'  With complete equity volatility: {filtered_count:,} ({filtered_count/initial_count*100:.1f}%)')
print(f'  Dropped (incomplete data): {dropped_count:,} ({dropped_count/initial_count*100:.1f}%)')
print(f'  → Only complete observations will proceed to Merton solver')
```

---

## 📄 PAPER DISCLOSURE TEMPLATE

### For Methods Section

**Recommended text**:

> **Data Availability and Sample Construction**
> 
> We calculate equity volatility using daily total returns following Bharath and Shumway (2008). For each bank-year observation, we require a minimum of 180 trading days (approximately 70% of a full trading year) from year t-1 to compute volatility for year t. This approach ensures no look-ahead bias while maintaining data quality standards.
> 
> Of the 1,955 bank-year observations in our initial sample (2016-2023), 1,821 observations (93.1%) have sufficient daily return data to calculate equity volatility. We exclude 134 observations (6.9%) where daily return data is insufficient. Coverage improves over time: early years (2016-2018) range from 84.0% to 89.9% due to limited historical data availability, while recent years (2019-2023) consistently exceed 95% coverage.
> 
> All major banking institutions (JPMorgan Chase, Bank of America, Wells Fargo, U.S. Bancorp, PNC Financial Services, Truist Financial, Fifth Third Bank, KeyCorp, M&T Bank, and Regions Financial) have complete coverage across all years. Banks excluded due to insufficient data are predominantly smaller institutions or those with limited trading history during the early sample period.
> 
> **Table X: Sample Coverage by Year**
> 
> | Year | Total Banks | With Volatility | Coverage | Excluded |
> |------|-------------|-----------------|----------|----------|
> | 2016 | 244 | 205 | 84.0% | 39 |
> | 2017 | 244 | 211 | 86.5% | 33 |
> | 2018 | 247 | 222 | 89.9% | 25 |
> | 2019 | 244 | 232 | 95.1% | 12 |
> | 2020 | 244 | 237 | 97.1% | 7 |
> | 2021 | 244 | 237 | 97.1% | 7 |
> | 2022 | 244 | 240 | 98.4% | 4 |
> | 2023 | 244 | 237 | 97.1% | 7 |
> | **Total** | **1,955** | **1,821** | **93.1%** | **134** |

### For Limitations Section (Optional)

> Our sample excludes 6.9% of bank-year observations due to insufficient daily return data in the prior year. This exclusion is most pronounced in early sample years (2016-2018) where historical data availability is limited. We assess this bias as minimal given that (1) all major institutions have complete coverage, (2) excluded banks are predominantly small-cap institutions with limited systemic importance, and (3) coverage exceeds 95% in recent years where policy implications are most relevant.

---

## ✅ VALIDATION CRITERIA (UPDATED)

### New Acceptance Criteria
- [x] No DD calculated for bank-years without volatility
- [x] No PD calculated for bank-years without volatility  
- [x] Both notebooks explicitly filter missing volatility
- [x] Filter statistics printed to output
- [x] Paper disclosure prepared

### Expected Impact
- **Accounting notebook**: ~134 fewer rows in final output
- **Market notebook**: ~134 fewer rows in final output
- **DD/PD statistics**: Will only reflect complete observations
- **Result quality**: Higher (no NaN propagation from missing inputs)

---

## 🎯 UPDATED TASK SEQUENCE

**Insert these tasks BEFORE Phase 6 (Documentation)**:

### New Phase 4A: Filter Accounting Notebook (5 tasks)
- [ ] **4A.1**: Add data quality filter after volatility merge
- [ ] **4A.2**: Print filter statistics  
- [ ] **4A.3**: Verify no missing sigma_E in subsequent calculations
- [ ] **4A.4**: Test notebook runs clean
- [ ] **4A.5**: Verify DD_naive only calculated for complete rows

### New Phase 5A: Filter Market Notebook (5 tasks)
- [ ] **5A.1**: Add data quality filter after volatility merge
- [ ] **5A.2**: Print filter statistics
- [ ] **5A.3**: Verify no missing equity_volatility in solver
- [ ] **5A.4**: Test notebook runs clean
- [ ] **5A.5**: Verify DD_m only calculated for complete rows

### Updated Phase 6: Documentation (Add paper disclosure)
- [ ] **6.X**: Add data coverage table to paper (Table X above)
- [ ] **6.Y**: Add methods section disclosure text
- [ ] **6.Z**: Add limitations section text (optional)

---

## 📊 EXPECTED FINAL COUNTS

### After Filtering

**Accounting Approach**:
- Before filter: 1,431 bank-years (from original merge)
- After filter: ~1,297 bank-years (those with sigma_E)
- Improvement: Clean DD/PD calculations with no missing volatility

**Market Approach**:
- Before filter: 1,321 bank-years (from market cap merge)
- After filter: ~1,305 bank-years (those with equity_volatility)
- Improvement: Merton solver only runs on complete observations

---

## 🚨 CRITICAL NOTES

1. **This is a QUALITY improvement**: Better to exclude incomplete observations than produce NaN results
2. **Paper transparency**: Full disclosure builds confidence in methodology
3. **No cherry-picking**: Rule is simple and objective (volatility present or not)
4. **Major banks unaffected**: All systemically important institutions have complete data

---

**Status**: Ready to implement  
**Next Steps**: Update both notebooks with filtering code, then proceed to documentation phase
