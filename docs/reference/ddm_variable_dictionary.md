# DDm Variable Dictionary

The table below summarizes every variable that participates in the Distance to Default (DDm) calculation implemented in `dd_pd_market.ipynb`.

| Variable | Description | Units / Source | Role in DDm computation |
| --- | --- | --- | --- |
| `T` | Time horizon over which default risk is evaluated. | Years (set to 1.0). | Scales both the drift term and volatility denominator in the DDm formula. |
| `asset_value` (`V`) | Firm asset value estimated by the Merton solver for each instrument-year observation. | USD (solved from equity market cap, equity volatility, debt). | Appears in the log leverage term `ln(V/F)` and influences the drift component. |
| `asset_vol` (`σ_V`) | Asset volatility returned by the Merton solver. | Annualized volatility (decimal). | Used in both the drift adjustment `(r_f - 0.5 σ_V^2)T` and the denominator `σ_V √T`. |
| `debt_total` | Total debt from source data reported in millions of USD. | Millions of USD (raw input). | Converted to actual USD before forming the leverage ratio. |
| `debt_total_usd` (`F`) | Debt converted from millions to actual USD for consistent leverage calculations. | USD (`debt_total * 1,000,000`). | Serves as the default barrier `F` inside `ln(V/F)`. |
| `rf` (`r_f`) | Annual risk-free rate merged from Fama-French data and converted from percent to decimal. | Decimal rate. | Provides the drift term `(r_f - 0.5 σ_V^2)T` in the numerator. |
| `solver_status` | Flag emitted by the Merton solver indicating solution quality (`converged`, `no_debt`, etc.). | Categorical status. | Rows flagged `no_debt` skip DDm computation and receive `NaN`. |
| `DDm` | Distance to Default metric computed per observation. | Standard deviations. | Result of combining the above inputs via the Merton formula. |

