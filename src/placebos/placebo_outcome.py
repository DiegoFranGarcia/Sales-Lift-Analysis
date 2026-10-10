"""
§8.4 Placebo outcome.

Estimate the same design on an outcome Promo2 cannot plausibly affect. A
non-null result would indicate a data artifact rather than a treatment effect.

The plan suggests open days per week. That outcome is nearly constant - most
stores open six days most weeks - so there is little variance for anything to
show up in, and a null here is weak evidence. Run and reported as specified;
not over-claimed.

A second placebo outcome is included: days observed per week, which is purely
a function of the calendar and cannot respond to anything a store does. That
one is a pure sanity check - a non-null there would mean something is wrong
with the panel construction itself.
"""
import os

import numpy as np
import pandas as pd
from diff_diff import CallawaySantAnna
from dotenv import load_dotenv
from sqlalchemy import create_engine

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

df = pd.read_sql("""
    SELECT store, week_start, log_sales, open_days, days_observed, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

# How much variance is there to detect anything in?
print("Outcome variation among treated stores:")
for col in ["open_days", "days_observed"]:
    s = df.loc[df.first_treat > 0, col]
    print(f"  {col:15s} mean {s.mean():.3f}  sd {s.std():.3f}  "
          f"range {s.min():.0f}-{s.max():.0f}")
print()

FIT = dict(unit="store", time="period", first_treat="first_treat")

for outcome, label in [
    ("open_days", "open days per week (plan's placebo outcome)"),
    ("days_observed", "days observed per week (calendar only)"),
    ("log_sales", "log sales (real outcome, for reference)"),
]:
    res = CallawaySantAnna(
        control_group="never_treated", estimation_method="dr",
        base_period="universal", n_bootstrap=199,
        bootstrap_weights="mammen", seed=42,
    ).fit(df, outcome=outcome, **FIT)

    b = res.bootstrap_results
    att = res.overall_att
    print(f"{label}")
    print(f"  ATT      : {att:+.4f}")
    print(f"  Boot SE  : {b.overall_att_se:.4f}")
    print(f"  95% CI   : [{b.overall_att_ci[0]:+.4f}, {b.overall_att_ci[1]:+.4f}]")
    print(f"  p-value  : {b.overall_att_p_value:.4f}")
    print()