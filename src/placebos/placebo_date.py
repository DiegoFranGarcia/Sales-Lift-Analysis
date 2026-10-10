"""
§8.3 Placebo treatment date.

Assign each treated store a fake adoption 26 weeks before its real one, and
truncate the panel at the real adoption date so that no genuinely treated week
is ever labelled post-treatment. Never-treated stores are kept whole as controls.

Nothing happened at the fake date. A non-null result would mean the design picks
up something other than the treatment - most plausibly a pre-adoption trend,
which is the §8.2 mean-reversion risk.

Sample attrition is expected and should be reported: stores adopting early in the
panel have too little room before their fake date to contribute, so the test runs
on later cohorts.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine

import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week, ever_treated
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)

SHIFT = 26
df["fake_week"] = df["adoption_week"] - pd.Timedelta(weeks=SHIFT)
df["fake_treat"] = df["fake_week"].map(wi).fillna(0).astype(int)

# Truncate: treated stores keep only weeks strictly before real adoption.
# Controls keep everything.
keep = (~df.ever_treated) | (df.week_start < df.adoption_week)
d = df[keep].copy()

# A treated store needs pre-periods relative to its FAKE date to contribute
pre_counts = (d[d.ever_treated]
              .assign(pre=lambda x: x.period < x.fake_treat)
              .groupby("store")["pre"].sum())
usable = set(pre_counts[pre_counts >= 8].index)

d.loc[d.ever_treated & ~d.store.isin(usable), "fake_treat"] = 0
d = d[(~d.ever_treated) | d.store.isin(usable)]

n_treated = d.loc[d.fake_treat > 0, "store"].nunique()
n_control = d.loc[d.fake_treat == 0, "store"].nunique()
print(f"Fake-treated stores : {n_treated}  (of 96)")
print(f"Control stores      : {n_control}")
print(f"Store-weeks         : {len(d):,}  (full panel 82,300)")
print(f"Fake cohorts        : {d.loc[d.fake_treat > 0, 'fake_treat'].nunique()}")

res = CallawaySantAnna(
    control_group="never_treated", estimation_method="dr",
    base_period="universal", n_bootstrap=999,
    bootstrap_weights="mammen", seed=42,
).fit(d, outcome="log_sales", unit="store", time="period", first_treat="fake_treat")

b = res.bootstrap_results
att = res.overall_att
print()
print(f"PLACEBO ATT  : {att:+.4f}  ({(np.exp(att)-1)*100:+.2f}%)")
print(f"Bootstrap SE : {b.overall_att_se:.4f}")
print(f"95% CI       : [{b.overall_att_ci[0]:+.4f}, {b.overall_att_ci[1]:+.4f}]"
      f"  = [{(np.exp(b.overall_att_ci[0])-1)*100:+.2f}%, "
      f"{(np.exp(b.overall_att_ci[1])-1)*100:+.2f}%]")
print(f"p-value      : {b.overall_att_p_value:.4f}")
print()
print(f"Real ATT for comparison: +0.0428  (+4.37%)")
