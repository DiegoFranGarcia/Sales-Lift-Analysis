"""
§7 Two-way fixed effects estimate and Goodman-Bacon decomposition.

Purpose
-------
TWFE is the standard DiD workhorse and the estimate most analysts would
report. Under staggered adoption it is also known to be biased: the single
coefficient is a weighted average of all possible 2x2 DiD comparisons in the
panel, and some of those comparisons use ALREADY-TREATED stores as controls
for LATER-TREATED ones. Those comparisons are contaminated by the earlier
group's own treatment effect, and their weights can be negative.

This script computes the TWFE estimate and then decomposes it (Goodman-Bacon
2021) to show how much weight sits on clean versus contaminated comparisons.
The decomposition, not the coefficient, is the point.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sqlalchemy import create_engine

engine = create_engine("postgresql://diegogarcia@localhost:5432/rossmann")

df = pd.read_sql("""
    SELECT store, week_start, log_sales,
           ever_treated, post_treatment, adoption_week, cohort_quarter
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week", "cohort_quarter"])

df["treat"] = df["post_treatment"].fillna(False).astype(int)

# ---------------------------------------------------------------------
# TWFE
#
# C(store) and C(week_start) are the fixed effects. With 619 stores and 135
# weeks this is a large but tractable dummy-variable regression.
#
# The coefficient on `treat` is the TWFE DiD estimate.
# ---------------------------------------------------------------------
m = smf.ols("log_sales ~ treat + C(store) + C(week_start)", data=df).fit(
    cov_type="cluster", cov_kwds={"groups": df["store"]}
)

b  = m.params["treat"]
se = m.bse["treat"]
lo, hi = m.conf_int().loc["treat"]

print("TWFE (store + week fixed effects)")
print(f"  log-point estimate : {b:+.4f}  (SE {se:.4f})")
print(f"  95% CI             : [{lo:+.4f}, {hi:+.4f}]")
print(f"  approx. % effect   : {(np.exp(b)-1)*100:+.2f}%")
print(f"  CI in %            : [{(np.exp(lo)-1)*100:+.2f}%, {(np.exp(hi)-1)*100:+.2f}%]")

# ---------------------------------------------------------------------
# Goodman-Bacon decomposition
#
# The package needs:
#   unit        - store id
#   time        - an ORDERED integer period index (not a date)
#   first_treat - the period index of adoption; 0 means never-treated
#
# Both week_start and adoption_week are mapped onto the same integer
# grid so that "period 47" means the same thing in both columns.
# ---------------------------------------------------------------------
from diff_diff import bacon_decompose

# Build the integer week grid from the panel's own weeks
weeks = sorted(df["week_start"].unique())
week_index = {w: i for i, w in enumerate(weeks)}

bd = df[["store", "week_start", "log_sales", "adoption_week"]].copy()
bd["period"] = bd["week_start"].map(week_index)

# 0 is the package's never-treated sentinel. Our adoption weeks all map to
# index >= 1 (earliest adoption is well after panel start), so there is no
# collision with a real cohort.
bd["first_treat"] = bd["adoption_week"].map(week_index).fillna(0).astype(int)

assert bd.loc[bd["first_treat"] != 0, "first_treat"].min() > 0, \
    "A real cohort collided with the never-treated sentinel"

res = bacon_decompose(
    data=bd,
    outcome="log_sales",
    unit="store",
    time="period",
    first_treat="first_treat",
)

res.print_summary()

# --- Validation ---------------------------------------------------
# The decomposition is only trustworthy if it reproduces the TWFE
# coefficient we estimated independently above.
print()
print(f"TWFE from statsmodels : {b:+.6f}")
print(f"TWFE from decomposition: {res.twfe_estimate:+.6f}")
print(f"Decomposition error    : {res.decomposition_error:.2e}")
print(f"Always-treated remapped: {res.n_always_treated_remapped}  (should be 0)")

# --- Weight breakdown ---------------------------------------------
print()
print("Weight by comparison type:")
for k, v in res.weight_by_type().items():
    print(f"  {k:24s} {v:7.2%}")

print()
print("Weighted average effect by comparison type:")
for k, v in res.effect_by_type().items():
    if v is not None:
        print(f"  {k:24s} {v:+.4f}  ({(np.exp(v)-1)*100:+.2f}%)")

