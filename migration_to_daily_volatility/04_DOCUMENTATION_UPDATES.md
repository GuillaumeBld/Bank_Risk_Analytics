# Documentation Updates
## dd_and_pd.md - Changes Required

**File**: `docs/writing/dd_and_pd.md`  
**Estimated Time**: 1-2 hours  
**Difficulty**: Easy

---

## 📋 What Needs to Change

### Summary of Changes

1. **Methodology Section**: Update volatility calculation description
2. **Data Section**: Update data sources table
3. **References**: Add Bharath & Shumway (2008) citation
4. **Remove**: Any references to "3-year rolling annual"

---

## 🎯 Specific Changes

### CHANGE 1: Methodology Section

**Location**: Around line 50-80

**FIND THIS**:
```markdown
### Equity Volatility Calculation

We calculate equity volatility (σ_E) using a 3-year rolling window of annual returns:

σ_{E,t-1} = SD(r_{t-1}, r_{t-2}, r_{t-3})

This ensures we only use historical data available at time t.
```

**REPLACE WITH**:
```markdown
### Equity Volatility Calculation

Following Bharath and Shumway (2008), we calculate equity volatility (σ_E) using
daily stock returns from the year prior to the observation year:

σ_{E,t-1} = SD(daily log returns in year t-1) × √252

**Implementation**:
- **Data**: Daily total returns including dividends
- **Window**: All trading days in year t-1 (approximately 252 days)
- **Minimum**: 180 trading days required (70% of year)
- **Annualization**: Scale daily standard deviation by √252
- **Log Returns**: r_d = ln(1 + R_d) for normality

**Fallback Methods**:
1. **Partial Year** (90-179 days): Use available data with flag
2. **Peer Median** (<90 days): Use median of same-size banks

This approach ensures:
- **No look-ahead bias**: Only uses data from year t-1
- **Academic standard**: Matches Bharath & Shumway (2008) methodology
- **Market responsiveness**: Captures recent volatility dynamics
```

---

### CHANGE 2: Data Sources Table

**Location**: Around line 100-120

**FIND THIS**:
```markdown
| Data Type | Source | Period | Description |
|-----------|--------|--------|-------------|
| **Total Returns** | CRSP | 2013-2023 | Monthly total returns including dividends (3-year lookback) |
```

**REPLACE WITH**:
```markdown
| Data Type | Source | Period | Description |
|-----------|--------|--------|-------------|
| **Total Returns** | CRSP | 2015-2023 | Daily total returns including dividends (252-day window) |
```

---

### CHANGE 3: Add Method Comparison Table

**Location**: Add after methodology section

**ADD THIS NEW SECTION**:
```markdown
### Volatility Calculation: Daily vs Annual Methods

| Aspect | Previous (Annual) | Current (Daily) |
|--------|------------------|-----------------|
| **Frequency** | Annual returns | Daily returns |
| **Window** | 3 years (t-1, t-2, t-3) | 1 year (year t-1 only) |
| **Observations** | 3 annual observations | ~252 daily observations |
| **Annualization** | None (already annual) | ×√252 |
| **Minimum Data** | 2 years | 180 trading days |
| **Literature Support** | Ad-hoc | Bharath & Shumway (2008) |
| **Market Sensitivity** | Lower (3-year average) | Higher (recent dynamics) |

The daily method is now standard in default prediction literature and provides:
- **Better crisis detection**: Captures 2008, COVID-19 volatility spikes
- **Academic rigor**: Can cite specific methodology
- **Temporal precision**: Uses only relevant recent data
```

---

### CHANGE 4: Update Distance to Default Formula

**Location**: Wherever DD formula appears

**ENSURE IT SHOWS**:
```markdown
### Distance to Default Calculation

**Accounting Approach**:
DD_a = (ln(V_a/F) + (μ - 0.5σ²_V) × T) / (σ_V × √T)

Where:
- V_a = E + F (naive asset value)
- σ_V = σ_E × (E/(E+F)) (naive asset volatility)
- **σ_E calculated from daily returns** (252-day window)

**Market Approach**:
DD_m = (ln(V_m/F) + (r_f - 0.5σ²_V) × T) / (σ_V × √T)

Where:
- V_m, σ_V solved from Merton equations
- **σ_E input from daily returns** (252-day window)
```

---

### CHANGE 5: References Section

**Location**: End of document

**ADD THIS CITATION**:
```markdown
## References

**Bharath, S. T., & Shumway, T. (2008).**  
*Forecasting default with the Merton distance to default model.*  
The Review of Financial Studies, 21(3), 1339-1369.  
[https://doi.org/10.1093/rfs/hhn044](https://doi.org/10.1093/rfs/hhn044)

**Key Methodology**: This paper establishes the standard for equity volatility 
calculation in default prediction models:
- Daily stock returns over past year (252 trading days)
- Log returns for distributional properties
- Standard deviation annualized by √252
- Minimum data requirements and fallback procedures
```

---

### CHANGE 6: Remove Old References

**SEARCH AND REMOVE**:
- Any mention of "3-year rolling"
- Any mention of "annual return volatility"
- Any phrase like "using 3 years of data"

**REPLACE WITH**:
- "252-day daily return window"
- "daily return volatility"
- "using year t-1 daily data"

---

## 🔍 Search & Replace Guide

### Use Your Editor's Find & Replace

```bash
# In your text editor (VS Code, etc.)

# Find: "3-year rolling"
# Replace: "252-day daily"

# Find: "annual returns"  (in volatility context)
# Replace: "daily returns"

# Find: "rolling window of returns"
# Replace: "252-day window of daily returns"
```

---

## ✅ Verification Checklist

### Content Check
- [ ] No mentions of "3-year" in volatility context
- [ ] All references say "daily" or "252-day"
- [ ] Bharath & Shumway (2008) cited
- [ ] Method comparison table included

### Accuracy Check
- [ ] Formula shows ×√252
- [ ] Mentions 180-day minimum
- [ ] Describes fallback methods
- [ ] Explains no look-ahead bias

### Formatting Check
- [ ] Tables formatted correctly
- [ ] Citations properly formatted
- [ ] Code blocks display correctly
- [ ] Links work (if any)

---

## 📝 Additional Documents to Update

### 1. EQUITY_VOLATILITY_EXPLANATION.md

**File**: `docs/guides/EQUITY_VOLATILITY_EXPLANATION.md`

**Changes**:
```markdown
# Line 13: Change title
- OLD: σ_{E,t-1} = 3-year rolling standard deviation of annual returns (rit)
+ NEW: σ_{E,t-1} = Standard deviation of daily returns (252-day window)

# Line 16-20: Update characteristics
- **Window**: 252 trading days (year t-1)
- **Input**: Daily total returns (including dividends)
- **Timing**: Uses ONLY year t-1 data
- **Min periods**: 180 trading days minimum
- **Source**: Daily stock return data
- **Annualization**: Daily SD × √252
```

### 2. README.md

**File**: `README.md` (root directory)

**Add Section**:
```markdown
## Methodology

### Equity Volatility Calculation

We follow **Bharath & Shumway (2008)** for equity volatility estimation:
- **Data**: Daily total returns from year t-1
- **Window**: 252 trading days (1 year)
- **Formula**: σ_E = SD(daily log returns) × √252
- **Fallbacks**: Peer median for insufficient data

This represents the academic standard in default prediction literature.
```

### 3. Market_approach Reference

**File**: `docs/reference/Market_approach`

**Update Line 11-12**:
```markdown
	•	market_cap → equity value E in USD
	•	equity_vol → σ_E annualized, decimal (from daily returns, 252-day window)
	•	debt_total_usd or configured barrier F in USD
```

---

## 📊 Before/After Example

### BEFORE (Old Documentation)

```markdown
## Data

We use 3-year rolling windows of annual returns to calculate equity volatility.
This provides a robust measure using historical data from years t-1, t-2, and t-3.

Volatility = SD(r_{t-1}, r_{t-2}, r_{t-3})

Minimum 2 years of data required.
```

### AFTER (New Documentation)

```markdown
## Data

We use daily returns from year t-1 to calculate equity volatility following
Bharath & Shumway (2008). This captures recent market dynamics with 252 
trading day observations.

Volatility = SD(daily log returns in year t-1) × √252

Minimum 180 trading days required (70% of year). Fallback to peer median 
if insufficient data.

**Citation**: Bharath, S. T., & Shumway, T. (2008). Forecasting default 
with the Merton distance to default model. *The Review of Financial Studies*, 
21(3), 1339-1369.
```

---

## ✅ Completion

After all updates:

```bash
# Preview changes
git diff docs/writing/dd_and_pd.md

# Commit changes
git add docs/
git commit -m "Update documentation: switch to daily volatility methodology (Bharath & Shumway 2008)"
```

---

## 📚 Full Citation Format

**For LaTeX/BibTeX**:
```bibtex
@article{bharath2008forecasting,
  title={Forecasting default with the Merton distance to default model},
  author={Bharath, Sreedhar T and Shumway, Tyler},
  journal={The Review of Financial Studies},
  volume={21},
  number={3},
  pages={1339--1369},
  year={2008},
  publisher={Oxford University Press}
}
```

**For APA**:
```
Bharath, S. T., & Shumway, T. (2008). Forecasting default with the Merton 
distance to default model. The Review of Financial Studies, 21(3), 1339-1369.
```

---

**→ Next**: Review your updated `dd_and_pd.md` and ensure all changes are complete!
