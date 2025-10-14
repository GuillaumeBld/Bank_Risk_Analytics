# COMPLETE TASK LIST - Daily Volatility Migration (Part 2 of 2)
## Documentation, Testing, and Finalization

**Total Tasks Part 2**: 87 tasks  
**Estimated Time**: 6-7 hours

---

## PHASE 6: DOCUMENTATION UPDATES (43 tasks, 2.5 hours)

### Update dd_and_pd.md - Data Sources Section

- [ ] **6.1** Open `docs/writing/dd_and_pd.md`
- [ ] **6.2** Find Table at line 100-106 "Data Sources"
- [ ] **6.3** Locate row: "**Total Returns** | CRSP | 2013-2023 | Monthly total returns including dividends (3-year lookback)"
- [ ] **6.4** Change "Monthly total returns" to "Daily total returns"
- [ ] **6.5** Change "(3-year lookback)" to "(252-day window)"
- [ ] **6.6** Change period if needed: "2015-2023" (need prior year for 2016)

### Update Equity Volatility Section - Primary Method

- [ ] **6.7** Find Section "#### Primary Method: 36-Month Rolling Standard Deviation" (line ~115)
- [ ] **6.8** Change header to: "#### Primary Method: 252-Day Daily Standard Deviation (Bharath & Shumway 2008)"
- [ ] **6.9** Find Formula block starting "σ_{E,t-1} = √12 × std(r_{t-36:t-1})"
- [ ] **6.10** Replace with: "σ_{E,t-1} = √252 × std(daily log returns in year t-1)"
- [ ] **6.11** Update "Where:" section
- [ ] **6.12** Change: "r_t = ln(P_t / P_{t-1}): Monthly log returns" to "Daily log returns"
- [ ] **6.13** Change: "√12: Annualization factor" to "√252: Annualization factor"
- [ ] **6.14** Change: "Window: 36 months ending at t-1" to "Window: 252 trading days (all of year t-1)"
- [ ] **6.15** Change: "Requirements: Minimum 9 valid monthly returns" to "Minimum 180 trading days (70% of year)"
- [ ] **6.16** Change: "Coverage: Approximately 98%" to "Approximately 90%"

### Update Fallback Methods

- [ ] **6.17** Find "#### Fallback 1: EWMA" section (line ~133)
- [ ] **6.18** Change header to: "#### Fallback 1: Partial Year Data"
- [ ] **6.19** Remove EWMA formula completely
- [ ] **6.20** Replace with: "Used when 90-179 trading days available in year t-1"
- [ ] **6.21** Add: "**Method**: Use available daily data with √252 annualization, flagged as 'insufficient_days'"
- [ ] **6.22** Change coverage: "Approximately 7-8% of observations"

- [ ] **6.23** Find "#### Fallback 2: Peer Median" (line ~150)
- [ ] **6.24** Update criteria: "Used when <90 trading days available"
- [ ] **6.25** Keep rest of section mostly the same
- [ ] **6.26** Update coverage: "Approximately 2-3% of observations"

### Update Provenance Tracking Section

- [ ] **6.27** Find Section "### Provenance Tracking" (line ~182)
- [ ] **6.28** Find table with Field | Description | Example Values
- [ ] **6.29** Update **sigma_E_method** examples: "daily_252, daily_partial, imputed_peer"
- [ ] **6.30** Change **sigma_E_window_months** to **days_used**
- [ ] **6.31** Update description: "Actual trading days used"
- [ ] **6.32** Update example values: "180, 220, 252"
- [ ] **6.33** Remove sigmaE_window_start_year row (not applicable for daily)
- [ ] **6.34** Keep sigmaE_window_end_year: "Always t-1 (no lookahead)"

- [ ] **6.35** Find Example at line ~194: "For 2018 DD calculation:"
- [ ] **6.36** Change: "**σ_E computed from**: Jan 2015 - Dec 2017 (36 months)"
- [ ] **6.37** To: "**σ_E computed from**: Jan 2017 - Dec 2017 (252 trading days)"
- [ ] **6.38** Change: "**Window end**: 2017 (t-1)" (keep as is)
- [ ] **6.39** Update note: "Uses only 2017 daily data" instead of "pre-2018 data"

### Add New Comparison Section

- [ ] **6.40** After line 199, add new section header: "### Volatility Method Comparison: Previous vs Current"
- [ ] **6.41** Add comparison table with columns: Aspect | Previous (Annual) | Current (Daily)
- [ ] **6.42** Row 1: Data Frequency | Annual returns | Daily returns
- [ ] **6.43** Row 2: Time Window | 3 years (t-1, t-2, t-3) | 1 year (year t-1 only)
- [ ] **6.44** Row 3: Observations | 3 annual observations | ~252 daily observations
- [ ] **6.45** Row 4: Annualization | None (already annual) | ×√252
- [ ] **6.46** Row 5: Literature Support | Ad-hoc | Bharath & Shumway (2008)
- [ ] **6.47** Row 6: Market Sensitivity | Lower (3-year average) | Higher (recent dynamics)
- [ ] **6.48** Add explanation paragraph: "The daily method is now standard in default prediction literature..."

### Update References Section

- [ ] **6.49** Scroll to end of document (line ~969)
- [ ] **6.50** Find "**Key References:**" section
- [ ] **6.51** Add full Bharath & Shumway citation after Merton (1974)
- [ ] **6.52** Format: "Bharath, S. T., & Shumway, T. (2008). 'Forecasting Default with the Merton Distance to Default Model.' The Review of Financial Studies, 21(3), 1339-1369."
- [ ] **6.53** Add DOI link: "https://doi.org/10.1093/rfs/hhn044"
- [ ] **6.54** Add note: "Standard methodology for equity volatility in DD calculations"

### Update EQUITY_VOLATILITY_EXPLANATION.md

- [ ] **6.55** Open `docs/guides/EQUITY_VOLATILITY_EXPLANATION.md`
- [ ] **6.56** Find line 13: "σ_{E,t-1} = 3-year rolling standard deviation"
- [ ] **6.57** Replace with: "σ_{E,t-1} = Standard deviation of daily returns (252-day window)"
- [ ] **6.58** Find "Key characteristics:" section (lines 15-20)
- [ ] **6.59** Update **Window**: "252 trading days (all of year t-1)"
- [ ] **6.60** Update **Input**: "Daily total returns (including dividends)"
- [ ] **6.61** Update **Min periods**: "180 trading days minimum (70% of year)"
- [ ] **6.62** Update **Source**: "Daily stock return data"
- [ ] **6.63** Add line: "**Annualization**: Daily SD × √252"

- [ ] **6.64** Find formula section (line ~93)
- [ ] **6.65** Update formula to show daily calculation with √252
- [ ] **6.66** Update all "3 years" to "252 days"
- [ ] **6.67** Update all "annual" to "daily" where appropriate

### Update README.md

- [ ] **6.68** Open `README.md` in root directory
- [ ] **6.69** Search for any methodology or volatility mentions
- [ ] **6.70** If methodology section exists, update it
- [ ] **6.71** If not, add new section: "## Methodology"
- [ ] **6.72** Add subsection: "### Equity Volatility Calculation"
- [ ] **6.73** Write: "We follow Bharath & Shumway (2008) for equity volatility:"
- [ ] **6.74** List: Data source (daily returns), Window (252 days), Formula (SD × √252)
- [ ] **6.75** Mention fallback procedures
- [ ] **6.76** Add: "This represents the academic standard in default prediction literature"

### Update Reference Documents

- [ ] **6.77** Open `docs/reference/Market_approach`
- [ ] **6.78** Find line 12: "equity_vol → σ_E annualized, decimal"
- [ ] **6.79** Add to description: "(from daily returns, 252-day window)"

- [ ] **6.80** Check if `docs/reference/Accounting_approach` exists
- [ ] **6.81** If yes, update any sigma_E references similarly

### Global Search & Replace

- [ ] **6.82** Search all .md files in docs/ for "3-year rolling"
- [ ] **6.83** Replace occurrences with "252-day daily" (verify context first)
- [ ] **6.84** Search for "36 months" or "36-month"
- [ ] **6.85** Replace with "252 days" or "252-day" (verify context)
- [ ] **6.86** Search for "monthly returns" in volatility calculation context
- [ ] **6.87** Replace with "daily returns" (but not in other contexts)
- [ ] **6.88** Search for "√12" or "sqrt(12)"
- [ ] **6.89** Replace with "√252" or "sqrt(252)"

---

## PHASE 7: COMPARISON ANALYSIS (15 tasks, 1 hour)

### Run Analysis Script

- [ ] **7.1** Navigate to migration folder
- [ ] **7.2** Run: `python 07_COMPARISON_ANALYSIS.py`
- [ ] **7.3** Monitor console output: "[1] Loading data..."
- [ ] **7.4** Verify daily volatility loads successfully
- [ ] **7.5** Verify old volatility loads (if exists)
- [ ] **7.6** Monitor "[2] Comparing volatility methods..."
- [ ] **7.7** Review statistics printed to console
- [ ] **7.8** Monitor "[3] Creating visualizations..."
- [ ] **7.9** Wait for 7-plot figure generation
- [ ] **7.10** Monitor "[4] Identifying top movers..."
- [ ] **7.11** Review top increases/decreases
- [ ] **7.12** Check for completion message

### Review Outputs

- [ ] **7.13** Navigate to: `data/outputs/analysis/`
- [ ] **7.14** Open: `volatility_comparison_analysis.png`
- [ ] **7.15** Review Plot 1: Scatter (old vs new) - should show positive correlation
- [ ] **7.16** Review Plot 2: Distribution comparison - should overlap
- [ ] **7.17** Review Plot 3: Difference distribution - check if centered reasonably
- [ ] **7.18** Review Plot 4: Mean volatility by year - trends should make sense
- [ ] **7.19** Review Plot 5: % Change by year - note which years differ most
- [ ] **7.20** Review Plot 6: Direction by year - % banks with higher daily vol
- [ ] **7.21** Review Plot 7: Box plots by year - check for outliers

- [ ] **7.22** Open: `volatility_comparison_data.csv`
- [ ] **7.23** Spot check values for reasonableness
- [ ] **7.24** Sort by delta_pct to see biggest changes

- [ ] **7.25** Open: `migration_summary_report.txt`
- [ ] **7.26** Review correlation value (should be 0.6-0.9)
- [ ] **7.27** Review mean % change (should be <40%)
- [ ] **7.28** Note interpretation bullets

### Document Findings

- [ ] **7.29** Create file: `MIGRATION_FINDINGS.txt`
- [ ] **7.30** Document correlation coefficient
- [ ] **7.31** Document mean volatility change
- [ ] **7.32** Document which years changed most (likely 2018, 2020)
- [ ] **7.33** Document top 5 banks with biggest increases
- [ ] **7.34** Document any concerning patterns
- [ ] **7.35** Note if results match expectations

---

## PHASE 8: FULL SYSTEM VALIDATION (20 tasks, 2 hours)

### Clean Restart Test

- [ ] **8.1** Close all Jupyter notebooks
- [ ] **8.2** Shut down Jupyter server
- [ ] **8.3** Restart Jupyter: `jupyter notebook`
- [ ] **8.4** Clear all browser cache (optional but recommended)

### Test Accounting Notebook

- [ ] **8.5** Open dd_pd_accounting.ipynb fresh
- [ ] **8.6** Kernel → Restart & Clear Output
- [ ] **8.7** Kernel → Restart & Run All
- [ ] **8.8** Monitor Section 1-4: Should run normally
- [ ] **8.9** Monitor Section 5: NEW volatility loading code
- [ ] **8.10** Verify Section 5 prints show daily_252 method
- [ ] **8.11** Verify coverage ≥90%
- [ ] **8.12** Monitor Section 6: DD/PD calculation
- [ ] **8.13** Monitor Section 7-8: Output and diagnostics
- [ ] **8.14** Wait for completion (~10-15 minutes)
- [ ] **8.15** Verify no errors in any cell
- [ ] **8.16** Check last cell shows success message
- [ ] **8.17** Verify output file created with timestamp

### Test Market Notebook

- [ ] **8.18** Open dd_pd_market.ipynb fresh
- [ ] **8.19** Kernel → Restart & Clear Output
- [ ] **8.20** Kernel → Restart & Run All
- [ ] **8.21** Monitor Section 1-4: Should run normally
- [ ] **8.22** Monitor Section 5: NEW volatility file path
- [ ] **8.23** Verify loads from DAILY file
- [ ] **8.24** Monitor Section 6: Solver
- [ ] **8.25** Check solver convergence rate (should be >80%)
- [ ] **8.26** Monitor Section 7-8: DD/PD and output
- [ ] **8.27** Wait for completion (~15-20 minutes)
- [ ] **8.28** Verify no errors
- [ ] **8.29** Check convergence messages
- [ ] **8.30** Verify output file created

### Verify Output Files

- [ ] **8.31** List outputs: `ls -lh data/outputs/datasheet/`
- [ ] **8.32** Find newest accounting file: `accounting_[timestamp].csv`
- [ ] **8.33** Find newest market file: `market_[timestamp].csv`
- [ ] **8.34** Check file sizes are reasonable (should be similar to before)

### Sanity Check Results

- [ ] **8.35** Load accounting CSV in Python/pandas or Excel
- [ ] **8.36** Check columns include: sigma_E, sigma_E_method, DD_a, PD_a
- [ ] **8.37** Calculate: `df['DD_a'].mean()` - should be 5-15
- [ ] **8.38** Calculate: `df['PD_a'].mean()` - should be 0.0001-0.01
- [ ] **8.39** Check: `df['sigma_E_method'].value_counts()` - daily_252 should dominate
- [ ] **8.40** Load market CSV
- [ ] **8.41** Check columns include: equity_vol, DD_m, PD_m
- [ ] **8.42** Calculate: `df['DD_m'].mean()` - should be 4-12
- [ ] **8.43** Calculate: `df['PD_m'].mean()` - should be 0.0001-0.01
- [ ] **8.44** Check solver status distribution

### Coverage Verification

- [ ] **8.45** Count non-null DD_a: `df['DD_a'].notna().sum()`
- [ ] **8.46** Should be ≥90% of total rows
- [ ] **8.47** Count non-null DD_m: `df['DD_m'].notna().sum()`
- [ ] **8.48** Should be ≥80% of total rows
- [ ] **8.49** Check which bank-years are missing
- [ ] **8.50** Verify missing make sense (IPOs, insufficient data, etc.)

---

## PHASE 9: FINAL COMMIT (9 tasks, 30 minutes)

### Review All Changes

- [ ] **9.1** Run: `git status` to see all modified files
- [ ] **9.2** Run: `git diff dd_pd_accounting.ipynb | head -100` to review changes
- [ ] **9.3** Run: `git diff dd_pd_market.ipynb | head -100`
- [ ] **9.4** Run: `git diff docs/writing/dd_and_pd.md | head -100`
- [ ] **9.5** Verify changes look correct

### Stage Files

- [ ] **9.6** Stage notebooks: `git add dd_pd_accounting.ipynb dd_pd_market.ipynb`
- [ ] **9.7** Stage new volatility: `git add data/clean/equity_volatility_by_year_DAILY.csv`
- [ ] **9.8** Stage documentation: `git add docs/`
- [ ] **9.9** Stage migration folder: `git add migration_to_daily_volatility/`
- [ ] **9.10** Check status: `git status` - verify correct files staged

### Commit with Detailed Message

- [ ] **9.11** Create commit with comprehensive message (see template in Part 1, task 9.10)
- [ ] **9.12** Include: Methodology change, files updated, validation results, references
- [ ] **9.13** Commit: `git commit -F commit_message.txt` (if saved to file)
- [ ] **9.14** Or: `git commit -m "..."` with full message
- [ ] **9.15** Verify commit: `git log --oneline -1`
- [ ] **9.16** Check diff stats: `git show --stat`

### Push to Remote

- [ ] **9.17** Push branch: `git push origin feature/daily-volatility`
- [ ] **9.18** Verify push succeeded
- [ ] **9.19** Note branch URL for later merge/PR

---

## PHASE 10: POST-MIGRATION CLEANUP (9 tasks, 30 minutes)

### Check Other Notebooks

- [ ] **10.1** Open `merging.ipynb` (if it exists)
- [ ] **10.2** Check if it references equity volatility files
- [ ] **10.3** Update if needed to use DAILY file
- [ ] **10.4** Test run if changes made

- [ ] **10.5** Check `analysis.ipynb` (if it exists)
- [ ] **10.6** Update any volatility references
- [ ] **10.7** Check any visualization scripts
- [ ] **10.8** Update any hardcoded "3-year" references

### Create Summary Report

- [ ] **10.9** Create `MIGRATION_COMPLETE_SUMMARY.md` in root
- [ ] **10.10** Document what changed
- [ ] **10.11** Document validation results
- [ ] **10.12** Document key findings from comparison
- [ ] **10.13** Note any issues encountered
- [ ] **10.14** List next steps or recommendations

### Archive Old Files (Optional)

- [ ] **10.15** Create archive folder: `mkdir data/clean/ARCHIVE_OLD_VOLATILITY`
- [ ] **10.16** Move old file: `mv data/clean/equity_volatility_by_year.csv.OLD data/clean/ARCHIVE_OLD_VOLATILITY/`
- [ ] **10.17** Add README explaining what's archived

### Update Project Documentation

- [ ] **10.18** Update any project wiki or external docs
- [ ] **10.19** Update any presentations referencing methodology
- [ ] **10.20** Notify collaborators of changes

---

## ✅ FINAL CHECKLIST (20 verification items)

### Technical Verification
- [ ] **F.1** Both notebooks run without errors (end-to-end)
- [ ] **F.2** Output files generated with correct structure
- [ ] **F.3** Daily volatility file has ≥1,800 rows
- [ ] **F.4** Coverage ≥90% for accounting, ≥80% for market
- [ ] **F.5** Validation tests pass (≤3 warnings, 0 failures)
- [ ] **F.6** Comparison analysis shows reasonable correlation (≥0.6)

### Code Quality
- [ ] **F.7** No hardcoded "3-year" references in notebooks
- [ ] **F.8** All sigma_E references use new DAILY source
- [ ] **F.9** Method values updated (daily_252, not monthly36)
- [ ] **F.10** Proper error handling in place

### Documentation Quality
- [ ] **F.11** All "3-year" changed to "252-day" in docs
- [ ] **F.12** Bharath & Shumway (2008) cited properly
- [ ] **F.13** Formulas updated (√252 instead of √12)
- [ ] **F.14** Method comparison table added
- [ ] **F.15** README updated with methodology

### Results Quality
- [ ] **F.16** DD values in reasonable range (3-20)
- [ ] **F.17** PD values in reasonable range (0.0001-0.05)
- [ ] **F.18** Volatility values in reasonable range (0.10-1.0)
- [ ] **F.19** Critical banks (JPM, BAC, WFC) all have values
- [ ] **F.20** No unexpected massive spikes in defaults

### Process Quality
- [ ] **F.21** Backups exist and verified
- [ ] **F.22** Git branch created and pushed
- [ ] **F.23** Commit message is descriptive
- [ ] **F.24** Migration folder contains all guides
- [ ] **F.25** Rollback instructions available if needed

---

## 🎉 COMPLETION CERTIFICATE

Once all tasks are checked:

**Date Completed**: ___________  
**Total Time**: _____ hours  
**Tests Passed**: _____ / _____  
**Final Coverage**: _____%  
**Correlation with Old**: _____  

**Migration Status**: ✅ **COMPLETE**

**Signed**: _________________  
**Notes**: _________________

---

*End of Complete Task List - You did it! 🎊*
