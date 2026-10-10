# src/spec_curve_diag.py
import pandas as pd

sc = pd.read_csv("outputs/spec_curve.csv")

print("Ten largest estimates:")
print(sc.nlargest(10, "att").to_string(index=False))
print("\nFour negative estimates:")
print(sc[sc.att < 0].to_string(index=False))

print("\nQuarterly specs, sorted:")
q = sc[sc.cohort == "quarterly"].sort_values("att", ascending=False)
print(q[["closure_rule", "gapped", "pre_min", "outcome", "control",
         "n_treated", "n_control", "att"]].head(15).to_string(index=False))

print("\nTreated-store counts by branch combination:")
print(sc.groupby(["cohort", "gapped", "pre_min"])
        [["n_treated", "n_control", "att"]].agg(["min", "max"])
        .to_string())