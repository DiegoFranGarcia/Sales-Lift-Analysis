"""
§12 Leave-one-out robustness.

The §8.3 Check 1 result showed the ATT falling from +4.37% to +1.01% when 34
treated stores drop out. That suggests the estimate is concentrated rather than
broad-based. This quantifies it two ways:

  1. Leave-one-store-out, 96 refits. Shows whether any single store moves the
     aggregate materially.
  2. Leave-one-cohort-out, 15 refits. More informative here, since adoption
     weeks are the natural grouping and two cohorts hold 60 of 96 stores.

A broad-based effect barely moves when one unit leaves. A concentrated one
collapses when the right one does.
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
    SELECT store, week_start, log_sales, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
inv = {v: k for k, v in wi.items()}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

FIT = dict(outcome="log_sales", unit="store", time="period",
           first_treat="first_treat")


def att(data):
    return CallawaySantAnna(
        control_group="never_treated", estimation_method="dr",
        base_period="universal",
    ).fit(data, **FIT).overall_att


full = att(df)
print(f"Full-sample ATT: {full:+.4f}  ({(np.exp(full)-1)*100:+.2f}%)\n")

treated = sorted(df.loc[df.first_treat > 0, "store"].unique())

# ---------------------------------------------------------------
# 1. Leave one store out
# ---------------------------------------------------------------
rows = []
for s in treated:
    rows.append({"store": s, "att": att(df[df.store != s])})
loo = pd.DataFrame(rows)
loo["delta"] = loo["att"] - full
loo.to_csv("outputs/loo_store.csv", index=False)

print("LEAVE-ONE-STORE-OUT (96 refits)")
print(f"  range        : {loo.att.min():+.4f} to {loo.att.max():+.4f}")
print(f"  sd of ATT    : {loo.att.std():.4f}")
print(f"  largest |Δ|  : {loo.delta.abs().max():.4f}")
print("\n  Most influential stores:")
print(loo.reindex(loo.delta.abs().sort_values(ascending=False).index)
         .head(5).to_string(index=False))

# ---------------------------------------------------------------
# 2. Leave one cohort out
# ---------------------------------------------------------------
sizes = (df.loc[df.first_treat > 0, ["store", "first_treat"]]
           .drop_duplicates().groupby("first_treat").size())

rows = []
for g, n in sizes.items():
    drop = df.loc[df.first_treat == g, "store"].unique()
    rows.append({
        "cohort_period": g,
        "adoption_week": inv[g].date(),
        "n_stores": n,
        "att": att(df[~df.store.isin(drop)]),
    })
loc_ = pd.DataFrame(rows)
loc_["delta"] = loc_["att"] - full
loc_["pct"] = (np.exp(loc_["att"]) - 1) * 100
loc_.to_csv("outputs/loo_cohort.csv", index=False)

print("\n\nLEAVE-ONE-COHORT-OUT (15 refits)")
print(loc_.sort_values("delta").to_string(index=False))