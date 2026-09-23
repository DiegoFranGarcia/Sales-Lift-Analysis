"""
§1 Naive benchmarks.

Two deliberately biased estimates, computed before any causal estimate so
that the contrast in §7 is fixed in advance.

  1. Cross-sectional: adopters vs never-adopters, all weeks pooled.
     Biased by selection - §8.2 showed adopters start ~12% lower.
  2. Before/after:     adopters after adoption vs the same stores before.
     Biased by anything else changing over calendar time.

Neither includes store or week fixed effects. That omission is the point.
Standard errors are clustered at the store level throughout.
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv()
    
engine = create_engine(os.getenv("DATABASE_URL"))

df = pd.read_sql("""
    SELECT store, week_start, log_sales, mean_daily_sales,
           ever_treated, post_treatment, event_time
    FROM panel_primary
""", engine, parse_dates=["week_start"])

df["treated"] = df["ever_treated"].astype(int)
df["post"] = df["post_treatment"].fillna(False).astype(int)


def report(name, model, term):
    b  = model.params[term]
    se = model.bse[term]
    lo, hi = model.conf_int().loc[term]
    print(f"\n{name}")
    print(f"  log-point estimate : {b:+.4f}  (SE {se:.4f})")
    print(f"  95% CI             : [{lo:+.4f}, {hi:+.4f}]")
    print(f"  approx. % effect   : {(np.exp(b)-1)*100:+.2f}%")
    print(f"  CI in %            : [{(np.exp(lo)-1)*100:+.2f}%, {(np.exp(hi)-1)*100:+.2f}%]")


# ---------------------------------------------------------------
# 1. Cross-sectional: adopters vs never-adopters
# ---------------------------------------------------------------
m1 = smf.ols("log_sales ~ treated", data=df).fit(
    cov_type="cluster", cov_kwds={"groups": df["store"]}
)
report("CROSS-SECTIONAL  (adopters vs never-adopters, all weeks)", m1, "treated")


# ---------------------------------------------------------------
# 2. Before/after: adopters only, post vs pre
# ---------------------------------------------------------------
treated_only = df[df["ever_treated"]].copy()
m2 = smf.ols("log_sales ~ post", data=treated_only).fit(
    cov_type="cluster", cov_kwds={"groups": treated_only["store"]}
)
report("BEFORE/AFTER     (adopters only, post vs pre adoption)", m2, "post")


# ---------------------------------------------------------------
# Context: what happened to never-treated stores over the same span?
# If controls also rose, the before/after number is partly calendar time.
# ---------------------------------------------------------------
print("\n" + "-" * 60)
print("Mean log sales by group and period:")
print(df.groupby(["ever_treated", "post"])["log_sales"].agg(["mean", "count"]))