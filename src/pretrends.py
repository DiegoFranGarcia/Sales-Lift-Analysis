"""
§8.1 Pre-trend assessment via Callaway-Sant'Anna uniform confidence bands.

§8 pre-commits: if pre-trend coefficients are jointly significant, report that
prominently and frame the estimate as suggestive rather than causal.

Uniform (simultaneous) confidence bands from the multiplier bootstrap are the
right test here - they account for testing many horizons at once, unlike
pointwise intervals.

Long horizons are excluded. The event_study table's `n` column counts
contributing COHORTS, and at event time below about -60 only one or two
late-adopting cohorts are in scope, so those coefficients describe a handful
of stores rather than the sample.
"""
import os

import numpy as np
import pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine
from sqlalchemy import create_engine
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
week_index = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(week_index)
df["first_treat"] = df["adoption_week"].map(week_index).fillna(0).astype(int)

res = CallawaySantAnna(
    control_group="never_treated",
    estimation_method="dr",
    base_period="universal",
    n_bootstrap=999,
    bootstrap_weights="mammen",
    seed=42,
).fit(df, outcome="log_sales", unit="store", time="period",
      first_treat="first_treat")

es = res.aggregate("event_study").to_dataframe()
es.to_csv("outputs/cs_event_study_boot.csv", index=False)

pre = es[(es.event_time < 0) & (~es.is_reference)].copy()

# How many cohorts back each horizon
print("Cohorts contributing, by horizon:")
for lo, hi in [(-130, -100), (-99, -60), (-59, -26), (-25, -13), (-12, -1)]:
    w = pre[(pre.event_time >= lo) & (pre.event_time <= hi)]
    if len(w):
        print(f"  {lo:>5} to {hi:>4}: n cohorts {int(w.n.min())}-{int(w.n.max())},"
              f"  {len(w)} horizons")

print()
for lo, hi, label in [(-52, -1, "-52 to -1"),
                      (-26, -1, "-26 to -1"),
                      (-12, -1, "-12 to -1")]:
    w = pre[(pre.event_time >= lo) & (pre.event_time <= hi)]
    has_band = w.cband_lower.notna()
    band_excl = ((w.cband_lower > 0) | (w.cband_upper < 0)).sum()
    point_excl = ((w.conf_int_lower > 0) | (w.conf_int_upper < 0)).sum()
    print(f"{label}:  {len(w)} horizons")
    print(f"  mean coefficient            : {w.att.mean():+.4f}")
    print(f"  largest |coefficient|       : {w.att.abs().max():.4f}")
    print(f"  pointwise CI excludes zero  : {point_excl}/{len(w)}")
    if has_band.any():
        print(f"  uniform band excludes zero  : {band_excl}/{int(has_band.sum())}")
    else:
        print("  uniform band               : not available")
    print()

print("Near pre-period, horizon by horizon:")
near = pre[pre.event_time >= -12].sort_values("event_time")
print(near[["event_time", "att", "se", "conf_int_lower", "conf_int_upper",
            "cband_lower", "cband_upper", "n"]].to_string(index=False))