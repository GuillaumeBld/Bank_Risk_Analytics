KMV-Merton’s Distance-to-Default Model

The pioneering work of Merton (1974) is the approach used to measure the bank distance-to-default and expected default frequency. Kealhofer, McQuown, and Vasicek (KMV, a unit of Moody’s Analytics) extended the model to calculate the expected default frequencies for publicly traded firms; hence the reference to KMV-Merton model). Implementing the model begins with premise of viewing the firm’s equity as a call option written on the distributional information on the value of the firm (current value (V) and its standard deviation (σV)), the face value of the firm’s debt representing the strike price (F), and the time to maturity of debt characterizing the horizon for this valuation (T).With the exception of V and σV, all other variables are either publicly available with exception of  the standard deviation of equity returns, σE, which can be estimated from past data. The unobservable variables can be estimated using the option pricing and equity volatility equations (1), and (2) below.

E=V"Φ" (d_1 )-Fe^((-rT) ) "Φ" (d_2 )								(1)

σ_E=(V/E)Φ(d_1 ) σ_V									(2)

These two equations come from the Black-Scholes-Merton option pricing framework (Merton, 1974). Equation (1) treats equity as a European call option on the firm's assets with a strike price equal to the debt level. The first term, V×Φ(d_1), represents the expected asset value weighted by the probability that assets will exceed debt at maturity. The second term, F×e^(-rT)×Φ(d_2), is the present value of debt weighted by the risk-adjusted probability of payment. Equation (2) relates equity volatility to asset volatility through the leverage effect: since equity holders have a LEVERAGED claim on assets, equity volatility is amplified by the factor (V/E)×Φ(d_1), which captures both the leverage ratio and the option's delta (sensitivity to asset changes).

where d_1=[ln"(V/F)+(r+0.5σ_V^2 )T]/(σ_V √T),  d_2=d_1-σ_V √T, r is the risk free rate of interest and Φ is the standard normal cumulative probability distribution.  

A numerical root-finding algorithm is then applied to find V and σV simultaneously feeding directly into the distance-to-default calculation in equation (3). In our implementation, we use SciPy's root function with the hybrid method. The solver starts with intuitive initial guesses: V₀ = E + F (total firm value equals equity plus debt) and σ_V₀ = σ_E (asset volatility approximates equity volatility). The algorithm iteratively adjusts these values until both equations (1) and (2) are satisfied—that is, until the model-implied equity value and volatility match the observed market data within a small tolerance (price residual < 10⁻⁶, volatility residual < 10⁻⁴). This converged solution provides the asset value V and asset volatility σ_V needed for the DD calculation.

**Variable Definitions and Timing**

**CRITICAL: Time Index Conventions to Prevent Lookahead Bias**

| Variable | Description | Time Period | Source | Notes |
|----------|-------------|-------------|--------|-------|
| E_t | Market value of equity | Current (t) | Stock price × shares outstanding | Observed at t |
| σ_{E,t-1} | Equity volatility | **Prior (t-1)** | 3-year rolling std of returns **up to t-1 only** | **No future data** |
| F_t | Face value of debt | Current (t) | Balance sheet (total liabilities for banks) | Observed at t |
| r_{f,t} | Risk-free rate | Current (t) | Fama-French annual factors | Observed at t |
| T | Time horizon | Fixed | 1 year | From t to t+1 |
| V_t | Asset value (solved) | Current (t) | Output from solver | Solved at t |
| σ_{V,t} | Asset volatility (solved) | Current (t) | Output from solver | Solved at t |
| μ_V | Asset drift | Varies by approach | Market: r_{f,t}; Accounting: r_{i,t-1} | **t-1 for accounting** |

**Key Timing Rules**:
- σ_{E,t-1} uses **only** returns up to year t-1 (window ends strictly at t-1)
- For accounting approach: μ_hat_t = r_{i,t-1} (previous year's equity return)
- All windows validated to exclude current and future data
- Provenance tracked: sigmaE_window_start_year, sigmaE_window_end_year, mu_source_year

DD=["ln" (V/F)+(μ_V-0.5σ_V^2 )×T]/(σ_V×√T)								(3)
Where
    "ln" (V/F) is the natural logarithm of the ratio of total assets (V) to the default barrier (F). In our implementation, F represents **total liabilities** for banks (deposits are liabilities and dominate bank funding). A large and positive number indicates assets significantly exceed liabilities.
    
    (μ_V-0.5σ_V^2 )×T accounts for the expected growth (or drift) of assets over the chosen timeframe (T = 1 year), adjusted by a volatility factor σ_V^2. The drift parameter μ_V varies by approach:
        - Market approach (DD_m): μ_V = r_t (risk-free rate at time t), following the risk-neutral Q-measure
        - Accounting approach (DD_a): μ_V = r_i,t-1 (lagged equity return), following the real-world P-measure
    
    σ_V×√T measures asset-value fluctuations over the period.

Finally, the expected default frequency (EDF) representing the probability that the value of the firm will be less than the face value of the debt at maturity will be equal the cumulative probability of the DD represented in equation (4) and visually shown in Figure (1).

EDF =  {-( ["ln" (V/F)+(μ_V-0.5σ_V^2 )×T]/(σ_V×√T))} =  (-DD)						(4)



Tepe, M., Thastrom, P., and Chang, R. How Does ESG Activities Affect default Risk, https://ficonsulting.com/wp-content/uploads/2022/04/FI_ESG_WP_2022.pdf

Following Bharath and Shumway (2008), Badghdadi et al. (2019), and Mckenna (2021) a simplified version of the EDF is used where  the asset value (V) is equal to the sum of market value of equity and face value of debt (E+ F), asset volatility (σV) is computed as the average volatility, and the drift of
asset value μ is an estimate of the expected annual return of the firm's assets using the previous monthly equity rates of return. The probability of default under the simplified model is presented in equation (5)
EDF =  {-( ["ln" (E+F/F)+(μ_E-0.5〖 Simplified σ〗_V^2 )×T]/(Simplified σ_V×√T))} =  (-DD)				(5)


**Examples: JPMorgan Chase and Bank of America (2019)**

### Example 1: JPMorgan Chase (JPM) - Market Approach

**Observable Inputs (time t = 2019)**

| Variable | Value | Source |
|----------|-------|--------|
| E (Market Cap) | $387.4 billion | Stock price × shares |
| σ_E (Equity Vol) | 0.227 (22.7%) | 3-year rolling std |
| F (Debt Total) | $516.093 billion | Balance sheet |
| r (Risk-Free Rate) | 0.0214 (2.14%) | Fama-French |
| T (Time Horizon) | 1 year | Fixed |

**Solver Output**

| Variable | Value |
|----------|-------|
| V (Asset Value) | $892.6 billion |
| σ_V (Asset Vol) | 0.099 (9.9%) |

**DD and PD Calculation**

DD_m = [ln(892.6/516.1) + (0.0214 - 0.5×0.099²)×1] / (0.099×1)
     = [0.548 + 0.0165] / 0.099
     = 5.70

PD_m = Φ(-5.70) = 0.000006% (essentially zero)

**Interpretation:** JPM's assets are 5.7 volatility steps above debt, indicating very low default risk.

### Example 2: Bank of America (BAC) - Market Approach

**Observable Inputs (time t = 2019)**

| Variable | Value | Source |
|----------|-------|--------|
| E (Market Cap) | $265.3 billion | Stock price × shares |
| σ_E (Equity Vol) | 0.279 (27.9%) | 3-year rolling std |
| F (Debt Total) | $430.169 billion | Balance sheet |
| r (Risk-Free Rate) | 0.0214 (2.14%) | Fama-French |
| T (Time Horizon) | 1 year | Fixed |

**Solver Output**

| Variable | Value |
|----------|-------|
| V (Asset Value) | $686.3 billion |
| σ_V (Asset Vol) | 0.108 (10.8%) |

**DD and PD Calculation**

DD_m = [ln(686.3/430.2) + (0.0214 - 0.5×0.108²)×1] / (0.108×1)
     = [0.467 + 0.0156] / 0.108
     = 4.47

PD_m = Φ(-4.47) = 0.0004%

**Interpretation:** BAC is 4.47 volatility steps from default, slightly higher risk than JPM but still very safe.

### Comparison

| Bank | DD_m | PD_m | Asset Value | Asset Vol | Risk Level |
|------|------|------|-------------|-----------|------------|
| JPM | 5.70 | 0.000006% | $892.6B | 9.9% | Very Safe |
| BAC | 4.47 | 0.0004% | $686.3B | 10.8% | Safe |

**Key Insights:**
- JPM has 1.23 more volatility steps of safety
- JPM's PD is 67× lower than BAC's
- JPM has lower asset volatility (more stable)
- Both banks show very low default risk










