# src/cs_twfe_reconcile.py
"""
Reconciling CS (+4.37%) and TWFE (+0.67%).

CS anchors every post-treatment ATT(g,t) to week g-1. TWFE differences against
the full pre-period. If the treated group's pre-period average sits ~0.036
above g-1 in DiD terms, the two estimates are the same number measured from
different baselines.

Event-study pre-period coefficients ARE that quantity: each is the treated-vs-
control difference at horizon e, relative to g-1. Weighting them by treated
store-weeks at each horizon approximates TWFE's implicit baseline.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine

engine = create_engine("postgresql://diegogarcia@localhost:5432/rossmann")
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week, event_time
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

res = CallawaySantAnna(control_group="never_treated", estimation_method="dr",
                       base_period="universal").fit(
    df, outcome="log_sales", unit="store", time="period", first_treat="first_treat")

es = res.aggregate("event_study").to_dataframe()
pre = es[(es.event_time < 0) & (~es.is_reference)].dropna(subset=["att"])

# Treated store-weeks at each pre horizon - TWFE's implicit weighting
w = (df[df.event_time.notna() & (df.event_time < 0)]
     .groupby("event_time").size().rename("store_weeks"))

pre = pre.merge(w, left_on="event_time", right_index=True, how="inner")

weighted  = np.average(pre.att, weights=pre.store_weeks)
unweighted = pre.att.mean()

att_cs, att_twfe = 0.0428, 0.0067

print(f"CS overall ATT (anchored at g-1)        : {att_cs:+.4f}")
print(f"TWFE                                    : {att_twfe:+.4f}")
print(f"Gap to explain                          : {att_cs - att_twfe:+.4f}")
print()
print(f"Pre-period mean, unweighted             : {unweighted:+.4f}")
print(f"Pre-period mean, weighted by store-weeks: {weighted:+.4f}")
print()
print(f"CS minus weighted pre-period baseline   : {att_cs - weighted:+.4f}")
print(f"                              vs TWFE   : {att_twfe:+.4f}")