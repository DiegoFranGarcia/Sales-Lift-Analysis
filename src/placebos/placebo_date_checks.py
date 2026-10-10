"""
Three checks on the §8.3 placebo result (-3.16%, p = 0.001).

The placebo fired, triggering a §12 condition. Before accepting it as evidence
of a pre-adoption dip, rule out three alternative explanations:

  1. SAMPLE COMPOSITION. The placebo ran on 62 of 96 stores, and the 34 lost are
     all early adopters. Comparing a 62-store placebo against a 96-store real
     estimate is not like for like. Re-estimate the real ATT on exactly those 62.

  2. TRUNCATION ARTIFACT. 748 group-time cells were non-estimable because treated
     stores were truncated at real adoption. Confirm the aggregation rests on the
     intended ~26 post-periods per cohort rather than something degenerate.

  3. DOSE-RESPONSE. If the placebo is picking up a roughly linear pre-trend, a
     13-week shift should give roughly half the effect of a 26-week shift. If
     13 weeks gives the same -3%, the story is not a smooth trend.
"""
import numpy as np
import pandas as pd
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
df["real_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

pct = lambda x: (np.exp(x) - 1) * 100

FIT = dict(outcome="log_sales", unit="store", time="period")


def fit_cs(data, treat_col, boot=0):
    kw = dict(control_group="never_treated", estimation_method="dr",
              base_period="universal")
    if boot:
        kw.update(n_bootstrap=boot, bootstrap_weights="mammen", seed=42)
    return CallawaySantAnna(**kw).fit(data, first_treat=treat_col, **FIT)


def build_placebo(shift_weeks):
    """Fake adoption `shift_weeks` early, panel truncated at real adoption."""
    d = df.copy()
    d["fake_week"] = d["adoption_week"] - pd.Timedelta(weeks=shift_weeks)
    d["fake_treat"] = d["fake_week"].map(wi).fillna(0).astype(int)

    # Treated stores keep only weeks strictly before REAL adoption.
    keep = (~d.ever_treated) | (d.week_start < d.adoption_week)
    d = d[keep].copy()

    # Need >= 8 periods before the FAKE date to contribute
    pre = (d[d.ever_treated]
           .assign(p=lambda x: x.period < x.fake_treat)
           .groupby("store")["p"].sum())
    usable = set(pre[pre >= 8].index)

    d.loc[d.ever_treated & ~d.store.isin(usable), "fake_treat"] = 0
    d = d[(~d.ever_treated) | d.store.isin(usable)]
    return d, usable


# =====================================================================
# CHECK 1 - sample composition
# =====================================================================
print("=" * 66)
print("CHECK 1 - is the placebo result driven by the 62-store subsample?")
print("=" * 66)

d26, usable62 = build_placebo(26)
print(f"\nStores usable in the 26-week placebo: {len(usable62)} of 96")

# Real CS on the full 96
r_full = fit_cs(df, "real_treat")

# Real CS restricted to exactly the 62 placebo-usable treated stores
sub = df[(~df.ever_treated) | df.store.isin(usable62)].copy()
r_sub = fit_cs(sub, "real_treat")

print(f"\nReal ATT, all 96 treated      : {r_full.overall_att:+.4f}  "
      f"({pct(r_full.overall_att):+.2f}%)")
print(f"Real ATT, the same 62 stores  : {r_sub.overall_att:+.4f}  "
      f"({pct(r_sub.overall_att):+.2f}%)")
print(f"Placebo ATT, those 62 stores  : {-0.0321:+.4f}  ({-3.16:+.2f}%)")
print("\nThe like-for-like comparison is the second line against the third.")


# =====================================================================
# CHECK 2 - truncation artifact
# =====================================================================
print("\n" + "=" * 66)
print("CHECK 2 - is the aggregation resting on sensible cells?")
print("=" * 66)

es26 = fit_cs(d26, "fake_treat").aggregate("event_study").to_dataframe()
post = es26[(es26.event_time >= 0) & es26.att.notna()]

print(f"\nEstimable post-period horizons : {len(post)}")
print(f"Event-time range, post         : {int(post.event_time.min())} to "
      f"{int(post.event_time.max())}")
print(f"Expected by construction       : 0 to 25 (26-week fake post window)")
print(f"\nMean ATT over post horizons    : {post.att.mean():+.4f}")
print(f"ATT at horizon 0               : "
      f"{post.loc[post.event_time == 0, 'att'].iloc[0]:+.4f}"
      if (post.event_time == 0).any() else "")

print("\nPost-period profile (first 10 horizons):")
print(post[["event_time", "att", "se", "n"]].head(10).to_string(index=False))

pre26 = es26[(es26.event_time < 0) & es26.att.notna() & (~es26.is_reference)]
near = pre26[pre26.event_time >= -12]
print(f"\nPlacebo's own pre-period, -12 to -1: mean {near.att.mean():+.4f}, "
      f"{len(near)} horizons")
print("  (should be near zero - this is the window before the FAKE date)")


# =====================================================================
# CHECK 3 - dose-response
# =====================================================================
print("\n" + "=" * 66)
print("CHECK 3 - does a shorter shift give a proportionally smaller effect?")
print("=" * 66)

print(f"\n{'shift':>8} {'stores':>8} {'ATT':>10} {'percent':>10}")
print("-" * 40)
for shift in [13, 20, 26, 39]:
    d, us = build_placebo(shift)
    if len(us) < 10:
        print(f"{shift:>6}wk {len(us):>8}   too few stores")
        continue
    r = fit_cs(d, "fake_treat")
    print(f"{shift:>6}wk {len(us):>8} {r.overall_att:>+10.4f} "
          f"{pct(r.overall_att):>+9.2f}%")

print("\nA roughly linear pre-trend implies the effect scales with the shift.")
print("A flat profile across shifts implies something else is going on.")