# COMPLETE TASK LIST - Daily Volatility Migration (Part 1 of 2)
## Every Single Task Required - Pre-Migration Through Notebook Updates

**Total Tasks Part 1**: 107 tasks  
**Estimated Time**: 9-10 hours

---

## PHASE 0: PRE-MIGRATION SETUP (17 tasks, 45 minutes)

### Git & Backup Setup
- [ ] **0.1** Create git branch: `git checkout -b feature/daily-volatility`
- [ ] **0.2** Verify clean working directory: `git status`
- [ ] **0.3** Backup notebooks folder: `cp -r notebooks/ notebooks_BACKUP_$(date +%Y%m%d)/`
- [ ] **0.4** Backup data/clean folder: `cp -r data/clean/ data_BACKUP_$(date +%Y%m%d)/`
- [ ] **0.5** Backup old volatility file: `cp data/clean/equity_volatility_by_year.csv data/clean/equity_volatility_by_year.csv.OLD`
- [ ] **0.6** Verify backups exist: `ls -la notebooks_BACKUP_*/`
- [ ] **0.7** Verify backups exist: `ls -la data_BACKUP_*/`
- [ ] **0.8** Create backup timestamp file: `date > MIGRATION_START_TIME.txt`

### Environment Check
- [ ] **0.9** Verify Python 3.9+ installed: `python3 --version`
- [ ] **0.10** Verify pandas installed: `python3 -c "import pandas; print(pandas.__version__)"`
- [ ] **0.11** Verify numpy installed: `python3 -c "import numpy; print(numpy.__version__)"`
- [ ] **0.12** Verify scipy installed: `python3 -c "import scipy; print(scipy.__version__)"`
- [ ] **0.13** Verify matplotlib installed: `python3 -c "import matplotlib; print(matplotlib.__version__)"`
- [ ] **0.14** Verify jupyter installed: `jupyter --version`

### Read Documentation
- [ ] **0.15** Read `migration_to_daily_volatility/00_README.md` completely
- [ ] **0.16** Read `migration_to_daily_volatility/01_MASTER_IMPLEMENTATION_PLAN.md` completely
- [ ] **0.17** Print `IMPLEMENTATION_CHECKLIST.md` for reference

---

## PHASE 1: DATA PREPARATION (22 tasks, 2 hours)

### Review Daily Return Data
- [ ] **1.1** Open `data/clean/raw_daily_total_return_2015_2023.csv`
- [ ] **1.2** Verify file has 547,890 rows
- [ ] **1.3** Verify columns: Instrument, Total Return, Date
- [ ] **1.4** Check date range: 2008-02-28 to 2023-12-29
- [ ] **1.5** Count unique instruments: should be 244
- [ ] **1.6** Spot check data quality (random sample)
- [ ] **1.7** Check for missing values in critical columns
- [ ] **1.8** Verify date format is parseable

### Review Ticker Mapping
- [ ] **1.9** Open `data/clean/List_bank.xlsx`
- [ ] **1.10** Verify ticker column exists
- [ ] **1.11** Count unique tickers
- [ ] **1.12** Open `data/clean/ticker_mapping_exceptions.csv`
- [ ] **1.13** Review existing mappings
- [ ] **1.14** Identify any obvious missing mappings

### Review Size Classification
- [ ] **1.15** Open `data/clean/esg_0718.csv`
- [ ] **1.16** Verify columns: instrument, year, dummylarge, dummymid
- [ ] **1.17** Check size bucket distribution
- [ ] **1.18** Verify years covered: 2016-2023

### Script Preparation
- [ ] **1.19** Review `05_VOLATILITY_CALCULATOR_SCRIPT.py` completely
- [ ] **1.20** Understand each step in the calculator
- [ ] **1.21** Note expected outputs and their locations
- [ ] **1.22** Prepare to run script (terminal ready, paths verified)

---

## PHASE 2: CALCULATE DAILY VOLATILITY (18 tasks, 2 hours)

### Run Calculator
- [ ] **2.1** Navigate to migration folder: `cd migration_to_daily_volatility`
- [ ] **2.2** Run script: `python 05_VOLATILITY_CALCULATOR_SCRIPT.py`
- [ ] **2.3** Monitor console output for errors
- [ ] **2.4** Verify STEP 1 completes (data loading)
- [ ] **2.5** Verify STEP 2 completes (ticker standardization)
- [ ] **2.6** Verify STEP 3 completes (log returns)
- [ ] **2.7** Verify STEP 4 completes (volatility calculation)
- [ ] **2.8** Verify STEP 5 completes (peer median fallback)
- [ ] **2.9** Verify STEP 6 completes (winsorization)
- [ ] **2.10** Verify STEP 7 completes (quality checks)
- [ ] **2.11** Verify STEP 8 completes (file saving)

### Verify Outputs
- [ ] **2.12** Check file exists: `ls -lh data/clean/equity_volatility_by_year_DAILY.csv`
- [ ] **2.13** Check file size is reasonable (should be ~100-200KB)
- [ ] **2.14** Open file and inspect first 20 rows
- [ ] **2.15** Verify columns: ticker, year, sigma_E, method, days_used, flag, size_bucket
- [ ] **2.16** Check row count: should be ~1,848 (231 banks × 8 years)
- [ ] **2.17** Check diagnostic file: `ls -lh data/clean/volatility_diagnostic_DAILY.csv`
- [ ] **2.18** Review diagnostic file contents

---

## PHASE 3: VALIDATION TESTS (20 tasks, 1 hour)

### Run Tests
- [ ] **3.1** Run validation: `python 06_VALIDATION_TESTS.py`
- [ ] **3.2** Monitor TEST 1: File Existence (should pass)
- [ ] **3.3** Monitor TEST 2: Data Loading (should pass)
- [ ] **3.4** Monitor TEST 3: Coverage Requirements (should pass ≥95%)
- [ ] **3.5** Monitor TEST 4: Value Ranges (should pass)
- [ ] **3.6** Monitor TEST 5: Method Distribution (should pass ≥80%)
- [ ] **3.7** Monitor TEST 6: Timing Discipline (should pass)
- [ ] **3.8** Monitor TEST 7: Critical Bank Coverage (should pass)
- [ ] **3.9** Monitor TEST 8: Comparison with Old (informational)

### Review Test Results
- [ ] **3.10** Count total PASS: should be ≥15
- [ ] **3.11** Count total WARN: should be ≤3
- [ ] **3.12** Count total FAIL: should be 0
- [ ] **3.13** Review any warnings in detail
- [ ] **3.14** Document any unexpected results
- [ ] **3.15** Verify coverage by year (all ≥95%)
- [ ] **3.16** Verify mean volatility is reasonable (0.20-0.50)
- [ ] **3.17** Verify primary method usage ≥80%
- [ ] **3.18** Verify critical banks all present (JPM, BAC, WFC, etc.)

### Decision Point
- [ ] **3.19** STOP if >5 test failures - investigate before proceeding
- [ ] **3.20** PROCEED if ≤3 warnings and 0 critical failures

---

## PHASE 4: UPDATE ACCOUNTING NOTEBOOK (30 tasks, 3 hours)

### Preparation
- [ ] **4.1** Open `migration_to_daily_volatility/02_NOTEBOOK_ACCOUNTING_CHANGES.md`
- [ ] **4.2** Read guide completely
- [ ] **4.3** Open `dd_pd_accounting.ipynb` in Jupyter
- [ ] **4.4** Locate Section 5 (search for "## 5. Equity volatility")
- [ ] **4.5** Note current code loads from equity_volatility_by_year.csv (line ~375)

### Update Section 5 Markdown Header
- [ ] **4.6** Find markdown cell with "## 5. Equity volatility proxy with rolling window..."
- [ ] **4.7** Replace title: "## 5. Load Equity Volatility (Daily Returns, 252-Day Window)"
- [ ] **4.8** Replace description with Bharath & Shumway (2008) methodology
- [ ] **4.9** Add note about 252-day window from year t-1

### Update Code Cell - Load Volatility
- [ ] **4.10** Find line: `vol_fp = base_dir / 'data' / 'clean' / 'equity_volatility_by_year.csv'`
- [ ] **4.11** Change to: `equity_volatility_by_year_DAILY.csv`
- [ ] **4.12** Update print statement to say "Loading sigma_E from equity_volatility_by_year_DAILY.csv..."
- [ ] **4.13** Keep equity_vol variable load line
- [ ] **4.14** Update column mapping - should use: ticker, year, sigma_E, method, days_used, flag

### Update Merge Logic
- [ ] **4.15** Find merge lines (around line 385-390)
- [ ] **4.16** Verify merge columns include: instrument, year from main df
- [ ] **4.17** From DAILY file: ticker→instrument, sigma_E_tminus1, sigma_E_method, days_used
- [ ] **4.18** Keep sigma_E assignment: `df['sigma_E'] = df['sigma_E_tminus1']`
- [ ] **4.19** Update method value expectations: daily_252, daily_partial, imputed_peer

### Add Validation Code
- [ ] **4.20** After merge, add print for coverage: `df['sigma_E_tminus1'].notna().sum()`
- [ ] **4.21** Add method distribution print: `df['sigma_E_method'].value_counts()`
- [ ] **4.22** Add value statistics: `df['sigma_E'].describe()`
- [ ] **4.23** Add range check: values between 0.10 and 1.0

### Update Window Calculation Logic
- [ ] **4.24** Find sigmaE_window_end_year calculation (line ~395)
- [ ] **4.25** Keep as is: `df['sigmaE_window_end_year'] = df['year'] - 1`
- [ ] **4.26** Update window start calculation for daily: use days_used field
- [ ] **4.27** Window start = end (only uses year t-1)

### Update Imputation Flag Logic
- [ ] **4.28** Find imputed_sigmaE_sizebucket flag setting (line ~435)
- [ ] **4.29** Change check: `df['sigma_E_method'] == 'imputed_peer'` (was peer_median)
- [ ] **4.30** Verify flag is set correctly based on method column

### Test Section 5
- [ ] **4.31** Run Section 5 cells only
- [ ] **4.32** Verify no errors
- [ ] **4.33** Check output shows correct file loaded
- [ ] **4.34** Check method distribution shows daily_252 as majority
- [ ] **4.35** Verify coverage ≥90%

---

## PHASE 5: UPDATE MARKET NOTEBOOK (20 tasks, 1.5 hours)

### Preparation
- [ ] **5.1** Open `migration_to_daily_volatility/03_NOTEBOOK_MARKET_CHANGES.md`
- [ ] **5.2** Read guide completely
- [ ] **5.3** Open `dd_pd_market.ipynb` in Jupyter
- [ ] **5.4** Locate Section 5 (search for "## 5. Merge Equity Volatility")
- [ ] **5.5** Note file path at line ~157: `vol_fp = ...equity_volatility_by_year.csv`

### Update File Path
- [ ] **5.6** Find line 157: vol_fp definition
- [ ] **5.7** Change filename to: `equity_volatility_by_year_DAILY.csv`

### Update Section 5 Markdown
- [ ] **5.8** Find markdown "## 5. Merge Equity Volatility"
- [ ] **5.9** Update description to mention daily returns, 252-day window
- [ ] **5.10** Add Bharath & Shumway (2008) citation
- [ ] **5.11** Update bullet points if they mention method details

### Update Load Code
- [ ] **5.12** Find line ~592: equity_vol load
- [ ] **5.13** Update print: "Loading equity volatility (daily-based, 252-day)..."
- [ ] **5.14** Verify columns from DAILY file: ticker_base, year, sigma_E, method, days_used
- [ ] **5.15** Keep ticker_prefix assignment: `equity_vol['ticker_prefix'] = equity_vol['ticker_base']`
- [ ] **5.16** Keep equity_volatility assignment: `equity_vol['equity_volatility'] = equity_vol['sigma_E']`

### Update Merge Code
- [ ] **5.17** Find merge at line ~600
- [ ] **5.18** Verify merge on ['ticker_prefix', 'year']
- [ ] **5.19** Keep equity_vol assignment: `df['equity_vol'] = df['equity_volatility']`
- [ ] **5.20** Verify sigma_E_tminus1 assignment at line ~662

### Add Provenance Merge
- [ ] **5.21** Find provenance merge section (line ~636)
- [ ] **5.22** Update columns to include from DAILY: sigma_E_method, days_used (not window_months)
- [ ] **5.23** Adjust window calculation if needed for daily (or comment out if not applicable)

### Add Validation
- [ ] **5.24** After merge, add coverage print
- [ ] **5.25** Add method distribution print
- [ ] **5.26** Add value range check (10%-100%)
- [ ] **5.27** Add mean/median statistics

### Test Section 5
- [ ] **5.28** Run Section 5 cells
- [ ] **5.29** Verify loads correctly
- [ ] **5.30** Check merge completes without reducing rows unexpectedly
- [ ] **5.31** Verify equity_vol populated
- [ ] **5.32** Check method shows daily_252 as primary

---

**→ Continue to COMPLETE_TASK_LIST_PART2.md for remaining phases**
