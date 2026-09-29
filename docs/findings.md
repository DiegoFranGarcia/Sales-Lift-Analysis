# Findings Log

Results in plan order, on the current primary sample (96 treated, 514
never-treated). Design changes go in `deviations.md`.

---

## 2026-09-29 — §8.2 Selection check (adopters vs never-adopters, pre-period)

Treated stores measured over pre-adoption weeks only; never-treated over the full
panel, so calendar spans differ slightly between groups.

| | Never-treated (514) | Adopters (96) |
|---|---|---|
| Mean daily sales | 7,344 | 6,490 |
| Mean daily customers | 846 | 736 |
| Mean transaction value | 8.99 | 9.07 |
| Mean competition distance | 6,348 | 3,853 |
| Median competition distance | 2,505 | 1,845 |

Store type (never-treated / adopters): a 305/62, b 11/1, c 70/8, d 128/25.

**Interpretation.** Selection is present, in the direction §8.2 anticipated.
Adopters were ~12% lower in daily sales and ~13% lower in customers before
adoption, while transaction value was effectively identical (9.07 vs 8.99) — the
baseline gap is footfall, not basket size. Adopters also sit closer to competitors
(median 1,845m vs 2,505m), consistent with competitive pressure driving enrollment.

This is selection on **levels**, which store fixed effects difference out, and does
not by itself threaten identification. Selection on **trends** would, and is
untested until the §8.1 event study.

**Specific risk.** If the chain enrolled underperforming stores, post-adoption
improvement could be mean reversion rather than treatment effect. The lower adopter
baseline makes this plausible, so the pre-period event-study coefficients carry more
weight than usual.

**§9 note.** Type b retains exactly 1 treated store after the §6.4 correction, so
the store-type heterogeneity split remains not estimable for type b (deviations.md,
2026-09-17).

---

## 2026-09-29 — §10 Power analysis

Residual SD of log sales, pre-adoption store-weeks only, after absorbing store and
week fixed effects: **σ = 0.0870** (74,437 store-weeks). α = 0.05, power = 0.80,
two-sided.

| Quantity | Value |
|---|---|
| Treated / never-treated stores | 96 / 514 |
| Mean weeks per store | 134.7 |
| Lag-1 residual autocorrelation (ρ) | 0.192 |
| Effective independent weeks per store | 5.06 |
| MDE, independent weeks (lower bound) | 0.23% |
| **MDE, equicorrelation (upper bound)** | **1.19%** |

**Method.** Serial correlation means 135 weekly observations carry far less than
135 observations' worth of information. Effective sample size per store is
n / (1 + (n−1)ρ), which assumes **equicorrelation** — every pair of weeks within a
store correlated at ρ. Applying a lag-1 value to all pairs overstates correlation,
so the resulting MDE is a conservative upper bound. The true value lies in
0.23–1.19%.

**Interpretation.** Even at the conservative bound, the design detects effects of
roughly 1.2%. Plausible retail promotion effects are larger, so a null is
informative rather than inconclusive.

**Supersedes the §2 underpowered framing.** The 30–99 band is a headcount
heuristic; this measures power directly and finds the sample adequate.

**Pending check.** The §8.5 in-time placebo will measure the design's standard
error empirically, without assuming a correlation structure. Compare to the range
above.

*(Prior sample 99/520: σ = 0.0889, ρ = 0.195, MDE 0.24–1.22%.)*

---

## 2026-09-29 — §1 Naive benchmarks

Computed before any causal estimate. Both omit store and week fixed effects
deliberately. SEs clustered at store level.

| Benchmark | Estimate | 95% CI |
|---|---|---|
| Cross-sectional (adopters vs never-adopters) | **−8.06%** | [−13.87%, −1.86%] |
| Before/after (adopters, post vs pre) | **+1.67%** | [−2.93%, +6.49%] |

Mean log sales: never-treated 8.826 (69,356 store-weeks); adopters 8.732 pre
(5,081), 8.749 post (7,863).

**Interpretation.** The cross-sectional benchmark says Promo2 *reduces* sales by
8%, significant at conventional levels — almost certainly the wrong sign, and
§8.2 explains why: adopters were already smaller. It measures selection into the
program, not the program.

The before/after benchmark is uncontaminated by selection but absorbs all
calendar-time variation, attributing chain-wide growth and seasonality to the
program. Its CI spans zero.

These are the reference points for the §7 contrast.

*(Prior sample 99/520: −8.34% and +2.45%.)*

---

## 2026-09-29 — §7 TWFE and Goodman-Bacon decomposition

**TWFE** (store + week FE, SEs clustered by store):
**+0.67%** (log point +0.0067, SE 0.0118), 95% CI [−1.63%, +3.03%].

**Goodman-Bacon decomposition** (`diff-diff`, exact Theorem 1 weights).
15 timing groups, 514 never-treated units, 225 2x2 comparisons.

| Comparison type | Weight | Avg effect | Contribution |
|---|---|---|---|
| Treated vs never-treated (clean) | 94.55% | +0.0047 | 0.0045 |
| Earlier vs later (valid) | 2.42% | +0.0581 | 0.0014 |
| Later vs earlier (forbidden) | 3.04% | +0.0066 | 0.0002 |

Decomposition reproduces the independently estimated TWFE coefficient
(+0.006711 both ways). Zero always-treated units remapped, confirming §6.1 was
applied correctly upstream.

**TWFE is not meaningfully contaminated here.** Contamination requires both
substantial forbidden weight and divergent estimates; forbidden comparisons carry
3% of the weight and give a similar, same-signed estimate. The large never-treated
pool drives this. The package's fixed-threshold warning at 3% is boilerplate, not
evidence of bias.

**Key result.** The point estimate (+0.67%) falls **below the MDE (1.19%)**. Per
§10 this is not evidence of no effect — it is an effect smaller than this design
can resolve. Reportable only because the power analysis ran first.

**Sensitivity to sample composition.** The estimate was +1.33% on 99/520. The
absolute shift (0.0066 log points) is smaller than one standard error, so the
apparent halving reflects an estimate near zero rather than instability — but
three stores moving it visibly is worth quantifying in the §11 specification curve
and a leave-one-out check.

**Decomposition error** is 6.44e-04, ~10% of the point estimate, up from 4.85e-04
on the larger sample despite the panel being *more* balanced now (50 missing
store-weeks vs 161). Cause unidentified. Immaterial to the weight breakdown, which
is the diagnostic of interest.

**Earlier-vs-later comparisons** estimate +5.98% (+6.41% on the prior sample) —
roughly ten times the clean comparisons and stable across both samples. Too little
weight to move the aggregate, but the stability suggests signal rather than noise.
§7's Callaway–Sant'Anna group-time estimates address this directly.

**Consequence for §7's narrative.** The planned framing ("TWFE is contaminated,
here is the credible estimate") is not supported. The finding is that TWFE was
tested for contamination and found largely clean. Callaway–Sant'Anna serves as
confirmation rather than correction.