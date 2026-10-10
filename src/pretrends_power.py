"""
Roth (2022) pre-trends power analysis.

§8.1 passed (0 of 11 uniform bands excluded zero in the near window). §8.3
then found -4.02% from a fake adoption date. This asks whether §8.1's test
had the power to detect the violation §8.3 found.

The minimum detectable violation (MDV) is the smallest linear pre-trend the
pre-test would reject with the stated power. If the MDV exceeds the drift the
placebo picked up, §8.1 passing is uninformative rather than reassuring.

Same event window and no-bootstrap constraint as the Honest DiD run
(deviations.md, 2026-10-01).
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna, PreTrendsPower
from sqlalchemy import create_engine

WINDOW = 26
import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week, event_time
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

keep = df.event_time.isna() | df.event_time.between(-WINDOW, WINDOW)
d = df[keep].copy()

weeks = sorted(d["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
d["period"] = d["week_start"].map(wi)
d["first_treat"] = d["adoption_week"].map(wi).fillna(0).astype(int)

res = CallawaySantAnna(
    control_group="never_treated", estimation_method="dr",
    base_period="universal",
).fit(d, outcome="log_sales", unit="store", time="period",
      first_treat="first_treat", aggregate="event_study")

pt = PreTrendsPower()
pt_res = pt.fit(res)

print(pt_res)
print()
for attr in ["mdv", "power", "slope", "bias", "likelihood_ratio"]:
    if hasattr(pt_res, attr):
        print(f"{attr:20s} {getattr(pt_res, attr)}")