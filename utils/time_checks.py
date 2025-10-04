"""
Time integrity validation for DD/PD calculations.

Ensures no lookahead bias by validating that:
- σ_E uses only data up to t-1
- μ̂ uses only data from t-1
- All time windows are correctly specified
"""

import numpy as np
import pandas as pd


def assert_time_integrity(df: pd.DataFrame) -> None:
    """
    Validate time integrity of DD/PD calculation inputs.
    
    Raises AssertionError if any lookahead bias is detected.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with time-tagged columns including:
        - year: current year (t)
        - sigmaE_window_end_year: last year used in σ_E calculation
        - mu_hat_from: source of μ̂ (if present)
        - mu_source_year: year of μ̂ source (if present)
    
    Raises
    ------
    AssertionError
        If any time integrity violations are detected
    """
    errs = []
    
    # Check 1: σ_E window must end at t-1
    if "sigmaE_window_end_year" in df.columns:
        bad_sigma = df["sigmaE_window_end_year"] != (df["year"] - 1)
        if bad_sigma.any():
            n_bad = bad_sigma.sum()
            errs.append(f"σ_E window end must be t-1 ({n_bad} violations)")
    
    # Check 2: μ̂ source year must be t-1 when using lagged return
    if "mu_hat_from" in df.columns and "mu_source_year" in df.columns:
        uses_lag = df["mu_hat_from"].eq("rit_tminus1")
        bad_mu = uses_lag & (df["mu_source_year"] != df["year"] - 1)
        if bad_mu.any():
            n_bad = bad_mu.sum()
            errs.append(f"μ̂ source year must be t-1 when using lagged return ({n_bad} violations)")
    
    # Check 3: Window start year must be <= window end year
    if "sigmaE_window_start_year" in df.columns and "sigmaE_window_end_year" in df.columns:
        bad_window = df["sigmaE_window_start_year"] > df["sigmaE_window_end_year"]
        if bad_window.any():
            n_bad = bad_window.sum()
            errs.append(f"σ_E window start must be <= window end ({n_bad} violations)")
    
    # Check 4: Window end year must be < current year (no future data)
    if "sigmaE_window_end_year" in df.columns:
        future_data = df["sigmaE_window_end_year"] >= df["year"]
        if future_data.any():
            n_bad = future_data.sum()
            errs.append(f"σ_E window cannot include current or future years ({n_bad} violations)")
    
    if errs:
        raise AssertionError("Time integrity violations: " + "; ".join(errs))


def validate_no_lookahead(df: pd.DataFrame, verbose: bool = True) -> bool:
    """
    Validate DataFrame for lookahead bias and return True if valid.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to validate
    verbose : bool, default True
        Print validation results
    
    Returns
    -------
    bool
        True if no lookahead bias detected, False otherwise
    """
    try:
        assert_time_integrity(df)
        if verbose:
            print("✅ Time integrity check passed: No lookahead bias detected")
        return True
    except AssertionError as e:
        if verbose:
            print(f"❌ Time integrity check failed: {e}")
        return False


def add_time_provenance_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add summary columns describing time provenance.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with time-tagged columns
    
    Returns
    -------
    pd.DataFrame
        DataFrame with added summary columns
    """
    df = df.copy()
    
    # Add σ_E window size
    if "sigmaE_window_start_year" in df.columns and "sigmaE_window_end_year" in df.columns:
        df["sigmaE_window_years"] = (
            df["sigmaE_window_end_year"] - df["sigmaE_window_start_year"] + 1
        )
    
    # Add time lag indicator
    if "sigmaE_window_end_year" in df.columns:
        df["sigmaE_lag_years"] = df["year"] - df["sigmaE_window_end_year"]
    
    return df
