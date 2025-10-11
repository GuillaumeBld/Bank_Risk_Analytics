# Integration Q&A - Quick Reference

**All 8 questions answered. Ready for implementation.**

---

## Q1: Identifier Alignment ✅

**a) One-to-one correspondence?**
- **NO on full instrument**, YES on ticker_base
- List_bank uses: `BAC`, return data uses: `BAC.N`
- 232/244 match automatically (95%)

**b) Join on instrument or ticker_base?**
- **Join on ticker_base** (cleaned)
- Strip suffixes from return data: `.N`, `.O`, `.OQ`, `^codes`
- Use manual mapping file for 12 exceptions

**c) Propagate both or only ticker_base?**
- **Propagate BOTH** in all outputs:
  - `instrument`: Full ticker with suffix (audit trail)
  - `ticker_base`: Clean ticker (for joins)
  - `company`: From List_bank
  - `perm_id`: Refinitiv ID

---

## Q2: Coverage Validation ✅

**return_coverage_detailed.csv is authoritative** ✓

**For 0-month years:**
- **Drop from all downstream aggregates**
- Keep in audit file with `exclusion_reason = "no_data"`

---

## Q3: Time Span ✅

**Exclude 2024:** YES ✓
- Filter: `year <= 2023` for both monthly and annual

**Month-end dated:** YES, 100% confirmed ✓
- No duplicates found
- Some gaps within years (acceptable if ≥ 9 months)

---

## Q4: Return Handling ✅

**All returns in percentage form:** YES ✓
- 6.16 = +6.16% (not 0.0616)

**Convert to decimals for modeling:** YES ✓
- Store as percentages in outputs (human-readable)
- Convert in modeling script: `r = return_pct / 100`

---

## Q5: Tier Rules ✅

**Enforce ≥ 9 months as Tier 1:** YES ✓

**Final tiers:**
- **Tier 1**: ≥ 9 months → 2,354 bank-years (88.4%)
- **Tier 2**: < 9 months + annual backup → 9 bank-years (0.3%)
- **Tier 3**: < 9 months + no backup → 301 bank-years (11.3%) **EXCLUDE**

**PCB 100%+ returns:** KEEP, flag as outlier ✓

**Config file:** YES, create config.json ✓
```json
{
  "tier_1_min_months": 9,
  "monthly_return_caps": [-50, 100],
  "annual_return_caps": [-80, 200],
  "exclude_2024": true
}
```

---

## Q6: Output Schemas ✅

**Three files with BOTH instrument and ticker_base:**

### 1. monthly_returns_clean.csv (Tier 1 only)
```
instrument, ticker_base, company, perm_id, year, month, date,
total_return_pct, total_return_decimal, data_tier, return_flag
```
**Rows**: ~28,000

### 2. annual_returns_all.csv (All tiers marked)
```
instrument, ticker_base, company, perm_id, year, total_return_pct,
data_tier, monthly_coverage_count, has_annual_backup, 
used_as_backup, return_flag, exclusion_reason
```
**Rows**: ~2,600

### 3. return_data_audit.csv (Full audit)
```
instrument, ticker_base, company, year, data_tier, valid_months,
has_annual_backup, annual_return_pct, exclusion_reason, action_taken
```
**Rows**: ~2,664

---

## Q7: Validation Thresholds ✅

**Caps:** Flag, don't drop ✓
- Monthly: [-50%, +100%]
- Annual: [-80%, +200%]

**Flag column name:** `return_flag` ✓
- Values: `"normal"`, `"outlier_high"`, `"outlier_low"`, `"missing"`

**Outliers detected:**
- 21 monthly (0.07%)
- 8 annual (0.31%)

---

## Q8: Integration Readiness ✅

**Workflow:** Load List_bank.xlsx FIRST, merge during tiering ✓

**Steps:**
1. Load List_bank.xlsx → prepare ticker_base
2. Clean return data identifiers (strip suffixes)
3. **Merge BEFORE tiering** (left join on ticker_base)
4. Apply manual mapping for 12 exceptions (see `ticker_mapping_exceptions.csv`)
5. Apply tier rules
6. Generate 3 output files

**Manual mapping required:** 12 instruments ✓
- File created: `data/clean/ticker_mapping_exceptions.csv`
- Most are suffix issues, 1 is ticker change (MCHB→HMST)

---

## 🔴 Critical Findings

### Manual Mapping (12 cases)
File: `ticker_mapping_exceptions.csv`

**Key case:** MCHB (new) → HMST (old) post-merger

### Match Rate
- **Automatic**: 232/244 (95%)
- **With manual mapping**: 244/244 (100%)

### Data Loss
- **11.3%** excluded (Tier 3: insufficient data)
- **Acceptable** given quality standards

---

## 📋 Implementation Checklist

- [ ] Load List_bank.xlsx
- [ ] Apply ticker_mapping_exceptions.csv
- [ ] Merge to return data
- [ ] Filter year <= 2023
- [ ] Apply tier rules (9-month threshold)
- [ ] Flag outliers
- [ ] Generate 3 output files
- [ ] Create config.json
- [ ] Validate row counts

---

## Expected Outcomes

**Coverage:**
- Tier 1: 2,354 bank-years (use directly)
- Tier 2: 9 bank-years (use annual)
- Tier 3: 301 bank-years (exclude)

**Join success:** 100% after manual mapping

**Data quality:** High (88.4% Tier 1 data)

---

## 🎯 Ready for Agent Coder

All questions answered. Proceed with integration.

**Full details:** See `INTEGRATION_QA_FINAL.md`

---

*Generated: 2025-10-11*
