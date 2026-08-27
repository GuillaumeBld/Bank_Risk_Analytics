"""Pull reported total liabilities per bank-year, keyed on RIC, name-verified.

Two identifier traps in this universe, both observed rather than assumed:

1. The PermId column of List_bank.xlsx is misaligned with its Ticker column for
   part of the file. LARK's listed PermId returns KeyCorp; KEY's returns
   JPMorgan Chase. PermId is therefore NOT usable from that file.
2. Guessing a RIC suffix resolves the wrong company silently. The Symbol column
   carries the correct RIC, including the '^' suffixes of the ten banks delisted
   in 2025-2026, which are needed rather than excluded.

So: key on Symbol, and verify every row by company name before trusting it. A
wrong entity returns a complete, internally consistent balance sheet, which no
plausibility check on the numbers alone can detect.
"""
import re
import time
import pandas as pd
import refinitiv.data as rd

YEARS = range(2016, 2024)
FIELDS = {
    "TR.F.TotAssets":   "total_assets_ref",
    "TR.F.TotLiab":     "total_liabilities",
    "TR.F.DeposTot":    "deposits",
    "TR.F.TotShHoldEq": "total_equity",
    "TR.F.DebtTot":     "debt_total_ref",
}
STOPWORDS = {"inc", "corp", "corporation", "company", "co", "the", "group",
             "incorporated", "bancorp", "bancorporation", "bancshares",
             "financial", "holdings", "holding", "services", "ltd", "na"}


def tokens(name: str) -> set[str]:
    words = re.findall(r"[a-z]+", str(name).lower())
    return {w for w in words if w not in STOPWORDS}


rd.open_session()
banks = pd.read_csv("List_bank.csv")
banks = banks[banks["Symbol"].notna()].copy()
banks["ticker"] = banks["Ticker"].astype(str).str.upper()
universe = banks["Symbol"].tolist()
print(f"universe: {len(universe)} RICs from the Symbol column", flush=True)

# Verify identity once, on names, before pulling eight years of numbers.
names = []
for start in range(0, len(universe), 50):
    chunk = universe[start:start + 50]
    try:
        names.append(rd.get_data(chunk, ["TR.CommonName"]))
    except Exception as exc:
        print(f"  name lookup failed {start}: {exc}", flush=True)
names = pd.concat(names, ignore_index=True)
names.columns = ["Symbol", "vendor_name"]
check = banks.merge(names, on="Symbol", how="left")
check["name_ok"] = [
    bool(tokens(a) & tokens(b)) if pd.notna(b) else False
    for a, b in zip(check["Company"], check["vendor_name"])
]
rejected = check[~check["name_ok"]]
print(f"name check: {int(check['name_ok'].sum())}/{len(check)} verified", flush=True)
if not rejected.empty:
    print("REJECTED (ticker | expected | vendor returned):", flush=True)
    for _, r in rejected.iterrows():
        print(f"  {r['ticker']:6s} | {r['Company']} | {r['vendor_name']}", flush=True)
check.to_csv("ric_identity_check.csv", index=False)

verified = check[check["name_ok"]]
lookup = dict(zip(verified["Symbol"], verified["ticker"]))
universe = verified["Symbol"].tolist()

rows = []
for year in YEARS:
    fields = [f"{code}(Period=FY{year})" for code in FIELDS]
    for start in range(0, len(universe), 50):
        chunk = universe[start:start + 50]
        for _ in range(3):
            try:
                df = rd.get_data(chunk, fields)
                break
            except Exception as exc:
                print(f"  retry {year}/{start}: {exc}", flush=True)
                time.sleep(3)
        else:
            continue
        df.columns = ["Symbol"] + list(FIELDS.values())
        df["year"] = year
        rows.append(df)
    print(f"  FY{year} done", flush=True)

out = pd.concat(rows, ignore_index=True)
out["ticker"] = out["Symbol"].map(lookup)
out = out[["ticker", "Symbol", "year"] + list(FIELDS.values())]
for col in FIELDS.values():
    out[col] = pd.to_numeric(out[col], errors="coerce")
out = out[out["total_liabilities"].notna() & out["ticker"].notna()]
out.to_csv("total_liabilities_verified.csv", index=False)
print(f"\nrows {len(out)}  tickers {out['ticker'].nunique()}  "
      f"dupes {out.duplicated(['ticker','year']).sum()}")
