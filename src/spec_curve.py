"""
§11 Specification curve.

Re-estimates the ATT under every defensible combination of analytic choices.
With §12 invoked, the purpose is to show the range of answers the data supports,
not to demonstrate robustness.

-----------------------------------------------------------------------------
REWRITE NOTE (2026-10-04)

A first version produced estimates up to +55%, which is not a plausible retail
promotion effect. Cause: the quarterly-cohort branch remapped `first_treat` to
the start of the adoption quarter while leaving the panel at WEEKLY grain. A
store adopting 2014-03-03 was coded as treated from 2014-01-06, so eight
genuinely untreated weeks were labelled post-treatment. That is a coding error,
not a defensible specification - it is exactly the timing bias that motivated
choosing weekly cohorts in the first place (deviations.md 2026-09-30).

Two further faults in that version:
  - `pre_weeks` came from the database as CALENDAR weeks since panel start,
    computed off the real adoption week. It did not track the remapped
    treatment timing, and for gapped stores it overstated observed history by
    25 weeks.
  - No guard against degenerate cells, so implausible estimates were reported
    as successes.

This version fixes all three. Quarterly now means a genuinely quarterly panel:
the outcome is aggregated to store-quarters and treatment timing is defined on
the same grid.
-----------------------------------------------------------------------------

BRANCHES (128 = 2 x 2 x 2 x 4 x 2 x 2)

  grain         weekly | quarterly
  closure_rule  literal | refurb_only          (§6.4, deviations 2026-09-29)
  gapped        exclude | include              (§6.4 robustness run)
  pre_min       13 | 20 | 26 | 39              (§6.5, OBSERVED weeks)
  outcome       mean_daily | total             (§5; §8.4 composition)
  control       never_treated | not_yet_treated

EXCLUDED, with reasons
  row-gaps-only closure rule - the implementation bug corrected 2026-09-29.
  estimation method (dr/reg/ipw) - all three returned +0.0428 to four decimals
    (findings.md 2026-10-01). No variation; checked separately.
  pre_min = 8 - below §8.1's requirement of 8 observed pre-periods.

Padding the curve with indefensible specifications would widen it for free and
make the non-identification claim unearned.
"""
import itertools
import os

import numpy as np
import pandas as pd
from diff_diff import CallawaySantAnna
from dotenv import load_dotenv
from sqlalchemy import create_engine

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

# A full calendar quarter holds 13 weeks. Store-quarters with fewer observed
# weeks are dropped: a quarter with 4 observed weeks has roughly a third of
# normal turnover, which reads as a huge artificial dip. Affects both panel
# edges and the gapped stores' 2014 Q3/Q4.
MIN_WEEKS_PER_QUARTER = 10

# Any |ATT| above this is implausible for a retail promotion; flagged, not
# silently reported.
IMPLAUSIBLE = 0.25


# =====================================================================
# Load
# =====================================================================
wk = pd.read_sql("""
    SELECT w.store, w.week_start, w.open_days, w.sales_open,
           s.treat_group, s.adoption_week, s.is_gapped, s.has_long_closure
    FROM store_week w
    JOIN store_sample s USING (store)
    WHERE w.open_days > 0 AND w.sales_open > 0
""", engine, parse_dates=["week_start", "adoption_week"])

wk = wk[wk.treat_group.isin(["never_treated", "in_window"])].copy()

# Closure runs of >=4 consecutive zero-open weeks, with dates, so the
# refurbishment-window-only variant of §6.4 can be built.
closures = pd.read_sql("""
    WITH z AS (
        SELECT store, week_start,
               ROW_NUMBER() OVER (PARTITION BY store ORDER BY week_start) AS rn
        FROM store_week WHERE open_days = 0
    ),
    g AS (
        SELECT store, week_start,
               week_start - (rn * INTERVAL '7 day') AS island
        FROM z
    )
    SELECT store, MIN(week_start) AS run_start, MAX(week_start) AS run_end
    FROM g GROUP BY store, island HAVING COUNT(*) >= 4
""", engine, parse_dates=["run_start", "run_end"])

REFURB_START = pd.Timestamp("2014-07-07")
REFURB_END = pd.Timestamp("2014-12-22")
refurb_overlap = set(closures.loc[
    (closures.run_start <= REFURB_END) & (closures.run_end >= REFURB_START),
    "store"])
wk["closure_refurb"] = wk.store.isin(refurb_overlap)

print(f"Stores with a >=4wk closure run : {closures.store.nunique()}")
print(f"  overlapping refurb window     : {len(refurb_overlap)}")


# =====================================================================
# Pre-period length in OBSERVED weeks before adoption.
#
# Grain-independent, so `pre_min` means the same thing in both branches. This
# replaces the database's `pre_weeks`, which counted calendar weeks since
# panel start and so overstated history for gapped stores by 25 weeks.
# =====================================================================
pre_obs = (wk[wk.week_start < wk.adoption_week]
           .groupby("store").size().rename("pre_weeks_obs"))
wk["pre_weeks_obs"] = wk.store.map(pre_obs).fillna(0).astype(int)

print("\nObserved pre-adoption weeks among treated stores:")
t = wk[wk.treat_group == "in_window"][["store", "pre_weeks_obs"]].drop_duplicates()
for k in [13, 20, 26, 39]:
    print(f"  >= {k:2d} weeks : {(t.pre_weeks_obs >= k).sum():3d} stores")


# =====================================================================
# Panels
# =====================================================================
def weekly_panel(d):
    p = d[["store", "week_start", "open_days", "sales_open",
           "treat_group", "adoption_week"]].copy()
    p = p.rename(columns={"week_start": "t_date"})
    p["mean_daily"] = p.sales_open / p.open_days
    p["total"] = p.sales_open
    p["adopt_t"] = p.adoption_week
    return p


def quarterly_panel(d):
    """
    Store-quarter panel. Sales and open days are summed within the quarter, so
    `mean_daily` keeps its §5 definition (sales per open day) at a coarser
    grain and `total` is quarterly turnover. Partial quarters are dropped so
    an incomplete quarter is not read as a collapse in sales.
    """
    p = d.copy()
    p["q"] = p.week_start.dt.to_period("Q")
    g = (p.groupby(["store", "q"])
           .agg(open_days=("open_days", "sum"),
                sales_open=("sales_open", "sum"),
                weeks=("week_start", "size"),
                treat_group=("treat_group", "first"),
                adoption_week=("adoption_week", "first"))
           .reset_index())
    g = g[g.weeks >= MIN_WEEKS_PER_QUARTER].copy()
    g["t_date"] = g.q.dt.start_time
    g["mean_daily"] = g.sales_open / g.open_days
    g["total"] = g.sales_open
    # Coherent here because the time axis is also quarterly.
    g["adopt_t"] = g.adoption_week.dt.to_period("Q").dt.start_time
    return g


# =====================================================================
# One specification
# =====================================================================
def run_spec(grain, closure_rule, gapped, pre_min, outcome, control):
    d = wk
    d = d[~d.has_long_closure] if closure_rule == "literal" else d[~d.closure_refurb]
    if gapped == "exclude":
        d = d[~d.is_gapped]
    d = d[(d.treat_group == "never_treated") | (d.pre_weeks_obs >= pre_min)]

    p = weekly_panel(d) if grain == "weekly" else quarterly_panel(d)

    dates = sorted(p.t_date.unique())
    idx = {v: i + 1 for i, v in enumerate(dates)}
    p["period"] = p.t_date.map(idx)

    def first_period(a):
        if pd.isna(a):
            return 0
        later = [v for v in dates if v >= a]
        return idx[later[0]] if later else 0

    amap = p[["store", "adopt_t"]].drop_duplicates().set_index("store")["adopt_t"]
    p["first_treat"] = p.store.map(amap.map(first_period)).fillna(0).astype(int)
    p["y"] = np.log(p[outcome])

    n_tr = p.loc[p.first_treat > 0, "store"].nunique()
    n_ct = p.loc[p.first_treat == 0, "store"].nunique()
    out = dict(n_treated=n_tr, n_control=n_ct, n_periods=p.period.nunique(),
               n_obs=len(p), att=np.nan, note="")

    if n_tr < 10 or n_ct < 10:
        out["note"] = "too few units"
        return out

    try:
        r = CallawaySantAnna(control_group=control, estimation_method="dr",
                             base_period="universal").fit(
            p, outcome="y", unit="store", time="period",
            first_treat="first_treat")
        out["att"] = r.overall_att
        if abs(r.overall_att) > IMPLAUSIBLE:
            out["note"] = "IMPLAUSIBLE"
    except Exception as e:
        out["note"] = f"failed: {type(e).__name__}"
    return out


# =====================================================================
# Grid
# =====================================================================
BRANCHES = dict(
    grain=["weekly", "quarterly"],
    closure_rule=["literal", "refurb_only"],
    gapped=["exclude", "include"],
    pre_min=[13, 20, 26, 39],
    outcome=["mean_daily", "total"],
    control=["never_treated", "not_yet_treated"],
)
keys = list(BRANCHES)
combos = list(itertools.product(*(BRANCHES[k] for k in keys)))
print(f"\nSpecifications: {len(combos)}\n")

rows = []
for i, combo in enumerate(combos, 1):
    spec = dict(zip(keys, combo))
    res = run_spec(**spec)
    rows.append({**spec, **res,
                 "pct": (np.exp(res["att"]) - 1) * 100
                        if res["att"] == res["att"] else np.nan})
    if i % 32 == 0:
        print(f"  {i}/{len(combos)}")

sc = pd.DataFrame(rows)
sc.to_csv("outputs/spec_curve.csv", index=False)


# =====================================================================
# Report
# =====================================================================
bad = sc[sc.note != ""]
if len(bad):
    print(f"\n{len(bad)} specification(s) flagged:")
    print(bad[["grain", "gapped", "pre_min", "outcome", "n_treated",
               "n_periods", "att", "note"]].to_string(index=False))

ok = sc[(sc.note == "") & sc.att.notna()]
print(f"\nClean fits: {len(ok)}/{len(sc)}")

print("\n" + "=" * 64)
print("DISTRIBUTION OF ESTIMATES")
print("=" * 64)
for lbl, v in [("min", ok.att.min()), ("25th pct", ok.att.quantile(.25)),
               ("median", ok.att.median()), ("75th pct", ok.att.quantile(.75)),
               ("max", ok.att.max())]:
    print(f"  {lbl:10s} {v:+.4f}  ({(np.exp(v)-1)*100:+6.2f}%)")
print(f"  sd         {ok.att.std():.4f}")
print()
print(f"  negative              : {(ok.att < 0).sum()}/{len(ok)}")
print(f"  below MDE (0.0334)    : {(ok.att < 0.0334).sum()}/{len(ok)}")
print(f"  primary specification : +0.0428")

print("\n" + "=" * 64)
print("WHICH CHOICE MOVES THE ANSWER")
print("=" * 64)
contrib = [{"branch": k,
            "spread": ok.groupby(k)["att"].mean().max()
                      - ok.groupby(k)["att"].mean().min()}
           for k in keys]
for c in sorted(contrib, key=lambda x: -x["spread"]):
    print(f"  {c['branch']:14s} spread of means {c['spread']:.4f}")

print("\nMean and range by level:\n")
for k in keys:
    print(f"  {k}:")
    for lvl, g in ok.groupby(k):
        print(f"    {str(lvl):18s} n={len(g):3d}  mean {g.att.mean():+.4f}  "
              f"range [{g.att.min():+.4f}, {g.att.max():+.4f}]")
    print()