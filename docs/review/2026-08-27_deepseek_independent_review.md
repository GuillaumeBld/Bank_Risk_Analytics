# Review: DD/PD pipeline (Merton + Bharath-Shumway)

I reconstructed every module and test in this diff from the diff text and ran them (pandas 2.3.3, scipy 1.13.1). The diff's own unit tests pass on the reconstruction, so the findings below are against the code as written. Findings are ranked by severity. Everything in 1–3 was demonstrated by running the code, not inferred.

---

**1. The acceptance gate passes a dataset whose barrier is wrong for any minority of rows — including the entire 2023 cross-section. [ddpd/bands.py + ddpd/validate.py — HIGH — verified by running]**

The five economic checks are all medians or share-thresholds, so they are robust exactly where the defect is harmful. I generated a 400-row panel (50 banks × 2016–2023) with real solver outputs, then set the barrier to `debt_total`-like (6% of assets, i.e. the v3.0 defect, a 15× understatement) **only for 2023 rows** and correct total-liabilities (89% of assets) elsewhere. The 2023 rows come out with V/F ≈ 3.1, σ_V ≈ 0.19, PD ≈ 6e-13 — the exact legacy signature — and the validator returns **PASS (exit 0), every band green**. It still passes with 3 of 8 years (37.5% of rows) defective: median V/F = 1.147, in band [1.02, 1.30]. A moderate uniform defect (F = 80% of assets instead of 89%) also passes. The concrete wrong input is precisely "the v3.0 defect confined to one year or one bank cohort" — 2023 being the SVB failure year makes that the worst place to hide it. The residual checks cannot help: for any given F the solver reproduces E and σ_E to ~1e-13, so the residual bands are green for *every* input, correct or not — they measure solver health, not input correctness (max residual in every experiment: 2e-13, tolerance 1e-6).

The reason the gate has this blind spot: four of the five checks (V/F, E/F, F/assets, σ_V) are the same degree of freedom — each is the leverage ratio transformed — so the gate is effectively one test of "is the whole dataset grossly over-levered?", which the medians dilute the moment any substantial share of rows is correct. There is no per-row or per-year check anywhere (no band on the *distribution*, no check on a year's median vs the panel's).

Confidence: high — the attacking dataset was constructed and the verdict observed.

---

**2. Missing rows are invisible: coverage is optional and caller-supplied, and one input-side band is silently skippable. [ddpd/validate.py — HIGH]**

`if n_expected:` — with no `--expected-rows`, the coverage check never runs at all; with it, the producer of the CSV supplies the number, so a self-serving count passes. I verified: a panel with the entire 2023 year silently absent returns PASS both without `--expected-rows` and with `--expected-rows = len(file)`. Closely related, the only band that looks at the input rather than the output — `median F/assets` — is skipped entirely when `assets_usd` is absent from the file, so a producer can simply omit that column and drop the input-side check. And a schema inconsistency: `sigma_E` is indexed by the "sigma_V below sigma_E" check but is *not* in the `required` column set; a dataset without it crashes `validate()` with an unhandled `KeyError` (traceback, not a clean BLOCKED/FAIL report) — I reproduced this.

Confidence: high (verified). Severity is high because it compounds finding 1: drop the bad rows, omit the column, or skip the flag, and a defective dataset ships with a printed "PASS: every band holds."

---

**3. The naive drift is the one input nothing verifies: a units error in the monthly file silently halves DD_a, and the only check is an un-thresholded log line. [ddpd/pipeline.py, ddpd/returns.py — HIGH]**

`mu_hat` is asserted in a docstring to be "a percentage per month" but nothing validates it. `agreement_with_market_cap` computes the correlation between the compounded return and the market-cap change and writes it to the log — it is never thresholded, and `validate` has no drift check at all. If the monthly file's `Total Return` column were decimal (0.01) rather than percent (1.0), `mu_hat` silently becomes ≈ 0 for every bank. Concrete numbers: with E=100, σ_E=0.40, F=900, the correct drift μ=0.08 gives DD_a = 0.972 (PD_a = 16.6%); the silently-zeroed drift gives DD_a = 0.515 (PD_a = 30.3%). DD_a correlates 0.96 with its drift, so this is a large, plausible-looking error, and the gate passes (PD_a non-degenerate and everything else stays green). This is the same failure class as the v3.0 `rit` defect the pipeline is explicitly trying to kill — the fix moved the source but kept the *verification* a log line. Note also the fallback path: any bank-year absent from the monthly file falls back to the `rit` column the module itself documents as corrupt (corr 0.46 with reality), so the panel silently mixes two drift measures with different error properties into one DD_a series.

Confidence: high for the mechanism (verified); medium for real-world likelihood (depends on whether the vendor file format can change — but a gate that relies on a docstring's promise is exactly what shipped the -424% `rit`).

---

**4. The `rit` fallback mislabels the lag when a bank-year is missing. [ddpd/pipeline.py — MEDIUM]**

`fallback_rit = panel.groupby("ticker")["rit"].shift(1)` is a row-shift, not a year-shift, but the value is recorded under `mu_source_year = year - 1`. If a bank's panel has a gap (e.g. rows for 2017, 2018, 2020 and no monthly coverage in 2019), the 2020 drift is the *2018* return presented as the 2019 return. Verified on a toy frame: the 2020 row receives `rit` from 2018. Wrong lag → wrong DD_a for that bank-year, no warning. (The primary monthly path is year-exact — merge on `mu_source_year` — so only the fallback is affected.)

Confidence: high on the mechanism; medium on how often gaps occur in the real panel (IPOs, delistings, missing accounting years are known present in this data — e.g. many banks start mid-panel).

---

**5. The liabilities "plausibility" filter drops exactly the distressed observations DD/PD exists to price, silently. [ddpd/liabilities.py — MEDIUM]**

`PLAUSIBLE_LIAB_RATIO = (0.60, 0.98)` is applied to *every* liability source, including the vendor-reported line, and removes bank-years whose liabilities exceed 98% of assets (equity < 2%) — i.e. near-failure banks. Verified: a bank with equity 0.4% of assets is silently absent from the resolved panel (`n_resolved` drops to 1 of 2; the only trace is a coverage percentage in the log, no row-level record of *which* rows were rejected or *why*). The rows with the highest default probability — the ones that move a PD regression — are the ones removed. If the intention is to exclude them, it should be logged per-row and visible in the datasheet; as written, "plausible-looking wrong number without raising" applies: the panel looks fine, and the tail is gone.

Confidence: high (verified). Counter-argument acknowledged: keeping insolvent rows would require downstream handling; but silent exclusion is not that handling.

---

**6. The Merton solver can report success at a bound with huge residuals, and the pipeline accepts it without checking residuals. [ddpd/models.py, ddpd/pipeline.py — MEDIUM/LOW]**

For E/F ≲ 0.001 (a genuinely near-default bank), the lower bound V ≥ 1.001·F binds; `least_squares` returns `success=True` with the price residual ≈ 25× equity (verified: `solve_merton(0.8e6, 0.35, 1e9, 0.02)` → V/F pinned at 1.001, resid_price = 25). The pipeline checks only `fit.success`, records `solver_status="converged"`, and never looks at the residuals it stores. Two consequences: (a) the "merton converged on N/M rows" log line can be true while N includes garbage rows; (b) if such a row reaches the file, the gate *fails the whole dataset* on the residual band — so the corrected run and the gate have a latent conflict over the very distressed banks finding 5 removes. In the current 244-bank data E/F stays above ~0.02 so this is latent, not live.

Confidence: high (verified numerically).

---

**7. Vendor identity: the "company-name token check" does not exist in this surface, and the 2% asset-agreement check cannot detect a mapping error shared by both sources. [ddpd/liabilities.py — LOW/MEDIUM]**

The only vendor-identity check is the 2% comparison of `total_assets_ref` against `assets_usd`. It catches one-sided mismatches (vendor's ticker→RIC resolves to a different company than the panel's ticker) — good, and tested. But both figures are keyed by the same normalized ticker string; if the *accounting file's* ticker→company mapping is itself wrong (the source of `assets_usd`), and the vendor pull shares that mapping, both numbers belong to the wrong company and agree. No name-token check exists anywhere in the diff (I searched; it may live in scripts outside this surface). The docstring's own claim — "which no plausibility band can detect" — is correct, and the 2% check is the right idea; its blind spot is shared corruption, which a name-token check would close.

Confidence: high that the token check is absent from the reviewed surface; the blind spot is structural.

---

**8. `_dedupe` crashes with `IndexError` on a duplicated key whose rule column is all-NaN. [ddpd/pipeline.py — LOW]**

A duplicated `(ticker, year)` in the accounting file with `total_assets` missing for every row makes `values = []` and `values[0]` raises (verified). Loud, not silent, but a one-row data hiccup kills the whole build with a traceback instead of a logged skip. Also minor: the market-cap merge uses a *silent* `drop_duplicates` (first row wins) where the accounting/volatility dedupes were given logged rules — inconsistent handling of the same class of problem.

Confidence: high (verified).

---

**9. Judgement calls (D).**

- **Implausible drift → NaN rather than clip: mostly defensible; two narrow objections.** The -100% floor is right (a return below -1 is impossible, monthly compounding can't reach it). But (a) the upper cap of 3.0 discards *real* observations — banks can return >300% in a year — so the rule removes genuine high-drift rows asymmetrically; and (b) because the monthly path can't produce a return below -1, the floor effectively bites only the fallback `rit` rows, i.e. the penalty lands on the rows already using the documented-unreliable source, while a corrupt-but-plausible `rit` value (-0.95) is used without question. Clipping would indeed invent a number; NaN is the honest choice — but the honest choice for a *broken* input is not the same as for a *real* extreme, and the band conflates the two.
- **First-year rows dropped, no imputation: fine, but the comment is wrong.** No imputation is defensible (peer-group means bias DD_a toward the mean). However, the code comment "That costs each bank its first panel year (244 rows)" contradicts returns.py's claim that the monthly file starts in 2013 and therefore supplies a 2015 lag for 2016 — if the latter is true, banks listed by 2015 lose nothing. The real loss is banks absent from the prior-year monthly data (or with <12 months), and the comment overstates it. The DD_a panel is unbalanced; document the actual loss, not a blanket 244.
- **d1/d2 clipped to ±35: no objection.** Φ saturates to machine precision well before ±35; the clip only creates a mass point at DD=±35 for pathological rows and flattens the solver's objective in already-saturated regions. Harmless.

---

**A. Finance formulas: no finding.** I hand-checked and numerically round-tripped the code: `E = V·Φ(d1) − F·e^{−rT}·Φ(d2)` and `σ_E = (V/E)·Φ(d1)·σ_V` are correct; `DD_m` is d2 with the `(rf − 0.5σ_V²)` drift, not d1 (the solver returns exactly d2 in the round-trip test); `PD_m = Φ(−DD_m)`; the naive model is Bharath-Shumway verbatim (`V̂ = E+F`, `σ_D = 0.05 + 0.25σ_E`, value-weighted `σ_V`, `μ = r_{i,t−1}`), and `DD_a` uses the physical drift with the correct `(μ − 0.5σ_V²)` term. No sign errors, no wrong drift, no measure misuse; the risk-neutral vs physical PD distinction is labeled in the output (`measure_m`/`measure_a`). The only blemish is finding 6, which is a solver-robustness issue, not a formula error.

**B. Verdict on the gate.** (i) A wrong dataset *can* pass all five bands — constructively demonstrated (findings 1–2). (ii) The bands are economically *justified* (leverage ratios, 1–5% asset vol), not crudely reverse-engineered — but they are anchored to the corrected output's medians with ~2–3× margins and, since four of them are one leverage degree of freedom, they only discriminate gross whole-dataset defects. (iii) The "gate must fail on legacy" test is real and non-vacuous: the legacy fixture fails five bands, the assertions check non-trivial properties (median V/F > 3.0, asset-vol median > 0.10), and a band widening would break it. Its weakness is narrower: it pins only the *whole-dataset* defect, which is exactly the case the gate already handles — it gives no assurance against the minority-defect cases of finding 1.

---

*Method note: everything in findings 1–6 and 8 was verified by running reconstructed code; 7 and 9 are code-reading with spot verification. I did not have access to the real data files (Book2_clean, monthly returns, etc.), so claims about the actual panel — whether year gaps occur, whether the monthly file's format can drift — are flagged medium confidence where they depend on data.*
EXIT=0
