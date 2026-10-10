"""
§8.5 In-time placebo on never-adopters.

Takes only the 514 never-treated stores, randomly assigns fake adoption dates
to 96 of them mirroring the real cohort structure exactly, and estimates the
ATT. Repeats many times.

Nothing happened to these stores. The distribution of estimates should centre
on zero. Two things it tells us:

  1. Whether the design manufactures effects from nothing. This matters more
     than usual here: the real treated group had a pre-adoption decline, and
     CS anchors on week g-1. If anchoring on g-1 systematically produces
     positive estimates whenever a group happens to dip, the real +4.37% is
     partly an artifact of the estimator rather than the treatment.

  2. An assumption-free standard error. The spread of this distribution IS the
     design's sampling variability, with no equicorrelation formula involved.
     Compare against the §10 MDE range of 0.23-1.19%.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine

N_ITER = 500
REAL_ATT = 0.0428

engine = create_engine("postgresql://diegogarcia@localhost:5432/rossmann")

df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week, ever_treated
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)

cohorts = (df.loc[df.ever_treated, ["store", "adoption_week"]]
             .drop_duplicates().groupby("adoption_week").size()
             .rename("n").reset_index())
cohorts["period"] = cohorts["adoption_week"].map(wi)

nt = df[~df.ever_treated].copy()
nt_stores = nt["store"].unique()
n_fake = int(cohorts.n.sum())

rng = np.random.default_rng(42)
ests = []

for it in range(N_ITER):
    chosen = rng.choice(nt_stores, size=n_fake, replace=False)
    assign, i = {}, 0
    for _, row in cohorts.iterrows():
        for s in chosen[i:i + row.n]:
            assign[s] = row.period
        i += int(row.n)

    d = nt.copy()
    d["first_treat"] = d["store"].map(assign).fillna(0).astype(int)

    try:
        r = CallawaySantAnna(control_group="never_treated",
                             estimation_method="dr",
                             base_period="universal").fit(
            d, outcome="log_sales", unit="store", time="period",
            first_treat="first_treat")
        ests.append(r.overall_att)
    except Exception:
        ests.append(np.nan)

    if (it + 1) % 100 == 0:
        print(f"  {it + 1}/{N_ITER}")

e = pd.Series(ests).dropna()
e.to_csv("outputs/placebo_intime.csv", index=False, header=["att"])

print()
print(f"Successful fits        : {len(e)}/{N_ITER}")
print(f"Mean placebo ATT       : {e.mean():+.4f}  ({(np.exp(e.mean())-1)*100:+.2f}%)")
print(f"Median                 : {e.median():+.4f}")
print(f"SD  (empirical SE)     : {e.std():.4f}")
print(f"2.5th / 97.5th pct     : {e.quantile(.025):+.4f} / {e.quantile(.975):+.4f}")
print()
print(f"Real ATT               : {REAL_ATT:+.4f}")
print(f"Placebo draws >= real  : {(e >= REAL_ATT).sum()}/{len(e)}  "
      f"= {(e >= REAL_ATT).mean():.3f}")
print()
print(f"Empirical MDE (2.8 x SE): {2.8 * e.std() * 100:.2f}%")
print(f"  §10 formula range     : 0.23% - 1.19%")
