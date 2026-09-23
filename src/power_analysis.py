"""
§10 Power analysis: finding the minimum detectable effect.

Residual variance is computed on pre-adoption store-weeks only, after
absorbing store and week fixed effects, so that no treatment effect
contaminates the noise estimate.
"""
import numpy as np
import pandas as pd
from scipy import stats
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

q = """
SELECT store, week_start, log_sales, ever_treated, event_time
FROM panel_primary
WHERE event_time IS NULL OR event_time < 0
"""
df = pd.read_sql(q, engine, parse_dates=["week_start"])

# Absorb store and week fixed effects by double demeaning
y = df["log_sales"].values
store_mean = df.groupby("store")["log_sales"].transform("mean")
week_mean  = df.groupby("week_start")["log_sales"].transform("mean")
grand_mean = df["log_sales"].mean()

resid = y - store_mean - week_mean + grand_mean
sigma = resid.std(ddof=1)

print(f"Pre-period store-weeks:      {len(df):,}") # number of weeks in pre-period
print(f"Residual SD of log sales:    {sigma:.4f}") # standard deviation of residuals after absorbing store and week fixed effects

# ---------------------------------------------------------------------
# Minimum detectable effect
#
# Two versions. The naive one treats every store-week as independent.
# The corrected one accounts for serial correlation within stores
# (Bertrand, Duflo and Mullainathan 2004). Store-week sales are strongly
# autocorrelated, so the naive figure overstates power substantially;
# the corrected figure is the one reported.
# ---------------------------------------------------------------------

N_TREATED = 99
N_CONTROL = 520
ALPHA = 0.05
POWER = 0.80

z_a = stats.norm.ppf(1 - ALPHA / 2)   # 1.96
z_b = stats.norm.ppf(POWER)           # 0.84
M = z_a + z_b                         # 2.80

weeks_per_store = 83404 / 619

# --- Naive: independent store-weeks ---
se_naive = sigma * np.sqrt(
    (1 / (N_TREATED * weeks_per_store)) + (1 / (N_CONTROL * weeks_per_store))
)
mde_naive = M * se_naive

# --- Corrected: discount for within-store autocorrelation ---
df["resid"] = resid
rho = (
    df.sort_values(["store", "week_start"])
      .groupby("store")["resid"]
      .apply(lambda s: s.autocorr(lag=1))
      .mean()
)

n_eff = weeks_per_store / (1 + (weeks_per_store - 1) * rho)

se_corrected = sigma * np.sqrt(
    (1 / (N_TREATED * n_eff)) + (1 / (N_CONTROL * n_eff))
)
mde_corrected = M * se_corrected

print()
print(f"Mean lag-1 residual autocorrelation: {rho:.4f}") # average lag-1 autocorrelation of residuals
print(f"Weeks per store (avg):               {weeks_per_store:.1f}") # average number of weeks per store
print(f"Effective independent weeks/store:   {n_eff:.2f}") # effective number of independent weeks per store
print()
print(f"MDE, naive (independent weeks):      {mde_naive*100:.2f}%") # minimum detectable effect, naive approach
print(f"MDE, corrected for autocorrelation:  {mde_corrected*100:.2f}%") # minimum detectable effect, corrected approach