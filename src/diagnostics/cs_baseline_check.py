# src/cs_baseline_check.py
"""
Why does CS (+4.37%) exceed TWFE (+0.67%) by 6.5x?

Hypothesis: the base period. CS with base_period="universal" anchors every
ATT(g,t) to week -1. The event study shows pre-period coefficients drifting
upward the further back you look (+0.0125 at -12, +0.0213 at -26, +0.0268 at
-52), so week -1 sits slightly below the treated group's longer-run level
relative to controls. TWFE has no such anchor - it differences against the
whole-panel mean.

Varying the base period is the direct test. The other three runs rule out
estimation method as a confound.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine

engine = create_engine("postgresql://diegogarcia@localhost:5432/rossmann")
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

FIT = dict(outcome="log_sales", unit="store", time="period", first_treat="first_treat")
pct = lambda x: (np.exp(x) - 1) * 100

runs = [
    ("universal base, dr  (current)", dict(base_period="universal", estimation_method="dr")),
    ("varying base,   dr",            dict(base_period="varying",   estimation_method="dr")),
    ("universal base, reg",           dict(base_period="universal", estimation_method="reg")),
    ("universal base, ipw",           dict(base_period="universal", estimation_method="ipw")),
]

print(f"{'specification':32s} {'log pt':>9} {'percent':>9}")
print("-" * 52)
for label, kw in runs:
    r = CallawaySantAnna(control_group="never_treated", **kw).fit(df, **FIT)
    print(f"{label:32s} {r.overall_att:>+9.4f} {pct(r.overall_att):>+8.2f}%")

print("-" * 52)
print(f"{'TWFE (reference)':32s} {0.0067:>+9.4f} {0.67:>+8.2f}%")