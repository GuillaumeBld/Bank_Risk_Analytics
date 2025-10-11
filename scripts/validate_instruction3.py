#!/usr/bin/env python3
# scripts/validate_instruction3.py
import sys, argparse, pandas as pd, numpy as np
from pathlib import Path

def pct(x): return f"{100*x:.1f}%"

def load_csv(p): 
    p = Path(p)
    if not p.exists(): sys.exit(f"Missing file: {p}")
    return pd.read_csv(p)

def dist(df, col):
    s = df[col].dropna().astype(float)
    return {
        "n": len(s),
        "mean": s.mean(),
        "p50": s.quantile(0.50),
        "p90": s.quantile(0.90),
        "p99": s.quantile(0.99),
        "max": s.max()
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--equity_vol", required=True, help="data/clean/equity_volatility_by_year.csv")
    ap.add_argument("--dd_market_new", required=True, help="output from dd_pd_market.ipynb")
    ap.add_argument("--dd_accounting_new", required=True, help="output from dd_pd_accounting.ipynb")
    ap.add_argument("--dd_market_old", default=None, help="optional baseline market DD")
    ap.add_argument("--dd_accounting_old", default=None, help="optional baseline accounting DD")
    ap.add_argument("--tier_diag", required=True, help="data/clean/total_return_diagnostic.csv")
    ap.add_argument("--status_col_market", default="status_m", help="status code column for market")
    ap.add_argument("--status_col_accounting", default="status_a", help="status code column for accounting")
    ap.add_argument("--id_col", default="ticker_base")
    ap.add_argument("--year_col", default="year")
    ap.add_argument("--ddm_col", default="DD_m")
    ap.add_argument("--dda_col", default="DD_a")
    args = ap.parse_args()

    # A) Convergence rate by year and size bucket
    ddm = load_csv(args.dd_market_new)
    if "size_bucket" not in ddm.columns:
        ddm["size_bucket"] = np.where(ddm.get("dummylarge", 0)==1, "large", "small_mid")
    conv = ddm.groupby([args.year_col, "size_bucket"])[args.ddm_col].apply(lambda s: s.notna().mean()).rename("conv_rate").reset_index()
    print("\n[A] DD_m convergence by year and size")
    print(conv.to_string(index=False))

    # B) Distribution deltas new vs old for DD_m and DD_a by year
    def yearly_stats(df, col, label):
        g = df.groupby(args.year_col).apply(lambda x: pd.Series(dist(x, col))).reset_index()
        g.insert(1, "metric", label)
        return g

    stats = []
    stats.append(yearly_stats(ddm, args.ddm_col, "DD_m new"))
    dda = load_csv(args.dd_accounting_new)
    stats.append(yearly_stats(dda, args.dda_col, "DD_a new"))

    if args.dd_market_old:
        ddm_old = load_csv(args.dd_market_old)
        stats.append(yearly_stats(ddm_old, args.ddm_col, "DD_m old"))
    if args.dd_accounting_old:
        dda_old = load_csv(args.dd_accounting_old)
        stats.append(yearly_stats(dda_old, args.dda_col, "DD_a old"))

    print("\n[B] Distribution summary by year")
    print(pd.concat(stats, ignore_index=True).round(3).to_string(index=False))

    # C) 2018 validation table for 20 banks, old vs new sigma_E and DD
    vol = load_csv(args.equity_vol)
    vol18 = vol[vol[args.year_col]==2018][[args.id_col, "sigma_E"]].rename(columns={"sigma_E":"sigma_E_new"})
    # try to load old volatility if present, else leave blank
    try:
        vol_old = load_csv(Path(args.equity_vol).with_name("equity_volatility_by_year_old.csv"))
        vol_old18 = vol_old[vol_old[args.year_col]==2018][[args.id_col, "sigma_E"]].rename(columns={"sigma_E":"sigma_E_old"})
    except Exception:
        vol_old18 = pd.DataFrame(columns=[args.id_col, "sigma_E_old"])

    ddm18 = ddm[ddm[args.year_col]==2018][[args.id_col, args.ddm_col]].rename(columns={args.ddm_col:"DD_m_new"})
    try:
        ddm_old18 = ddm_old[ddm_old[args.year_col]==2018][[args.id_col, args.ddm_col]].rename(columns={args.ddm_col:"DD_m_old"})
    except Exception:
        ddm_old18 = pd.DataFrame(columns=[args.id_col, "DD_m_old"])

    sample = (vol18.merge(vol_old18, on=args.id_col, how="left")
                    .merge(ddm18, on=args.id_col, how="left")
                    .merge(ddm_old18, on=args.id_col, how="left"))
    sample["sigma_E_delta"] = sample["sigma_E_new"] - sample.get("sigma_E_old")
    sample["DD_m_delta"] = sample["DD_m_new"] - sample.get("DD_m_old")
    print("\n[C] 2018 spot check, 20 banks old vs new (sigma_E and DD_m)")
    print(sample.head(20).round(4).to_string(index=False))

    # D) No bespoke 2018 flags remain
    bad_flags = []
    if args.status_col_market in ddm.columns:
        bad_flags += [x for x in ddm[args.status_col_market].dropna().unique() if "2018" in str(x)]
    if args.status_col_accounting in dda.columns:
        bad_flags += [x for x in dda[args.status_col_accounting].dropna().unique() if "2018" in str(x)]
    print("\n[D] Status code scan")
    if bad_flags:
        print("Found year specific flags:", sorted(set(bad_flags)))
    else:
        print("OK, only standard status codes present")

    # E) Tier counts unchanged from Instruction 2 inputs
    tier = load_csv(args.tier_diag)
    tier_counts = tier["tier"].value_counts()
    print("\n[E] Tier counts from diagnostic")
    for k in ["Tier 1", "Tier 2", "Tier 3"]:
        print(f"{k}: {tier_counts.get(k,0)}")
    print("Check that downstream DD tables preserve row counts aside from QC exclusions in audit.")

if __name__ == "__main__":
    main()
