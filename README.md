# ESG Risk for Banks Research Project

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](logs/INSTRUCTION_3_COMPLETE.md)
[![Version](https://img.shields.io/badge/Version-3.0-blue.svg)](docs/admin/PUSH_SUMMARY.md)
[![Validated](https://img.shields.io/badge/Solver-100%25_Convergence-success.svg)](logs/INSTRUCTION_3_COMPLETE.md)
[![Coverage](https://img.shields.io/badge/Coverage-90.6%25-green.svg)](data/outputs/datasheet/esg_dd_pd_20251011_043202.csv)

**Lead Researcher**: Guillaume Bolivard | **Faculty Advisor**: Dr. Abol Jalilvand | **Institution**: Loyola University Chicago

> **Abstract**: This research develops and validates a comprehensive framework for assessing default risk in banking institutions through both market-based (Merton model) and accounting-based (Bharath-Shumway naive) approaches. The study incorporates Environmental, Social, and Governance (ESG) factors into credit risk analysis for U.S. banks over the period 2016-2023. Our improved equity volatility methodology with hierarchical fallbacks and complete provenance tracking achieves 100% convergence rates and 90.6% data coverage across 244 unique banking institutions. All methodological specifications, validation procedures, and econometric designs presented herein were developed under the supervision of Dr. Abol Jalilvand.

---

## 🔬 Research Methodology

### Validation & Quality Assurance

**Current Status**: ✅ **PRODUCTION READY** - Version 3.0 | Research Review Ready

| Metric | Value | Status |
|--------|-------|--------|
| **Version** | 3.0 (October 11, 2025) | ✅ Latest |
| **Convergence Rate** | 100% (1,290/1,290) | ✅ Perfect |
| **Sample Coverage** | 1,290/1,424 (90.6%) | ✅ Excellent |
| **Total Observations** | 1,424 bank-years | ✅ Complete |
| **Period Coverage** | 2016-2023 (8 years) | ✅ Comprehensive |
| **Unique Banks** | 244 institutions | ✅ Robust |
| **Data Quality** | Tier 1: 92% | ✅ High |
| **Time Integrity** | No lookahead bias | ✅ Verified |
| **Documentation** | >2,000 lines | ✅ Publication-ready |

**Key Achievements (Version 3.0)**:
- ✅ **100% convergence rate** achieved through improved equity volatility methodology
- ✅ **90.6% coverage** (1,290/1,424 observations) with hierarchical volatility estimation
- ✅ **Comprehensive methodology** documented in 247-line academic paper section
- ✅ **Complete provenance tracking** for all volatility estimates (method, window, obs_count)
- ✅ **Time integrity guaranteed** with strict t-1 window endings (no lookahead bias)
- ✅ **Clean, reproducible pipeline** from CRSP data to final DD/PD estimates

**Validation Reports**:
- Complete validation: [`logs/INSTRUCTION_3_COMPLETE.md`](logs/INSTRUCTION_3_COMPLETE.md) (358 lines)
- Methodology paper: [`docs/writing/dd_and_pd.md`](docs/writing/dd_and_pd.md) (970 lines, v3.0)
- Dataset alignment: [`logs/PAPER_DATASET_ALIGNMENT_COMPLETE.md`](logs/PAPER_DATASET_ALIGNMENT_COMPLETE.md) (318 lines)

---

## Research Overview

### Motivation and Objectives

The banking sector's exposure to ESG-related risks necessitates rigorous quantitative frameworks for default probability estimation. This study addresses this need by implementing two complementary methodologies for credit risk measurement, each validated through comprehensive diagnostic procedures:

### **Market-Based Approach (Merton Model)**
- Solves the Merton KMV model using equity market data
- Estimates asset value (V_t) and volatility (σ_V,t) through Newton-Raphson optimization
- Computes market-implied DD (DD_m) and PD (PD_m)
- Uses risk-free rate as drift parameter (μ = r_f) under Q-measure
- **100% convergence rate** on observations with sufficient data

### **Accounting-Based Approach (Bharath-Shumway Naive DD)**
- Implements the naive distance-to-default methodology
- Uses accounting proxies without numerical solvers
- Computes accounting-based DD (DD_a) and PD (PD_a)
- Leverages balance sheet and market equity data
- **90.6% coverage** across full sample

### **Equity Volatility Methodology** (New in v3.0)
- **Primary method**: 36-month rolling standard deviation (~98% coverage)
- **Fallback 1**: EWMA for limited data (λ=0.94, ~1-2% coverage)
- **Fallback 2**: Peer median by size bucket (<1% coverage)
- **Complete provenance tracking**: method, window months, start/end years
- **Time integrity**: All windows end strictly at t-1 (no lookahead bias)
- **Quality tiers**: Tier 1 (92%), Tier 2 (0%), Tier 3 excluded (8%)

### **Research Objectives**

1. Develop numerically stable implementations of market-based (Merton KMV) and accounting-based (Bharath-Shumway) distance-to-default models
2. Establish comprehensive validation framework ensuring time-series integrity and preventing lookahead bias
3. Estimate default risk metrics for U.S. commercial banking institutions over 2016-2023
4. Investigate the empirical relationship between ESG performance metrics and credit risk indicators
5. Conduct comparative analysis of market-implied versus accounting-based risk measures
6. Perform rigorous sensitivity analysis examining solver parameters and alternative methodologies
7. Execute econometric specifications including instrumental variables, fixed effects, and robust standard errors

### **Methodological Framework**

The computational implementation employs a structured development approach:

1. **Algorithm Specification**: All numerical procedures, optimization frameworks, and econometric models specified according to established academic literature with novel adaptations for numerical stability

2. **Implementation Strategy**: Code generation leverages AI-assisted development tools under direct researcher supervision, ensuring rapid prototyping while maintaining reproducibility standards

3. **Validation Protocol**: Comprehensive testing framework validates (i) numerical convergence, (ii) time-series integrity, (iii) parameter sensitivity, and (iv) comparison with alternative methodologies

4. **Documentation Standards**: Automated generation of technical reports ensures transparency, reproducibility, and adherence to computational finance best practices

This approach maintains rigorous academic standards while enhancing development efficiency, enabling focus on methodological innovation and empirical interpretation.

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

### **Numerical Stability & Accuracy**
- Log-space parameterization ensures non-negativity constraints for asset values and volatilities
- Bounded d1/d2 calculations prevent numerical overflow in cumulative normal distribution evaluations  
- Robust loss function (soft_l1) provides resistance to outlier observations
- Convergence criterion achieves machine precision (residuals < 10^-10)
- Comprehensive diagnostic framework validates solver performance across parameter space

### **Time-Series Integrity Protocol**
- Equity volatility (σ_{E,t-1}): Estimated using returns from period [t-252, t-1] exclusively
- Market equity (E_t), face value of debt (F_t), risk-free rate (r_{f,t}): Values as of time t
- Asset value (V_t) and asset volatility (σ_{V,t}): Solved at time t conditional on information available through t-1
- Distance-to-default (DD_{m,t}) and default probability (PD_{m,t}): Computed at time t
- Automated test suite validates absence of lookahead bias (8/8 specifications verified)

### **Timestamped Outputs**
- All outputs use format: `{type}_YYYYMMDD_HHMMSS.csv` (CDT timezone)
- Enables version tracking and reproducibility
- Automatic archiving (max 5 files per type)

### **Column Naming Convention**
- **Accounting variables**: Prefixed with `a_*`
- **Market variables**: Prefixed with `m_*`
- **Final metrics**: `DD_a`, `PD_a`, `DD_m`, `PD_m` (unprefixed)
- Provenance columns track data sources and calculation methods

### **Data Quality & Validation**
- Solver status tracking (converged, no_sigma_E, validation failures)
- Pre-solve validation filters invalid inputs
- Outlier categorization (zero-cost debt, low leverage, etc.)
- Missing data indicators and coverage reporting
- Comprehensive diagnostic reports

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

## Technical Stack

### Core Dependencies
```bash
pip install pandas numpy scipy statsmodels matplotlib seaborn pytz linearmodels
```

### Package Versions (Tested)
- Python 3.11+
- pandas 2.2+
- numpy 2.0+
- scipy 1.16+
- statsmodels 0.14.5
- linearmodels 6.1
- matplotlib 3.10+
- seaborn (latest)

### Development Tools
- Jupyter Notebook/Lab for interactive analysis
- Git for version control
- pytest for automated testing (optional)

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

## Research Attribution and Methodology

**Principal Investigator**: Guillaume Bolivard  
*Quinlan School of Business, Loyola University Chicago*

**Faculty Supervisor**: Dr. Abol Jalilvand  
*Quinlan School of Business, Loyola University Chicago*

### Intellectual Contributions

All research design elements, including algorithm specifications, validation frameworks, econometric model designs, and empirical interpretations, were developed by the principal investigator under faculty supervision. The computational implementation leverages AI-assisted code generation as a development tool, analogous to the use of specialized software libraries or computational platforms in quantitative finance research.

### Development Protocol

**Research Design Phase**: Specification of numerical algorithms, optimization procedures, validation protocols, and econometric models according to established literature with methodological enhancements

**Implementation Phase**: Translation of specifications into executable code using AI-assisted development tools under direct researcher oversight, ensuring adherence to design specifications

**Validation Phase**: Comprehensive testing including convergence analysis, numerical stability verification, time-series integrity checks, and comparison with alternative methodologies

**Documentation Phase**: Generation of technical reports, diagnostic summaries, and reproducibility documentation

This workflow maintains rigorous academic standards and full intellectual attribution while employing modern computational tools to enhance research efficiency and code maintainability.

## Documentation

### Technical Reports
- [`docs/SOLVER_DIAGNOSTIC_REPORT.md`](docs/SOLVER_DIAGNOSTIC_REPORT.md) - Comprehensive solver validation
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) - Current project status and progress
- [`tests/test_time_tags.py`](tests/test_time_tags.py) - Automated time-integrity tests

### Key Files
- `dd_pd_market.ipynb` - Market-based Merton model implementation
- `dd_pd_accounting.ipynb` - Accounting-based naive DD implementation  
- `merging.ipynb` - Dataset integration pipeline
- `analysis.ipynb` - Econometric analysis (OLS, 2SLS, fixed effects)
- `solver_diagnostics.ipynb` - Solver sensitivity and validation analysis

## Academic References

### Primary Methodologies
- Merton, R. C. (1974). "On the Pricing of Corporate Debt: The Risk Structure of Interest Rates." *Journal of Finance*, 29(2), 449-470.
- Bharath, S. T., & Shumway, T. (2008). "Forecasting Default with the Merton Distance to Default Model." *Review of Financial Studies*, 21(3), 1339-1369.
- Vassalou, M., & Xing, Y. (2004). "Default Risk in Equity Returns." *Journal of Finance*, 59(2), 831-868.

### Numerical Methods
- Crosbie, P., & Bohn, J. (2003). "Modeling Default Risk." KMV Corporation.
- Powell, M. J. D. (2009). "The BOBYQA Algorithm for Bound Constrained Optimization Without Derivatives." *Cambridge NA Report*.

### ESG and Banking
- Chiaramonte, L., & Casu, B. (2017). "Capital and Liquidity Ratios and Financial Distress." *British Accounting Review*, 49(2), 138-161.
- Shakil, M. H., et al. (2019). "Do Environmental, Social and Governance Performance Affect the Financial Performance of Banks?" *Business Strategy and the Environment*, 28(8), 1446-1459.

## Contact

For inquiries or collaboration:
- **Email**: gbolivard@luc.edu
- **GitHub**: [@GuillaumeBld](https://github.com/GuillaumeBld)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
