#!/usr/bin/env python3
"""
Accounting-approach Distance to Default and Probability of Default
Updated to use daily-derived annual returns for drift calculation

Implements Bharath and Shumway (2008) naive DD approach.
Uses V_hat=E+F, sigma_D_hat=0.05+0.25*sigma_E, value-weighted sigma_V_hat,
and mu_hat from daily-derived annual returns (NOT rit).
"""

import math
from pathlib import Path
import numpy as np
import pandas as pd

try:
    from scipy.stats import norm
    Phi = norm.cdf
except Exception:
    from math import erf
    def Phi(x):
        x = np.asarray(x, dtype=float)
        return 0.5*(1.0 + np.vectorize(erf)(x/np.sqrt(2.0)))

pd.set_option('display.width', 120)
pd.set_option('display.max_columns', 40)

MM = 1_000_000.0
T = 1.0

def find_repo_root(start: Path, marker: str = '.git') -> Path:
    """Walk up from *start* until a directory containing *marker* is found."""
    current = start.resolve()
