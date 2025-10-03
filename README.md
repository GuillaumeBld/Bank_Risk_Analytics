# ESG Risk for Banks Research Project

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This repository documents research work assisting Dr. Abol Jalilvand on ESG risk assessment for banking institutions, incorporating Distance to Default (DD) and Probability of Default (PD) metrics.

## About

This research project investigates the relationship between Environmental, Social, and Governance (ESG) factors and default risk in the banking sector. We implement two complementary approaches to measure credit risk:

### **Market-Based Approach (Merton Model)**
- Solves the Merton KMV model using equity market data
- Estimates asset value and volatility through iterative optimization
- Computes market-implied DD (DD_m) and PD (PD_m)
- Uses risk-free rate as drift parameter (μ = r_f)

### **Accounting-Based Approach (Bharath-Shumway Naive DD)**
- Implements the naive distance-to-default methodology
- Uses accounting proxies without numerical solvers
- Computes accounting-based DD (DD_a) and PD (PD_a)
- Leverages balance sheet and market equity data

### **Research Objectives**
1. Calculate DD and PD metrics for U.S. banking institutions (2016-2023)
2. Analyze the relationship between ESG scores and default risk
3. Compare market-based vs. accounting-based risk measures
4. Identify outliers and data quality issues
5. Perform regression analysis with ESG variables and controls

## Project Structure

```
risk_bank/
├── dd_pd_market.ipynb          # Market-based DD/PD calculation (Merton model)
├── dd_pd_accounting.ipynb      # Accounting-based DD/PD calculation (Naive DD)
├── merging.ipynb               # Merge accounting and market datasets
├── analysis.ipynb              # Comprehensive analysis and visualizations
│
├── data/
│   ├── clean/                  # Cleaned input datasets
│   ├── outputs/
│   │   ├── datasheet/         # Timestamped DD/PD outputs
│   │   └── analysis/          # Analysis outputs and outliers
│   └── logs/                   # Execution logs
│
├── archive/
│   └── datasets/              # Archived outputs (max 5 per type)
│
├── docs/
│   ├── reference/             # Technical documentation
│   ├── literature_review/     # Research papers
│   └── writting/              # Working papers and notes
│
└── scripts/                   # Utility scripts
```

## Workflow

### **1. Calculate Distance to Default and Probability of Default**

#### Market Approach
```bash
# Run dd_pd_market.ipynb
# Outputs: market_YYYYMMDD_HHMMSS.csv
```
- Loads market cap, equity volatility, debt, and risk-free rate data
- Solves Merton model for asset value (V) and asset volatility (σ_V)
- Computes DD_m and PD_m
- Archives old files automatically

#### Accounting Approach
```bash
# Run dd_pd_accounting.ipynb
# Outputs: accounting_YYYYMMDD_HHMMSS.csv
```
- Loads balance sheet and market data
- Computes equity proxies (price-to-book, D/E, WACC weights)
- Calculates naive DD_a and PD_a using Bharath-Shumway methodology
- Archives old files automatically

### **2. Merge Datasets**
```bash
# Run merging.ipynb
# Outputs: merged_YYYYMMDD_HHMMSS.csv
```
- Loads latest accounting and market datasets
- Merges on `[instrument, year]` with outer join
- Applies prefixes: `a_*` (accounting), `m_*` (market)
- Keeps DD_a, PD_a, DD_m, PD_m unprefixed

### **3. Comprehensive Analysis**
```bash
# Run analysis.ipynb
# Outputs: Various analysis files and visualizations
```

**Includes:**
- **Visualizations**: Distributions, box plots, scatter plots, time series
- **Correlation Analysis**: Correlation matrices and heatmaps
- **OLS Regression**: With year fixed effects
- **2SLS Analysis**: Instrumental variable estimation
- **ESG Regression Analysis**:
  - ESG raw scores (environmental, social, governance)
  - ESG combined score
  - Dummy variables (size, year)
  - Control variables (lnta, td/ta, price_to_book, capital_adequacy)
  - Sequential model building
- **Outlier Detection**: Categorizes outliers by data quality issues
  - Zero-cost debt
  - Low debt (≤1M)
  - Low leverage (D/E ≤ 0.05)
  - Outputs: `outliers_accounting_*.csv`, `outliers_market_*.csv`

## Key Features

### **Timestamped Outputs**
- All outputs use format: `{type}_YYYYMMDD_HHMMSS.csv` (CDT timezone)
- Enables version tracking and reproducibility

### **Automatic Archiving**
- Old files moved to `archive/datasets/`
- Retention: Maximum 5 files per dataset type
- Prevents clutter while maintaining history

### **Column Naming Convention**
- **Accounting variables**: Prefixed with `a_*`
- **Market variables**: Prefixed with `m_*`
- **Final metrics**: `DD_a`, `PD_a`, `DD_m`, `PD_m` (unprefixed)

### **Data Quality Flags**
- Solver status tracking (converged, no_debt, invalid_inputs)
- Outlier categorization
- Missing data indicators

## Variables

### **Distance to Default (DD)**
- **DD_a**: Accounting-based distance to default
- **DD_m**: Market-based distance to default

### **Probability of Default (PD)**
- **PD_a**: Accounting-based probability of default (Φ(-DD_a))
- **PD_m**: Market-based probability of default (Φ(-DD_m))

### **ESG Variables**
- `environmental_pillar_score`
- `social_pillar_score`
- `governance_pillar_score`
- `esg_combined_score`

### **Control Variables**
- `lnta`: Log total assets
- `td/ta`: Total debt to total assets ratio
- `price_to_book_value_per_share`
- `capital_adequacy_total_(%)`: Capital adequacy ratio

### **Dummy Variables**
- `size_dummy`: 0 if total_assets ≤ 1M, 1 if > 1M
- `year_dummy`: 0 if 2016-2019, 1 if 2020-2023

## Requirements

```bash
pip install pandas numpy scipy statsmodels matplotlib seaborn pytz linearmodels
```

## Usage

1. **Clone the repository**
```bash
git clone https://github.com/GuillaumeBld/risk_bank.git
cd risk_bank
```

2. **Run the workflow**
```bash
# Step 1: Calculate market DD/PD
jupyter notebook dd_pd_market.ipynb

# Step 2: Calculate accounting DD/PD
jupyter notebook dd_pd_accounting.ipynb

# Step 3: Merge datasets
jupyter notebook merging.ipynb

# Step 4: Run analysis
jupyter notebook analysis.ipynb
```

3. **Outputs will be in:**
- `data/outputs/datasheet/` - DD/PD datasets
- `data/outputs/analysis/` - Analysis results and outliers
- `archive/datasets/` - Archived files

## Research Team

**Lead Researcher**: Guillaume Bolivard  
**Faculty Advisor**: Dr. Abol Jalilvand  
**Institution**: Loyola University Chicago

## References

- Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates"
- Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model"
- KMV Corporation (1993-2002). Credit Monitor documentation

## Contact

For inquiries or collaboration:
- **Email**: gbolivard@luc.edu
- **GitHub**: [@GuillaumeBld](https://github.com/GuillaumeBld)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
