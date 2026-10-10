"""
Last candidate for the CS/TWFE gap: unbalanced-panel handling.

The library warns on every fit that each ATT(g,t) uses within-cell panel
differencing on units observed at BOTH the base period and t, which it calls
"a valid but different estimand" from R's repeated-cross-section approach.
allow_unbalanced_panel=True switches to the R-compatible handling.

Also checks that the four specifications from cs_baseline_check.py were really
distinct runs - they agreed to four decimals, which is suspicious enough to
verify rather than assume.
"""
import numpy as np, pandas as pd
from diff_diff import CallawaySantAnna
from sqlalchemy import create_engine

engine = create_engine("postgresql://diegogarcia@localhost:5432/rossmann")
df = pd.read_sql("""
    SELECT store, week_start, log_sales, adoption_week
    FROM panel_primary
""", engine, parse_dates=["week_start", "adoption_week"])

weeks = sorted(df["week_start"].unique())
wi = {w: i + 1 for i, w in enumerate(weeks)}
df["period"] = df["week_start"].map(wi)
df["first_treat"] = df["adoption_week"].map(wi).fillna(0).astype(int)

FIT = dict(outcome="log_sales", unit="store", time="period", first_treat="first_treat")
pct = lambda x: (np.exp(x) - 1) * 100


def run(label, **kw):
    """Try allow_unbalanced_panel on the constructor; fall back to fit()."""
    try:
        r = CallawaySantAnna(control_group="never_treated", **kw).fit(df, **FIT)
    except TypeError:
        unb = kw.pop("allow_unbalanced_panel", None)
        r = CallawaySantAnna(control_group="never_treated", **kw).fit(
            df, allow_unbalanced_panel=unb, **FIT)
    print(f"{label:38s} {r.overall_att:>+9.4f} {pct(r.overall_att):>+8.2f}%")
    return r


print(f"{'specification':38s} {'log pt':>9} {'percent':>9}")
print("-" * 58)

r_base = run("universal, dr  (current)",
             base_period="universal", estimation_method="dr")

r_unb = run("universal, dr, allow_unbalanced",
            base_period="universal", estimation_method="dr",
            allow_unbalanced_panel=True)

r_vary = run("varying, dr",
             base_period="varying", estimation_method="dr")

print("-" * 58)
print(f"{'TWFE (reference)':38s} {0.0067:>+9.4f} {0.67:>+8.2f}%")

print("\nEvent-study comparison, universal vs varying base period:")
es_u = r_base.aggregate("event_study").to_dataframe().set_index("event_time")["att"]
es_v = r_vary.aggregate("event_study").to_dataframe().set_index("event_time")["att"]
diff = (es_u - es_v).dropna()
print(f"  horizons compared        : {len(diff)}")
print(f"  identical to 1e-10       : {(diff.abs() < 1e-10).all()}")
print(f"  largest absolute diff    : {diff.abs().max():.2e}")

print("\nEvent-study comparison, balanced vs allow_unbalanced:")
es_b = r_unb.aggregate("event_study").to_dataframe().set_index("event_time")["att"]
diff2 = (es_u - es_b).dropna()
print(f"  horizons compared        : {len(diff2)}")
print(f"  identical to 1e-10       : {(diff2.abs() < 1e-10).all()}")
print(f"  largest absolute diff    : {diff2.abs().max():.2e}")
