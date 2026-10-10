# src/honest_did.py
"""
Rambachan-Roth (2023) sensitivity analysis.

The §8.3 placebo fired (-3.16% on 62 stores, -4.02% on 93), indicating a
pre-adoption drift. Rather than treating parallel trends as pass/fail, Honest
DiD asks how large the violation would have to be to overturn the result.

Two restrictions:
  relative_magnitude - post-treatment violation at most M times the largest
                       pre-treatment violation. Breakdown M < 1 means the
                       result dies under a violation SMALLER than one already
                       visible in the pre-period.
  smoothness         - violation's second differences bounded by M; allows a
                       linear pre-trend to extrapolate forward.

NOTE: n_bootstrap must be 0. diff-diff issue #836 - bootstrapping clears
event_study_vcov, dropping cross-horizon covariance, and Honest DiD intervals
come out far too narrow.

Event window restricted to -26..+26 (deviations.md). The full -126..+108 range
would set the relative-magnitude benchmark off long-horizon cells resting on
1-4 cohorts.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna, HonestDiD
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
WINDOW = 26

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week, event_time
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

# Restrict treated stores to the event window; keep controls whole
keep = df.event_time.isna() | df.event_time.between(-WINDOW, WINDOW)
d = df[keep].copy()

weeks = sorted(d["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
d["period"] = d["week_start"].map(wi)
d["first_treat"] = d["adoption_week"].map(wi).fillna(0).astype(int)

print(f"Store-weeks in window : {len(d):,}")
print(f"Treated stores        : {d.loc[d.first_treat > 0, 'store'].nunique()}")

# aggregate at fit time: sensitivity analyses read the fit-time surface
res = CallawaySantAnna(
    control_group="never_treated", estimation_method="dr",
    base_period="universal",
).fit(d, outcome="log_sales", unit="store", time="period",
      first_treat="first_treat", aggregate="event_study")

print(f"\nATT on restricted window: {res.overall_att:+.4f} "
      f"({(np.exp(res.overall_att)-1)*100:+.2f}%)")
print(f"  (full-window ATT was +0.0428, +4.37%)")

for method in ["relative_magnitude", "smoothness"]:
    h = HonestDiD(method=method)
    bd = h.breakdown_value(res)
    print(f"\n{method}: breakdown M = {bd}")

h = HonestDiD(method="relative_magnitude")
sens = h.sensitivity_analysis(res, M_grid=[0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
print("\nSensitivity over M:")
print(sens)