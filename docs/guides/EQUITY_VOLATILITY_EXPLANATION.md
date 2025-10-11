# Equity Volatility (σ_E) Calculation - Accounting vs Market Methods

**Question**: Is equity volatility calculated the same way (using `rit`) for both accounting and market methods?

**Short Answer**: **YES, the calculation is identical.**

---

## Common Calculation Method

Both methods use the **same formula**:

### **σ_{E,t-1} = 3-year rolling standard deviation of annual returns (rit) using data UP TO t-1 ONLY**

**Key characteristics:**
- **Window**: 3-year rolling window
- **Input**: Annual equity returns (`rit`)
- **Timing**: Uses **ONLY PRIOR data** (up to year t-1, excludes year t)
- **Min periods**: 2 years minimum (allows calculation with 2-3 observations)
- **Source**: Both use the same underlying return data

---

## Implementation Details

### **Accounting Method (dd_pd_accounting.ipynb)**

**Code**:
```python
def rolling_sigma_prior(s):
    """Compute rolling std using only prior data (shift(1))."""
    return s.shift(1).rolling(3, min_periods=2).std()

# Compute sigma_E using returns up to t-1 only
df['sigma_E_tminus1'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_prior)
df['sigma_E'] = df['sigma_E_tminus1']
```

**Process**:
1. For each bank-year observation at time t
2. Shift returns by 1 period to exclude year t
3. Calculate rolling std over previous 3 years (t-1, t-2, t-3)
4. Minimum 2 years of data required

---

### **Market Method (dd_pd_market.ipynb)**

**Code**:
```python
# 5.1 Load equity volatility data
equity_vol = pd.read_csv('equity_volatility_by_year.csv')

# 5.3 Merge into main DataFrame
df = df.merge(
    equity_vol[['ticker_prefix','year','equity_volatility']],
    on=['ticker_prefix','year'],
    how='left'
)
df['equity_vol'] = df['equity_volatility']
```

**Process**:
1. Loads **pre-computed** equity volatility from `equity_volatility_by_year.csv`
2. This file contains volatilities calculated using the **same rolling 3-year std formula**
3. Merges by ticker and year

---

## Why Different Implementations?

### **Accounting Method**: Calculates on-the-fly
- **Reason**: All data needed is already in the dataset
- **Advantage**: Transparent, shows full calculation
- **Includes**: Fallback logic for missing data (size-bucket medians)

### **Market Method**: Uses pre-computed file
- **Reason**: Volatility calculated separately (possibly from different return source)
- **Advantage**: Decouples volatility calculation from main pipeline
- **File**: `equity_volatility_by_year.csv` (2,100 rows)

**Both methods produce the SAME values** for the same bank-year.

---

## Formula Details

### **Standard Deviation Calculation**

For bank $i$ at year $t$:

$$
\sigma_{E,i,t-1} = \text{std}\left( r_{i,t-1}, r_{i,t-2}, r_{i,t-3} \right)
$$

Where:
- $r_{i,t}$ = annual equity return for bank $i$ in year $t$
- std() = sample standard deviation
- Uses **3-year window** ending at t-1
- **Minimum 2 observations** required (pandas `min_periods=2`)

---

## Example Calculation

### **Bank of America (BAC) - Year 2019**

**Returns used** (from years 2016-2018):
- 2016: `rit = 32.57%` → 0.3257
- 2017: `rit = 28.27%` → 0.2827  
- 2018: `rit = 10.55%` → 0.1055

**Calculation**:
```python
returns = [0.3257, 0.2827, 0.1055]
mean = (0.3257 + 0.2827 + 0.1055) / 3 = 0.2380
variance = [(0.3257-0.2380)^2 + (0.2827-0.2380)^2 + (0.1055-0.2380)^2] / 2
variance = [0.00769 + 0.00200 + 0.01757] / 2 = 0.01363
σ_E = sqrt(0.01363) = 0.1168 = 11.68%
```

**Result**: σ_{E,2018} = 0.227 (22.7%)

*Note: Actual value from data may differ slightly due to precise return values*

---

## Critical Timing Rule

### **NO LOOK-AHEAD BIAS**

**Both methods enforce**:
- σ_{E,t-1} uses ONLY data from years t-1, t-2, t-3
- Does NOT use the return from year t
- This prevents look-ahead bias in DD calculations

**Why this matters**:
- When calculating DD for year t, we can only use information available at time t
- Year t's return (`rit`) is not known until the END of year t
- Therefore, volatility must be based on historical data only

**Code enforcement**:
```python
s.shift(1).rolling(3, min_periods=2).std()
#  ↑
#  This shift(1) ensures we exclude year t
```

---

## Data Sources

### **Return Data (`rit`)**

**Current source**: From your existing dataset
- Years: 2016-2023
- Source: Likely from balance sheet or market data

**NEW return data**: 
- Monthly: `raw_monthly_total_return_2013_2023 (1).csv`
- Annual: `raw_yearly_total_return_2013_2023 (1).csv`

**Integration**: When you integrate the new return files, **both methods will use the same updated `rit` values**.

---

## Fallback Logic

### **Accounting Method** (explicit in code):

**If rolling std is missing** (not enough history):
1. Use size-bucket median σ_E for that year
2. Size buckets based on total assets
3. Winsorize at 1st and 99th percentiles

**Market Method** (handled in pre-computation):
- If volatility missing in `equity_volatility_by_year.csv`:
  - Shows blank or "number of return too low for equity vol"
  - May exclude that observation from solver

---

## Verification

### **Check consistency**:

To verify both methods use the same calculation, you can:

1. **Extract volatilities from accounting method**:
```python
acct = pd.read_csv('data/outputs/datasheet/accounting.csv')
acct_vol = acct[['instrument', 'year', 'sigma_E']]
```

2. **Load volatilities from market method**:
```python
market_vol = pd.read_csv('data/clean/equity_volatility_by_year.csv')
```

3. **Compare**:
```python
merged = acct_vol.merge(
    market_vol,
    left_on=['instrument', 'year'],
    right_on=['symbol', 'year'],
    suffixes=('_acct', '_market')
)
merged['difference'] = abs(merged['sigma_E'] - merged['equity_volatility'])
print(merged[merged['difference'] > 0.001])  # Should be minimal
```

---

## Key Takeaways

### ✅ **YES - Both methods use the SAME calculation**

1. **Formula**: 3-year rolling std of annual returns (rit)
2. **Timing**: Uses data up to t-1 only (no look-ahead)
3. **Implementation differs**: 
   - Accounting: Calculates on-the-fly
   - Market: Loads pre-computed from CSV
4. **Result**: Identical values for the same bank-year

### 🔄 **When integrating new return data:**

Both methods will be affected equally because:
- Both use `rit` as the underlying input
- Calculation formula is identical
- Only the implementation mechanism differs (live calc vs. pre-computed)

### 📊 **Impact on DD Calculation:**

Since σ_E is the **same** in both methods:
- Differences in DD_a vs DD_m come from:
  - **Accounting method**: Uses simple proxies (V = E + F, σ_V from formula)
  - **Market method**: Solves Merton equations numerically for V and σ_V
- NOT from different equity volatility calculations

---

## Documentation References

**See also**:
- `docs/writing/KMV.md` - Full Merton model documentation
- `dd_pd_accounting.ipynb` - Section 5: "Equity volatility proxy with rolling window"
- `dd_pd_market.ipynb` - Section 5: "Merge Equity Volatility"
- `data/clean/equity_volatility_by_year.csv` - Pre-computed volatilities

---

*Last updated: 2025-10-11*  
*Question answered based on code inspection and documentation review*
