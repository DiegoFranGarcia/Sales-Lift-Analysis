"""
§9 Pre-specified heterogeneity.

Five splits, fixed in the plan before any estimation, to limit multiple
comparisons. Two caveats carried in:

  - StoreType b has exactly 1 treated store and is not estimable
    (deviations.md, 2026-09-17).
  - Competition proximity is the split leave-one-out pointed at: the dominant
    2013-07-29 cohort sits at 2,186m mean competition distance against 4,648m
    for the other 65 treated stores.

Dynamic effects by event time are handled by the event study already produced;
this script covers the four cross-sectional splits.

All estimates inherit the §12 identification failure. Reported as
characterisation of where the (unidentified) estimate is concentrated, not as
causal heterogeneity.
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
    SELECT store, week_start, log_sales, adoption_week,
           store_type, assortment, competition_distance, promo_interval
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

# Median competition distance over treated stores only, so the split is about
# the treated population rather than being dragged by the larger control pool.
med = (df.loc[df.first_treat > 0, ["store", "competition_distance"]]
         .drop_duplicates()["competition_distance"].median())
print(f"Median competition distance among treated stores: {med:.0f}m\n")
df["comp_near"] = df["competition_distance"] < med

FIT = dict(outcome="log_sales", unit="store", time="period",
           first_treat="first_treat")


def run(data, label, n_boot=199):
    """Estimate on a subgroup. Controls are always the full never-treated pool."""
    n = data.loc[data.first_treat > 0, "store"].nunique()
    if n < 5:
        print(f"{label:38s} {n:>3} treated   NOT ESTIMABLE")
        return
    res = CallawaySantAnna(
        control_group="never_treated", estimation_method="dr",
        base_period="universal", n_bootstrap=n_boot,
        bootstrap_weights="mammen", seed=42,
    ).fit(data, **FIT)
    b = res.bootstrap_results
    a = res.overall_att
    se = b.overall_att_se
    p = b.overall_att_p_value
    se_s = f"{se:.4f}" if se == se else "  nan "
    p_s = f"{p:.3f}" if p == p else " nan "
    print(f"{label:38s} {n:>3} treated   {a:+.4f}  "
          f"({(np.exp(a)-1)*100:+6.2f}%)   SE {se_s}   p {p_s}")


def subgroup(mask):
    """Keep never-treated stores whole; restrict treated to the subgroup."""
    d = df.copy()
    d.loc[(d.first_treat > 0) & ~mask, "first_treat"] = -1
    return d[d.first_treat >= 0]


print("=" * 86)
run(df, "FULL SAMPLE")
print("=" * 86)

print("\nBy competition proximity (§9):")
run(subgroup(df.comp_near),  f"  closer than {med:.0f}m")
run(subgroup(~df.comp_near), f"  farther than {med:.0f}m")

print("\nBy StoreType (§9):")
for t in sorted(df.store_type.dropna().unique()):
    run(subgroup(df.store_type == t), f"  type {t}")

print("\nBy Assortment (§9):")
for a in sorted(df.assortment.dropna().unique()):
    run(subgroup(df.assortment == a), f"  assortment {a}")

print("\nBy PromoInterval pattern (§9):")
for pi in sorted(df.promo_interval.dropna().unique()):
    if pi:
        run(subgroup(df.promo_interval == pi), f"  {pi}")