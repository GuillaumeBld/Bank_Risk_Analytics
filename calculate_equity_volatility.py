"""
This script calculates annualized equity volatility for each bank and year from monthly close prices.
Inputs:
  - bank_monthly_close_prices_2016_2023_new banks.csv
Outputs:
  - equity_volatility_by_year.csv
Log:
  - calculate_equity_volatility_log.txt
"""
import pandas as pd
import numpy as np

input_file = 'esg-default-risk-phase1/data/clean/bank_monthly_close_prices_2016_2023_merged.csv'
output_file = 'equity_volatility_by_year.csv'
output_12m = 'equity_volatility_rolling_12m.csv'
output_24m = 'equity_volatility_rolling_24m.csv'
log_file = 'calculate_equity_volatility_log.txt'

try:
    df = pd.read_csv(input_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['year'] = df['Date'].dt.year
    df['month'] = df['Date'].dt.month
    results = []
    results_12m = []
    results_24m = []
    tickers = [col for col in df.columns if col not in ['Date', 'year', 'month']]
    for ticker in tickers:
        sub = df[['Date', 'year', 'month', ticker]].dropna().sort_values('Date')
        sub = sub.rename(columns={ticker: 'price'})
        sub['return'] = sub['price'].pct_change()
        sub = sub.dropna(subset=['return'])
        # Rolling 12m and 24m volatility
        sub['rolling_12m_vol'] = sub['return'].rolling(window=12, min_periods=10).std() * np.sqrt(12)
        sub['rolling_24m_vol'] = sub['return'].rolling(window=24, min_periods=20).std() * np.sqrt(12)
        for idx, row in sub.iterrows():
            note_12m = '' if not np.isnan(row['rolling_12m_vol']) else 'not enough data for 12m window'
            note_24m = '' if not np.isnan(row['rolling_24m_vol']) else 'not enough data for 24m window'
            results_12m.append({
                'symbol': ticker,
                'year': row['year'],
                'month': row['month'],
                'rolling_12m_volatility': row['rolling_12m_vol'],
                'note': note_12m
            })
            results_24m.append({
                'symbol': ticker,
                'year': row['year'],
                'month': row['month'],
                'rolling_24m_volatility': row['rolling_24m_vol'],
                'note': note_24m
            })
        # Preserve original annual calculation
        for year, group in sub.groupby('year'):
            prices = group['price']
            returns = prices.pct_change().dropna()
            if len(returns) >= 2:
                vol = returns.std() * np.sqrt(12)
                results.append({'symbol': ticker, 'year': year, 'equity_volatility': vol, 'equity_volatility_note': np.nan})
            else:
                results.append({'symbol': ticker, 'year': year, 'equity_volatility': np.nan, 'equity_volatility_note': 'number of return too low for equity vol'})
    outdf = pd.DataFrame(results)
    outdf_12m = pd.DataFrame(results_12m)
    outdf_24m = pd.DataFrame(results_24m)
    if 'equity_volatility_note' not in outdf.columns:
        outdf['equity_volatility_note'] = np.nan
    outdf.to_csv(output_file, index=False)
    outdf_12m.to_csv(output_12m, index=False)
    outdf_24m.to_csv(output_24m, index=False)
    with open(log_file, 'w') as log:
        log.write(f"Successfully calculated equity volatility for {len(outdf)} bank-years.\n")
        log.write(f"Output: {output_file}\n")
        log.write(f"Rolling 12m output: {output_12m}\n")
        log.write(f"Rolling 24m output: {output_24m}\n")
    print(f"Calculation complete. Output: {output_file}")
    print(f"Rolling 12m output: {output_12m}")
    print(f"Rolling 24m output: {output_24m}")
except Exception as e:
    with open(log_file, 'w') as log:
        log.write(f"Error: {e}\n")
    print(f"Error: {e}") 