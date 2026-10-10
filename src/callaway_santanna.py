"""
§7 Callaway-Sant'Anna (2021) - the plan's primary estimator.

Estimates ATT(g,t) for each adoption week against never-treated stores only,
then aggregates. Weekly cohorts, not quarterly (deviations.md 2026-09-30).

Bootstrap inference because five cohorts hold a single store and analytical
influence-function SEs are unreliable there.
"""
import numpy as np
import pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy import create_engine
import os

N_BOOTSTRAP = 199

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))


df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

# Integer period grid starting at 1, leaving 0 free as the never-treated
# sentinel. Both columns map onto the same grid.
weeks = sorted(df["week_start"].unique())
week_index = {w: i + 1 for i, w in enumerate(weeks)}

df["period"] = df["week_start"].map(week_index)
df["first_treat"] = df["adoption_week"].map(week_index).fillna(0).astype(int)

FIT = dict(outcome="log_sales", unit="store", time="period", first_treat="first_treat")


def pct(x):
    """Log point to approximate percentage effect."""
    return (np.exp(x) - 1) * 100


# ---------------------------------------------------------------------
# Primary fit: never-treated controls
# ---------------------------------------------------------------------
cs = CallawaySantAnna(
    control_group="never_treated",
    estimation_method="dr",
    base_period="universal",
)
res = cs.fit(df, **FIT)

print(f"ATT, never-treated controls : {res.overall_att:+.4f}  ({pct(res.overall_att):+.2f}%)")


# ---------------------------------------------------------------------
# Not-yet-treated controls, as a comparison
# ---------------------------------------------------------------------
res_nyt = CallawaySantAnna(
    control_group="not_yet_treated",
    estimation_method="dr",
    base_period="universal",
).fit(df, **FIT)

print(f"ATT, not-yet-treated        : {res_nyt.overall_att:+.4f}  ({pct(res_nyt.overall_att):+.2f}%)")
print(f"TWFE, for reference         : +0.0067  (+0.67%)")


# ---------------------------------------------------------------------
# Bootstrap inference on the overall ATT
#
# Per-cohort bootstrap SEs come back non-finite for all 15 cohorts - those
# cells are too thin to resample. The overall ATT is still usable.
# ---------------------------------------------------------------------
res_boot = CallawaySantAnna(
    control_group="never_treated",
    estimation_method="dr",
    base_period="universal",
    n_bootstrap=N_BOOTSTRAP,
    bootstrap_weights="mammen",
    seed=42,
).fit(df, **FIT)

b = res_boot.bootstrap_results
print()
print(f"Bootstrap SE  : {b.overall_att_se:.4f}")
print(f"Bootstrap CI  : [{b.overall_att_ci[0]:+.4f}, {b.overall_att_ci[1]:+.4f}]"
      f"  = [{pct(b.overall_att_ci[0]):+.2f}%, {pct(b.overall_att_ci[1]):+.2f}%]")
print(f"Bootstrap p   : {b.overall_att_p_value:.4f}")


# ---------------------------------------------------------------------
# Write the aggregate tables and show their columns
# ---------------------------------------------------------------------
for name in ["simple", "event_study", "group"]:
    tbl = res.aggregate(name).to_dataframe()
    tbl.to_csv(f"outputs/cs_{name}.csv", index=False)
    print(f"\n--- {name} ---")
    print("columns:", list(tbl.columns))
    print(tbl.head(8).to_string(index=False))