"""
Is the §8.4 placebo failure contaminating the primary outcome?

§8.4 found treated stores lose 0.027 open days per week after adoption
(p = 0.020). The §5 outcome is mean daily sales ON OPEN DAYS, so dropping
below-average days mechanically raises that mean with no change in real sales.

Weekly TOTAL sales is immune to that composition effect. It has the flaw §5
named - a holiday week looks like a decline - but that flaw is unrelated to
treatment timing, so it should not bias the ATT.

If the ATT survives on totals, composition is not driving it. If it collapses,
it is.
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
    SELECT w.store, w.week_start, w.open_days,
           w.mean_daily_sales, w.sales_open,
           s.adoption_week
    FROM store_week w
    JOIN store_sample_primary s USING (store)
    WHERE w.open_days > 0 AND w.mean_daily_sales > 0
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

df["log_mean_daily"] = np.log(df["mean_daily_sales"])
df["log_total"] = np.log(df["sales_open"])
df["log_open_days"] = np.log(df["open_days"])

# log(total) = log(mean per open day) + log(open days), exactly.
# So ATT(total) = ATT(mean) + ATT(log open days), and the three estimates
# below must satisfy that identity. Worth checking rather than assuming.
chk = (df["log_total"] - df["log_mean_daily"] - df["log_open_days"]).abs().max()
print(f"Identity check, max |log(total) - log(mean) - log(days)|: {chk:.2e}\n")

FIT = dict(unit="store", time="period", first_treat="first_treat")

results = {}
for outcome, label in [
    ("log_mean_daily", "log mean daily sales, open days  (§5 primary)"),
    ("log_total",      "log weekly TOTAL sales           (composition-immune)"),
    ("log_open_days",  "log open days per week           (the mechanism)"),
]:
    res = CallawaySantAnna(
        control_group="never_treated", estimation_method="dr",
        base_period="universal", n_bootstrap=199,
        bootstrap_weights="mammen", seed=42,
    ).fit(df, outcome=outcome, **FIT)

    b = res.bootstrap_results
    att = res.overall_att
    results[outcome] = att
    print(f"{label}")
    print(f"  ATT     : {att:+.4f}  ({(np.exp(att)-1)*100:+.2f}%)")
    print(f"  Boot SE : {b.overall_att_se:.4f}")
    print(f"  95% CI  : [{b.overall_att_ci[0]:+.4f}, {b.overall_att_ci[1]:+.4f}]")
    print(f"  p       : {b.overall_att_p_value:.4f}")
    print()

print("Decomposition:")
print(f"  ATT(total)               = {results['log_total']:+.4f}")
print(f"  ATT(mean per open day)   = {results['log_mean_daily']:+.4f}")
print(f"  ATT(open days)           = {results['log_open_days']:+.4f}")
print(f"  mean + days              = "
      f"{results['log_mean_daily'] + results['log_open_days']:+.4f}")