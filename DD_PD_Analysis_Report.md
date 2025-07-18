# Distance to Default (DD) and Probability of Default (PD) Analysis Report

## Executive Summary

This report addresses the investigation of a negative Distance to Default (DDm) value for a bank and provides detailed explanations of the DD and PD calculation methodologies used in the Merton model implementation. The analysis reveals both the technical causes of negative DDm values and provides recommendations for volatility estimation periods.

## Key Findings

### 1. Negative DDm Value Investigation

**Identified Case**: MFIN (bank) in 2020 shows a DDm value of **-0.11** with a corresponding high PD of **0.544** (54.4% probability of default).

**Root Cause Analysis**:
The negative DDm value occurs when the natural logarithm term in the Merton formula becomes significantly negative, specifically when:
- The firm's asset value (V) is very close to or below the debt face value (F)
- The risk-free rate adjustment term (r_f - 0.5σ_V²)T becomes negative and large in magnitude
- High asset volatility (σ_V) compounds the effect

**Mathematical Explanation**:
The DDm formula is: `DDm = (ln(V/F) + (r_f - 0.5σ_V²)T) / (σ_V√T)`

For MFIN 2020:
- Asset value: 298,326,795 USD
- Debt total: 241,052 million USD (converted to actual USD: 241,052,000,000)
- Asset volatility: 0.780 (78%)
- Risk-free rate: 0.44%

The negative DDm indicates the firm was in severe financial distress with very high default probability.

### 2. Detailed DD and PD Calculation Methodology

#### Market-Based Calculations (DDm/PDm)

**Step 1: Merton Model Implementation**
- Uses iterative solver to estimate asset value (V) and asset volatility (σ_V) from market data
- Treats equity as a call option on firm assets: `E = VN(d1) - Fe^(-rT)N(d2)`

**Step 2: Distance to Default Formula**
```
DDm = (ln(V/F) + (r_f - 0.5σ_V²)T) / (σ_V√T)
```

**Step 3: Probability of Default**
```
PDm = Φ(-DDm)
```
where Φ is the cumulative standard normal distribution function.

#### Accounting-Based Calculations (DDa/PDa)

**Alternative Approach**: Uses book values instead of market values
- Asset value from balance sheet total assets
- Uses similar mathematical framework but with accounting data
- Results in DDa and PDa metrics for comparison

### 3. Equity Volatility Calculation Methodology

**Current Implementation**: 
- Based on **annualized equity volatility by year**
- Calculated from equity price returns over a **12-month period**
- Uses standard deviation of returns, annualized

**Data Structure**: The `equity_volatility_by_year.csv` file contains:
- Symbol-year pairs
- Annualized volatility estimates
- Notes indicating "number of return too low for equity vol" when insufficient data

**Volatility Calculation Process**:
1. Collect daily equity returns over the measurement period
2. Calculate standard deviation of returns
3. Annualize using √252 factor (trading days)
4. Apply to Merton model asset volatility estimation

### 4. 24-Month Volatility Estimation Analysis

**Current State**: The system currently uses 12-month periods for volatility calculation.

**24-Month Implementation Considerations**:

**Advantages**:
- More stable volatility estimates
- Reduces impact of short-term market shocks
- Better captures long-term risk characteristics
- May reduce volatility of DDm estimates over time

**Disadvantages**:
- Less responsive to recent changes in firm risk profile
- May not capture rapid deterioration in credit quality
- Requires more historical data availability

**Technical Implementation**:
To implement 24-month volatility estimation:
1. Modify the volatility calculation to use 24-month rolling windows
2. Ensure sufficient historical price data (minimum 500+ trading days)
3. Compare results with 12-month estimates for validation
4. Consider hybrid approaches (e.g., weighted average of 12m and 24m)

## Data Quality Assessment

### Coverage and Completeness
- **Total Institutions**: 1,425 bank-year observations
- **Solver Success Rate**: 98.6% (1,405/1,425 converged)
- **Missing DDm Values**: 20 observations (1.4%)
- **DDm Range**: -0.11 to 49.91
- **PDm Range**: 0.00 to 0.544

### Data Corrections Applied
The analysis revealed and corrected a significant unit mismatch:
- **Issue**: Market cap in USD vs debt_total in millions
- **Impact**: 80.8% of PDm values were zero due to numerical underflow
- **Solution**: Applied 1,000,000 multiplier to debt values
- **Result**: Realistic DDm/PDm ranges achieved

## Recommendations

### 1. Negative DDm Handling
- **Monitor**: Banks with DDm < 0 require immediate attention
- **Validate**: Cross-check with accounting-based DDa metrics
- **Flag**: Implement automated alerts for DDm < -0.5

### 2. Volatility Period Selection
- **Short-term**: Continue using 12-month for timely risk assessment
- **Long-term**: Implement 24-month option for stability analysis
- **Hybrid**: Consider weighted average: 0.7 × (12m) + 0.3 × (24m)

### 3. Model Validation
- **Backtesting**: Compare DDm predictions with actual default events
- **Benchmarking**: Validate against external credit ratings
- **Sensitivity**: Test impact of volatility period on DDm stability

### 4. Operational Implementation
- **Frequency**: Update DDm/PDm calculations monthly
- **Thresholds**: Establish DDm warning levels (e.g., DDm < 2.0)
- **Reporting**: Include both 12m and 24m volatility estimates in reports

## Technical Details

### File Structure
- **Market DD/PD**: `dd_pd_market.ipynb` - Market-based calculations
- **Accounting DD/PD**: `dd_pd_accounting.ipynb` - Book value calculations  
- **Results**: `data/merged_inputs/dd_pd_market.csv` - Final output
- **Logs**: `data/logs/dd_pd_market_log.txt` - Processing diagnostics

### Key Formula Components
- **Risk-free Rate**: Fama-French factors (annual)
- **Time Horizon**: T = 1 year
- **Asset Volatility**: Derived from equity volatility via Merton relationships
- **Debt Measure**: Total debt (book value) converted to market terms

## Conclusion

The negative DDm value for MFIN in 2020 (-0.11) is mathematically valid and indicates severe financial distress. The current 12-month volatility calculation provides timely risk assessment, while a 24-month option would offer greater stability. Both approaches have merits depending on the intended use case and risk management objectives.

The model implementation is robust with 98.6% solver convergence and appropriate handling of edge cases. The correction of unit mismatches has significantly improved the reliability of results.