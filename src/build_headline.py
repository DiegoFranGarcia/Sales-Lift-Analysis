"""
Collect every headline number into outputs/headline.json.

The app must not hardcode estimates, and findings.md must not be the only place
they live. This script re-derives the ladder of estimates from the data and
writes them to one file that the API reads.

Everything here has already been computed elsewhere in the project; this is a
consolidation step, not new analysis. Values are cross-checked against
findings.md on write and any mismatch is reported.
"""
import json
import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from diff_diff import CallawaySantAnna
from dotenv import load_dotenv
from sqlalchemy import create_engine

if os.path.exists(".env"):
    load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
OUT = "outputs/headline.json"

# Values recorded in findings.md, used to verify this script reproduces the
# documented analysis rather than silently drifting from it.
EXPECTED = {
    "naive_cross_sectional": -0.0841,
    "naive_before_after": +0.0166,
    "twfe": +0.0067,
    "cs_att": +0.0428,
}

pct = lambda x: (np.exp(x) - 1) * 100


# =====================================================================
# Panel
# =====================================================================
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week,
           ever_treated, post_treatment
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

df["treated"] = df.ever_treated.astype(int)
df["post"] = df.post_treatment.fillna(False).astype(int)

weeks = sorted(df.week_start.unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df.week_start.map(wi)
df["first_treat"] = df.adoption_week.map(wi).fillna(0).astype(int)

n_treated = int(df.loc[df.ever_treated, "store"].nunique())
n_control = int(df.loc[~df.ever_treated, "store"].nunique())


def ols(formula, data, term):
    m = smf.ols(formula, data=data).fit(
        cov_type="cluster", cov_kwds={"groups": data["store"]})
    lo, hi = m.conf_int().loc[term]
    return dict(att=float(m.params[term]), se=float(m.bse[term]),
                ci_lo=float(lo), ci_hi=float(hi),
                p=float(m.pvalues[term]))


# =====================================================================
# The ladder of estimates
# =====================================================================
estimates = {}

# §1 naive cross-sectional
estimates["naive_cross_sectional"] = {
    **ols("log_sales ~ treated", df, "treated"),
    "label": "Naive: adopters vs never-adopters",
    "note": "No controls. Measures who joined, not what joining did.",
}

# §1 naive before/after
tr = df[df.ever_treated].copy()
estimates["naive_before_after"] = {
    **ols("log_sales ~ post", tr, "post"),
    "label": "Naive: adopters before vs after",
    "note": "Absorbs all calendar-time variation.",
}

# §7 TWFE
estimates["twfe"] = {
    **ols("log_sales ~ treat + C(store) + C(week_start)",
          df.assign(treat=df.post), "treat"),
    "label": "Two-way fixed effects",
    "note": "Baseline is the full pre-period average.",
}

# §7 Callaway-Sant'Anna
cs = CallawaySantAnna(
    control_group="never_treated", estimation_method="dr",
    base_period="universal", n_bootstrap=999,
    bootstrap_weights="mammen", seed=42,
).fit(df, outcome="log_sales", unit="store", time="period",
      first_treat="first_treat")
b = cs.bootstrap_results

estimates["cs_att"] = {
    "att": float(cs.overall_att), "se": float(b.overall_att_se),
    "ci_lo": float(b.overall_att_ci[0]), "ci_hi": float(b.overall_att_ci[1]),
    "p": float(b.overall_att_p_value),
    "label": "Callaway-Sant'Anna (primary estimator)",
    "note": "Baseline is the week before adoption.",
}

for k, v in estimates.items():
    v["pct"] = pct(v["att"])
    v["pct_lo"] = pct(v["ci_lo"])
    v["pct_hi"] = pct(v["ci_hi"])


# =====================================================================
# Diagnostics, read from the files that produced them
# =====================================================================
placebo = pd.read_csv("outputs/placebo_intime.csv")["att"]
spec = pd.read_csv("outputs/spec_curve.csv")
spec_ok = spec[(spec.note.fillna("") == "") & spec.att.notna()]
loo = pd.read_csv("outputs/loo_cohort.csv")

mde = float(2.8 * placebo.std())

diagnostics = {
    "mde_empirical": {
        "value": mde, "pct": mde * 100,
        "label": "Minimum detectable effect",
        "note": ("2.8 x the SD of 500 in-time placebo estimates. "
                 "Supersedes the §10 formula range of 0.23-1.19%."),
    },
    "placebo_intime": {
        "n": int(len(placebo)), "mean": float(placebo.mean()),
        "sd": float(placebo.std()),
        "pct_975": float(placebo.quantile(0.975)),
        "n_exceeding_real": int((placebo >= estimates["cs_att"]["att"]).sum()),
        "label": "In-time placebo on never-adopters",
        "note": "500 fake adoption assignments. Design does not manufacture effects.",
    },
    "placebo_date": {
        "att": -0.0321, "p": 0.001, "n_treated": 62,
        "att_20wk": -0.0411, "n_treated_20wk": 93,
        "real_att_same_62": 0.0101,
        "label": "Placebo adoption date",
        "note": "FAILS. Fake adoption 26 weeks early yields a large negative effect.",
    },
    "placebo_dose": {
        "label": "Placebo adoption date, by shift length",
        "note": ("Fake adoption N weeks before the real one, panel truncated "
                 "at real adoption. A null result is expected at every shift."),
        "rows": [
            {"shift": 13, "n_treated": 96, "att": +0.0098},
            {"shift": 20, "n_treated": 93, "att": -0.0411},
            {"shift": 26, "n_treated": 62, "att": -0.0321},
            {"shift": 39, "n_treated": 50, "att": -0.0534},
        ],
    },
    "honest_did": {
        "breakdown_rm": 0.0342, "breakdown_sd": 0.0049,
        "label": "Honest DiD breakdown value",
        "note": ("Smallest parallel-trends violation at which the CI includes "
                 "zero. Applied work treats values below 1 as fragile."),
    },
    "leave_one_out": {
        "worst_cohort": str(loo.loc[loo.delta.idxmin(), "adoption_week"]),
        "worst_cohort_n": int(loo.loc[loo.delta.idxmin(), "n_stores"]),
        "att_without": float(loo.att.min()),
        "att_without_pct": pct(loo.att.min()),
        "label": "Leave-one-cohort-out",
        "note": "Dropping the largest cohort takes the estimate below the MDE.",
    },
    "spec_curve": {
        "n": int(len(spec_ok)),
        "min": float(spec_ok.att.min()), "max": float(spec_ok.att.max()),
        "median": float(spec_ok.att.median()),
        "n_below_mde": int((spec_ok.att < mde).sum()),
        "n_negative": int((spec_ok.att < 0).sum()),
        "label": "Specification curve",
        "note": "128 defensible specifications.",
    },
}


# =====================================================================
# §12 status
# =====================================================================
conditions = [
    {"text": "Pre-trend coefficients trending in the direction of the estimate",
     "status": "FIRED",
     "evidence": "Treated stores converge downward toward controls pre-adoption."},
    {"text": "Placebo treatment date producing an effect of similar magnitude",
     "status": "FIRED",
     "evidence": "-4.02% on 93 of 96 stores against +4.37% real."},
    {"text": "Estimate flipping sign across reasonable specifications",
     "status": "PARTIAL",
     "evidence": f"No sign flip, but {diagnostics['spec_curve']['n_below_mde']} "
                 f"of {diagnostics['spec_curve']['n']} specifications fall below the MDE."},
    {"text": "Goodman-Bacon showing nearly all weight on already-treated comparisons",
     "status": "NOT FIRED", "evidence": "94.6% clean weight."},
    {"text": "Fewer than 30 in-window adopters",
     "status": "NOT FIRED", "evidence": f"{n_treated} treated stores."},
]


# =====================================================================
# Write
# =====================================================================
payload = {
    "sample": {"treated": n_treated, "control": n_control,
               "store_weeks": int(len(df)),
               "panel_start": str(min(weeks).date()),
               "panel_end": str(max(weeks).date()),
               "cohorts": int(df.loc[df.first_treat > 0, "first_treat"].nunique())},
    "estimates": estimates,
    "diagnostics": diagnostics,
    "distrust_conditions": conditions,
    "conclusion": (
        "Three §12 distrust conditions have fired. The estimate is not reported "
        "as a causal effect of Promo2: this data cannot separate the program's "
        "effect from mean reversion among stores that adopted during a decline."
    ),
}

os.makedirs("outputs", exist_ok=True)
with open(OUT, "w") as f:
    json.dump(payload, f, indent=2)

print(f"Wrote {OUT}\n")
print(f"Sample: {n_treated} treated, {n_control} control, "
      f"{len(df):,} store-weeks\n")

print(f"{'estimate':36s} {'att':>9} {'pct':>9}   check")
print("-" * 72)
for k, v in estimates.items():
    exp = EXPECTED.get(k)
    flag = "" if exp is None else (
        "ok" if abs(v["att"] - exp) < 0.0005
        else f"MISMATCH, findings.md says {exp:+.4f}")
    print(f"{v['label'][:36]:36s} {v['att']:>+9.4f} {v['pct']:>+8.2f}%   {flag}")

print(f"\nEmpirical MDE: {mde:.4f} ({mde*100:.2f}%)")
print(f"Spec curve: {diagnostics['spec_curve']['n_below_mde']} of "
      f"{diagnostics['spec_curve']['n']} below MDE")