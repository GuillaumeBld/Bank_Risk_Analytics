"""
Tests for time integrity validation in DD/PD calculations.

Ensures that:
1. σ_E is computed only from returns up to t-1
2. μ̂ equals r_{i,t-1}
3. Assertions catch lookahead violations
"""

import numpy as np
import pandas as pd
import pytest
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.time_checks import assert_time_integrity, validate_no_lookahead


def create_test_panel(n_firms=2, n_years=4):
    """Create a small test panel with known returns."""
    data = []
    for firm in ['A', 'B'][:n_firms]:
        for year in range(2020, 2020 + n_years):
            data.append({
                'instrument': firm,
                'year': year,
                'rit': 0.1 * (year - 2020) + (0.05 if firm == 'A' else -0.05)
            })
    return pd.DataFrame(data)


def compute_sigma_E_tminus1(df):
    """Compute σ_E using only data up to t-1."""
    df = df.sort_values(['instrument', 'year'])
    
    def rolling_sigma_prior(s):
        return s.shift(1).rolling(3, min_periods=2).std()
    
    df['sigma_E_tminus1'] = df.groupby('instrument', group_keys=False)['rit'].apply(rolling_sigma_prior)
    df['sigmaE_count'] = df.groupby('instrument', group_keys=False)['rit'].apply(
        lambda s: s.shift(1).rolling(3, min_periods=1).count()
    )
    df['sigmaE_window_end_year'] = df['year'] - 1
    # Only set window start when we have data
    df['sigmaE_window_start_year'] = np.where(
        df['sigmaE_count'] > 0,
        df['year'] - df['sigmaE_count'].clip(upper=3).astype(int),
        df['year'] - 1  # When no data, set start = end to avoid violations
    )
    
    return df


def compute_mu_hat(df):
    """Compute μ̂ = r_{i,t-1}."""
    df = df.sort_values(['instrument', 'year'])
    df['mu_hat_from'] = 'rit_tminus1'
    df['mu_hat'] = df.groupby('instrument', group_keys=False)['rit'].shift(1)
    df['mu_source_year'] = df['year'] - 1
    return df


class TestTimeIntegrity:
    """Test suite for time integrity validation."""
    
    def test_sigma_E_uses_only_past_data(self):
        """Test that σ_E is computed from returns up to t-1 only."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_sigma_E_tminus1(df)
        
        # Check that window end is always t-1
        assert (df['sigmaE_window_end_year'] == df['year'] - 1).all()
        
        # Check that σ_E for year t uses only years up to t-1
        firm_a = df[df['instrument'] == 'A']
        
        # Year 2020: no prior data, should be NaN
        assert pd.isna(firm_a[firm_a['year'] == 2020]['sigma_E_tminus1'].iloc[0])
        
        # Year 2021: only 2020 data (1 point), should be NaN (min_periods=2)
        assert pd.isna(firm_a[firm_a['year'] == 2021]['sigma_E_tminus1'].iloc[0])
        
        # Year 2022: 2020-2021 data (2 points), should have value
        assert pd.notna(firm_a[firm_a['year'] == 2022]['sigma_E_tminus1'].iloc[0])
        
        # Year 2023: 2020-2022 data (3 points), should have value
        assert pd.notna(firm_a[firm_a['year'] == 2023]['sigma_E_tminus1'].iloc[0])
    
    def test_mu_hat_equals_lagged_return(self):
        """Test that μ̂_t equals r_{i,t-1}."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_mu_hat(df)
        
        # Check that mu_hat for year t equals rit from year t-1
        for instrument in df['instrument'].unique():
            firm_data = df[df['instrument'] == instrument].sort_values('year')
            
            for i in range(1, len(firm_data)):
                current_row = firm_data.iloc[i]
                previous_row = firm_data.iloc[i-1]
                
                if pd.notna(current_row['mu_hat']):
                    assert np.isclose(current_row['mu_hat'], previous_row['rit'])
                    assert current_row['mu_source_year'] == previous_row['year']
    
    def test_time_integrity_passes_valid_data(self):
        """Test that valid data passes time integrity checks."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_sigma_E_tminus1(df)
        df = compute_mu_hat(df)
        
        # Should not raise
        assert_time_integrity(df)
        assert validate_no_lookahead(df, verbose=False)
    
    def test_lookahead_sigma_E_raises_error(self):
        """Test that lookahead in σ_E window raises AssertionError."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_sigma_E_tminus1(df)
        
        # Inject lookahead: set window end to current year (should be t-1)
        df.loc[df['year'] == 2022, 'sigmaE_window_end_year'] = 2022  # Should be 2021
        
        # Should raise AssertionError
        with pytest.raises(AssertionError, match="σ_E window end must be t-1"):
            assert_time_integrity(df)
    
    def test_lookahead_mu_hat_raises_error(self):
        """Test that lookahead in μ̂ source raises AssertionError."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_mu_hat(df)
        
        # Inject lookahead: set mu source year to current year (should be t-1)
        df.loc[df['year'] == 2022, 'mu_source_year'] = 2022  # Should be 2021
        
        # Should raise AssertionError
        with pytest.raises(AssertionError, match="μ̂ source year must be t-1"):
            assert_time_integrity(df)
    
    def test_future_data_in_window_raises_error(self):
        """Test that future data in σ_E window raises AssertionError."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_sigma_E_tminus1(df)
        
        # Inject future data: set window end to future year
        df.loc[df['year'] == 2022, 'sigmaE_window_end_year'] = 2023  # Future!
        
        # Should raise AssertionError
        with pytest.raises(AssertionError, match="cannot include current or future years"):
            assert_time_integrity(df)
    
    def test_invalid_window_order_raises_error(self):
        """Test that window start > window end raises AssertionError."""
        df = create_test_panel(n_firms=2, n_years=4)
        df = compute_sigma_E_tminus1(df)
        
        # Inject invalid window: start > end
        df.loc[df['year'] == 2022, 'sigmaE_window_start_year'] = 2022
        df.loc[df['year'] == 2022, 'sigmaE_window_end_year'] = 2020
        
        # Should raise AssertionError
        with pytest.raises(AssertionError, match="window start must be <= window end"):
            assert_time_integrity(df)


class TestRollingVolatilityComputation:
    """Test that rolling volatility computation is correct."""
    
    def test_rolling_std_matches_manual_calculation(self):
        """Test that rolling σ_E matches manual calculation."""
        # Create simple test case with known returns
        df = pd.DataFrame({
            'instrument': ['A'] * 5,
            'year': [2020, 2021, 2022, 2023, 2024],
            'rit': [0.1, 0.2, 0.15, 0.25, 0.18]
        })
        
        df = compute_sigma_E_tminus1(df)
        
        # For year 2023, σ_E should use returns from 2020, 2021, 2022
        # Manual calculation: std([0.1, 0.2, 0.15])
        expected_sigma_2023 = np.std([0.1, 0.2, 0.15], ddof=1)
        actual_sigma_2023 = df[df['year'] == 2023]['sigma_E_tminus1'].iloc[0]
        
        assert np.isclose(actual_sigma_2023, expected_sigma_2023)
        
        # For year 2024, σ_E should use returns from 2021, 2022, 2023 (3-year window)
        expected_sigma_2024 = np.std([0.2, 0.15, 0.25], ddof=1)
        actual_sigma_2024 = df[df['year'] == 2024]['sigma_E_tminus1'].iloc[0]
        
        assert np.isclose(actual_sigma_2024, expected_sigma_2024)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
