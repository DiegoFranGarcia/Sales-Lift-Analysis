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

> **Superseded by the §8.5 in-time placebo (2026-10-01).** That test measured the
> design's sampling variability directly — empirical SE 0.0119, implying an MDE of
> **3.34%**. The equicorrelation formula below understated it by roughly 3x, even
> at the conservative end of its stated range. The empirical figure is the one to
> report. This entry is retained as a record of the method and of its failure.

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
| MDE, equicorrelation (stated upper bound) | 1.19% |
| **MDE, measured empirically (§8.5)** | **3.34%** |

**Method.** Serial correlation means 135 weekly observations carry far less than
135 observations' worth of information. Effective sample size per store is
n / (1 + (n−1)ρ), which assumes **equicorrelation** — every pair of weeks within a
store correlated at ρ. Applying a lag-1 value to all pairs overstates correlation,
which was expected to make the resulting MDE a conservative upper bound.

**Why the formula failed.** It modelled serial correlation within stores and
nothing else. A staggered design carries further sources of sampling variability —
which stores land in which cohort, how cohort timing interacts with calendar time,
the behaviour of thin groups — none of which a within-store correlation parameter
captures. Simulation picks all of it up because it resamples the design itself.

This is worth stating plainly: closed-form power calculations for staggered DiD can
be badly optimistic, and the error here was in the direction of overstating the
design's sensitivity.

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

**Key result.** The point estimate (+0.67%) falls **well below the MDE of 3.34%**
measured in §8.5. Per §10 this is not evidence of no effect — it is an effect
smaller than this design can resolve. Reportable only because the power analysis
was run before the estimate.

*(An earlier version of this entry cited an MDE of 1.19% from the §10 formula.
That figure is superseded; the conclusion is unchanged and the margin is larger
than originally stated.)*

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

**Consequence for §7's narrative.** The planned framing ("TWFE is contaminated,
here is the credible estimate") is not supported. The finding is that TWFE was
tested for contamination and found largely clean. Callaway–Sant'Anna serves as
confirmation rather than correction.

---

## 2026-10-01 — §7 Callaway–Sant'Anna and §8.1 pre-trend assessment

**Overall ATT: +4.37%** (log point +0.0428).
Bootstrap SE 0.0155, 95% CI **[+1.21%, +7.35%]**, p = 0.005.
999 multiplier replications, Mammen weights, never-treated controls,
doubly-robust estimation, universal base period. Weekly cohorts
(deviations.md 2026-09-30).

| Specification | ATT |
|---|---|
| CS, never-treated controls | +4.37% |
| CS, not-yet-treated controls | +4.46% |
| TWFE | +0.67% |
| Naive before/after | +1.67% |
| Naive cross-sectional | −8.06% |

Control-group choice is immaterial for the overall ATT (+4.37% vs +4.46%).

**§8.1 pre-trends — uniform confidence bands.** Simultaneous bands from the
multiplier bootstrap, which correct for testing many horizons at once.

| Window | Mean coef | Pointwise CI excl. 0 | Uniform band excl. 0 | Cohorts |
|---|---|---|---|---|
| −12 to −1 | +0.0125 | 4/11 | 0/11 | 15 |
| −26 to −1 | +0.0213 | 11/25 | **2/25** | 14–15 |
| −52 to −1 | +0.0268 | 19/51 | 4/51 | 9–15 |

**Parallel trends fails over the fuller pre-period.** Two uniform-band violations
appear at −26 to −1, a window where 14–15 of 15 cohorts contribute, so thin
cohorts do not explain them.

The near window (−12 to −1) is clean, but that is substantive rather than
reassuring: §8.3 Check 3 shows the drift occurs roughly between −26 and −13 and
flattens before adoption, so a 13-week placebo shift yields +0.98% while a 20-week
shift yields −4.02%. Testing only −12 to −1 looks at the stretch where nothing is
happening.

Violations at −52 and beyond are less informative — the event_study `n` column
counts contributing cohorts, and horizons past about −60 rest on 1–9 of 15.

Pointwise intervals flag far more violations than uniform bands at every window.
That gap is the multiple-comparisons correction, not the data.

**§8's pre-commitment fires.** Pre-trend coefficients are jointly significant over
the pre-period, so the estimate is framed as suggestive rather than causal.

---

## 2026-10-01 — CS/TWFE divergence reconciled: baseline choice

The two estimators use different pre-treatment baselines.

CS anchors every post-treatment ATT(g,t) to week g−1, the week before adoption.
TWFE differences against the store's full pre-period. Treated stores sat above
controls across their pre-period, and that gap had closed by g−1, so the same
post-adoption level reads as a larger jump from the CS anchor than from the TWFE
baseline.

**Arithmetic check.** Event-study pre-period coefficients are exactly this
quantity: the treated-vs-control difference at horizon e, measured relative to
g−1. Weighted by treated store-weeks at each horizon — TWFE's implicit weighting —
they average **+0.0380**.

| | Log points |
|---|---|
| CS overall ATT (anchored at g−1) | +0.0428 |
| TWFE | +0.0067 |
| Gap to explain | **+0.0361** |
| Weighted pre-period baseline | **+0.0380** |
| CS − weighted baseline | +0.0048 |
| Residual vs TWFE | 0.0019 |

The residual is well inside one standard error of either estimate (CS bootstrap SE
0.0155; TWFE SE 0.0118). The gap is fully accounted for.

The unweighted pre-period mean is +0.0810, more than double the weighted figure,
because long-horizon coefficients are large and rest on few cohorts. Weighting by
treated store-weeks is the correct comparison and is the one that reconciles.

**Ruled out along the way,** each leaving the ATT essentially unchanged:

| Specification | ATT |
|---|---|
| Universal base period (default) | +0.0428 |
| Varying base period | +0.0428 |
| Outcome regression instead of DR | +0.0428 |
| IPW instead of DR | +0.0428 |
| `allow_unbalanced_panel=True` | +0.0426 |
| Not-yet-treated controls | +0.0437 |

Base period does not move the overall ATT because it governs only pre-treatment
coefficients; post-treatment ATT(g,t) uses g−1 by construction. Event studies did
differ across these runs (max horizon-level difference 0.232), confirming the
specifications were distinct rather than silently ignored.

**What this does not settle.** The mechanism is a pre-trend. Treated stores were
~3.8% above controls across the pre-period, converging to parity by g−1 — the
mean-reversion pattern §8.2 flagged. §8.1's uniform bands show no significant
violation in the near window, but the weighted full-pre-period figure is not
negligible.

The two estimates therefore answer slightly different questions about a group
whose relative position was already moving:

- **CS (+4.37%)** — change from the immediate pre-adoption week. Correct if g−1 is
  the best available counterfactual.
- **TWFE (+0.67%)** — change relative to the full pre-period. Correct if the longer
  history is the better counterfactual.

Neither is wrong. Which is more credible depends on whether the pre-adoption
decline is a real trend or noise concentrated in thin early cohorts.

Code: `src/diagnostics/cs_baseline_check.py`, `cs_unbalanced_check.py`,
`cs_twfe_reconcile.py`.

---

## 2026-10-02 — §8.5 In-time placebo on never-adopters

500 iterations. Each draw assigns fake adoption dates to 96 of the 514
never-treated stores, mirroring the real cohort structure exactly (3 stores at
period 27, 31 at period 31, and so on), then estimates the CS overall ATT. No
store in these runs received any treatment.

| Quantity | Value |
|---|---|
| Successful fits | 500/500 |
| Mean placebo ATT | **−0.0004** (−0.04%) |
| Median | +0.0003 |
| SD (empirical SE) | **0.0119** |
| 2.5th / 97.5th percentile | −0.0237 / +0.0227 |
| Draws ≥ real ATT (+0.0428) | **0 / 500** |

**The design does not manufacture effects.** The distribution centres on zero.
This directly addresses the concern raised by the CS/TWFE reconciliation: CS
anchoring on week g−1 does not systematically produce positive estimates on
groups whose relative position happens to decline.

**Empirical p < 0.002.** No random assignment of fake adoption dates reached the
real estimate; the 97.5th percentile is +2.27% against a real ATT of +4.37%. This
is the strongest evidence in the project so far, and it rests on no distributional
assumption — it is a count, not a formula.

**Empirical MDE: 3.34%** (2.8 × 0.0119). This supersedes §10's formula range of
0.23–1.19% for all purposes; see the revision note on that entry.

The CS bootstrap SE on the real estimate (0.0155) is close to the empirical
placebo SE (0.0119). Bootstrap and simulation agree; the formula-based power
analysis was the outlier.

**Consequences:**
- CS's +4.37% clears the corrected MDE of 3.34%, though less comfortably than it
  cleared 1.19%.
- TWFE's +0.67% falls well below it, reinforcing the §7 reading that the estimate
  is below what this design can resolve.

Raw draws saved to `outputs/placebo_intime.csv` for the writeup histogram.

---

## 2026-10-03 — §8.3 Placebo treatment date: FAILS

Each treated store assigned a fake adoption 26 weeks before its real one, with
the panel truncated at real adoption so no genuinely treated week is ever
labelled post-treatment. Never-treated stores kept whole as controls. Nothing
happened at the fake date; the estimate should be null.

**Placebo ATT: −3.16%** (log point −0.0321), bootstrap SE 0.0101,
95% CI [−5.13%, −1.22%], **p = 0.001**.

Sample attrition is substantial: only 62 of 96 treated stores have ≥8 periods
before their fake date, and the 34 lost are the earliest adopters — including
the 31-store cohort at 2013-07-29.

### Check 1 — is it the subsample?

| Estimate | Value |
|---|---|
| Real ATT, all 96 treated | +4.37% |
| Real ATT, the same 62 stores | **+1.01%** |
| Placebo ATT, those 62 stores | **−3.16%** |

**The headline rests on 34 stores.** Dropping them takes the real estimate from
+4.37% to +1.01%. On a like-for-like sample, the fake effect (−3.16%) is three
times larger in magnitude than the real one (+1.01%).

### Check 2 — is it a truncation artifact?

No. The post window is exactly event time 0 to 25 as designed, and the placebo's
own pre-period (−12 to −1) averages −0.0088, appropriately flat.

The post-period profile is diagnostic:

| Horizon | 0 | 1 | 4 | 6 | 7 | 9 |
|---|---|---|---|---|---|---|
| ATT | −0.001 | +0.015 | −0.027 | −0.045 | −0.025 | −0.034 |

It starts at zero and drifts downward. A treatment effect jumps at horizon 0; a
trend accumulates. This is a trend.

### Check 3 — dose-response across shift lengths

| Shift | Treated stores | Placebo ATT |
|---|---|---|
| 13 weeks | 96 | **+0.98%** |
| 20 weeks | **93** | **−4.02%** |
| 26 weeks | 62 | −3.16% |
| 39 weeks | 50 | −5.20% |

The 20-week shift retains 93 of 96 stores — effectively the full sample — and
produces −4.02%, against a real estimate of +4.37%. Subsample composition cannot
explain that. The relationship is not linear: the final 13 weeks show no drift,
but 20 weeks and beyond show a large one.

**Interpretation.** Treated stores were on a declining path relative to controls
before adoption, and the estimator reads the end of that decline as a treatment
effect. This is an Ashenfelter dip: units enter the program during a downturn,
recover naturally, and a design anchored near the trough credits the recovery to
the treatment.

Code: `src/placebo_date.py`, `src/placebo_date_checks.py`.

---

## 2026-10-04 — Honest DiD (Rambachan–Roth 2023) sensitivity

Event window restricted to −26..+26 (deviations.md, 2026-10-01). Fitted without
bootstrap: `diff-diff` issue #836 reports that `n_bootstrap > 0` clears
`event_study_vcov`, dropping cross-horizon covariance, with Δ^SD(0) covering 68%
at a nominal 95%.

ATT on the restricted window: +4.59% (vs +4.37% on the full window), so the
restriction does not itself change the estimate.

| Restriction | Breakdown M |
|---|---|
| Relative magnitude (ΔRM) | **0.034** |
| Smoothness (ΔSD) | **0.005** |

**The breakdown value is the smallest violation at which the robust confidence
interval includes zero.** Under ΔRM, M = 1 corresponds to a post-treatment
violation the same size as the largest one already visible in the pre-period.

At M = 0.034, the result survives only if the post-treatment violation is under
**3.4% of the largest pre-treatment violation in the data**. Applied work
typically treats breakdown values below 1 as fragile. This is roughly thirty
times below that.

The smoothness result is stronger still: the violation would have to be almost
perfectly linear.

Code: `src/honest_did.py`.

---

## 2026-10-04 — §12 assessment: three distrust conditions have fired

§12 listed, in advance, what would make the result untrustworthy. Current status:

| Condition | Status |
|---|---|
| Pre-trend coefficients trending in the direction of the estimate | **FIRED** — treated stores converge downward toward controls pre-adoption; estimate is positive |
| Placebo treatment date producing an effect of similar magnitude | **FIRED** — −4.02% on 93 stores against +4.37% real |
| Estimate flipping sign across reasonable specifications | **Partially** — +4.37% on 96 stores, +1.01% on the 62-store placebo sample; no sign flip yet, pending §11 |
| Goodman-Bacon showing nearly all weight on already-treated comparisons | Not fired — 94.6% clean weight |
| Fewer than 30 in-window adopters | Not fired — 96 |

Four independent lines of evidence point at one mechanism:

1. §8.2 — adopters ~12% smaller at baseline, mean-reversion risk flagged
2. CS/TWFE reconciliation — treated stores 3.8% above controls across the
   pre-period, converging to parity by week g−1
3. §8.3 placebo — −4.02% from a fake adoption date on 93 of 96 stores
4. Honest DiD — breakdown M = 0.034

These are not four problems. They are four measurements of the same one: a
pre-adoption decline that the estimator reads as a treatment effect.

**§12's pre-committed response:** "If several of these fire, the honest
conclusion is that this data cannot identify the effect."

**Conclusion adopted.** The CS estimate of +4.37% is not reported as a causal
effect of Promo2. It is reported alongside the diagnostics that undermine it.
See deviations.md, 2026-10-04, for the reporting decision.

**A methodological note worth carrying into the writeup.** The §8.1 pre-trend
test *passed* — uniform confidence bands, 0 of 11 violations in the near window —
and it was wrong. The standard pre-trends test had no power against the violation
that actually mattered here. Roth (2022) pre-trends power analysis is the direct
check on this and is run next.

---

## 2026-10-05 — Roth (2022) pre-trends power

**MDV = 0.0011** log points per period at 80% power (−26..+26 window, no
bootstrap, as for Honest DiD).

Run to check whether §8.1's near-window pass reflected a lack of power. It did
not. The placebo implies drift of roughly 0.002 per week (−4.02% over 20 weeks),
nearly double the MDV, so the test had ample power to detect it — and did, at the
−26 window.

The near window is clean because the drift stops around −13, not because the test
could not see it. Power and identification are separate questions, and here only
the second one fails.

Code: `src/pretrends_power.py`.

---

## 2026-10-05 — §8.4 Placebo outcome: FAILS, quantified at 0.50pp

Estimated the same design on outcomes Promo2 cannot plausibly affect.

| Outcome | ATT | Boot SE | 95% CI | p |
|---|---|---|---|---|
| Open days per week | **−0.027 days** | 0.0114 | [−0.047, −0.002] | **0.020** |
| Days observed per week | +0.0000 | — | — | — |

`days_observed` is a pure calendar constant (7 for every complete week). It
returned exactly zero with a NaN standard error — nothing to estimate, correctly
estimated as nothing. This validates the panel construction: nothing is leaking
through the pipeline.

Open days is a different matter. Treated stores lose 0.027 open days per week
after adoption, significant at p = 0.020. Promo2 cannot plausibly change a
store's opening schedule, so per §8.4 this indicates a data artifact.

### Why it contaminates the primary outcome

§5's outcome is mean daily sales **on open days**. If treated stores drop
below-average days after adoption, the per-open-day mean rises mechanically with
no change in real sales. Direction fits: fewer days, higher measured per-day
sales.

### Composition decomposition

`log(total) = log(mean per open day) + log(open days)` exactly, so the three ATTs
must sum. Identity verified to 1.67e-15.

| Outcome | ATT | 95% CI | p |
|---|---|---|---|
| Log mean daily sales, open days (§5 primary) | **+4.37%** | [+1.21%, +7.35%] | 0.005 |
| Log weekly total sales (composition-immune) | **+3.85%** | [+0.60%, +6.86%] | 0.030 |
| Log open days per week (the mechanism) | **−0.50%** | [−0.84%, −0.08%] | 0.005 |

---

## 2026-10-05 — §12 Leave-one-out: the estimate rests on one cohort

96 leave-one-store-out refits and 15 leave-one-cohort-out refits.

**Leave-one-cohort-out:**

| Cohort | Stores | ATT without it | Δ |
|---|---|---|---|
| **2013-07-29** | **31** | **+1.71%** | **−0.0258** |
| 2013-07-01 | 3 | +4.08% | −0.0028 |
| 2013-09-30 | 2 | +4.15% | −0.0021 |
| ...eleven cohorts with \|Δ\| < 0.005... | | | |
| 2013-09-02 | 9 | +4.87% | +0.0048 |
| **2014-03-03** | **29** | **+5.80%** | **+0.0135** |

**Dropping the 2013-07-29 cohort takes the ATT from +4.37% to +1.71% — below the
empirical MDE of 3.34%.** Without one cohort of 31 stores, the estimate falls
below what this design can detect.

**The two large cohorts disagree.** Removing 2013-07-29 (31 stores) lowers the
estimate; removing 2014-03-03 (29 stores) raises it to +5.80%, meaning that
cohort's own effect is well below average. The sample is not estimating one
common effect. The other thirteen cohorts move the aggregate by less than 0.005
each.

**What distinguishes the 2013-07-29 cohort:** mean competition distance 2,186m
against 4,648m for the other 65 treated stores — less than half. Store types span
all four (it holds the sample's only type-b store); assortment and promo-interval
distributions match the rest. It looks like a targeted rollout wave to
high-competition stores.

This is the §9 competition-proximity split arriving early, and makes that split
the most informative of the pre-specified heterogeneity checks.

**On §12's third condition.** "Estimate flipping sign across reasonable
specifications" does not fire as written — no sign flip. But a 2.5x swing from
dropping one cohort, landing below the detection threshold, is the substance the
condition points at. §11's specification curve settles it properly.

Code: `src/loo.py`. Outputs: `outputs/loo_store.csv`, `outputs/loo_cohort.csv`.

---

## 2026-10-05 — §9 Pre-specified heterogeneity

Four cross-sectional splits from §9. Dynamic effects by event time are covered by
the event study. Subgroup estimates restrict treated stores while retaining the
full 514-store never-treated control pool.

All estimates inherit the §12 identification failure. Reported as characterisation
of where the estimate concentrates, not as causal heterogeneity.

**By competition proximity** (median among treated = 1,845m):

| Group | Treated | ATT | SE | p |
|---|---|---|---|---|
| Closer than 1,845m | 48 | +4.94% | 0.0202 | 0.010 |
| Farther than 1,845m | 48 | +3.71% | 0.0173 | 0.050 |

**No meaningful difference.** A 1.2pp gap against SEs of ~0.02. This split was
expected to isolate the dominant 2013-07-29 cohort, which has mean competition
distance 2,186m against 4,648m for other treated stores. It does not: that cohort
splits 19/12 across the median. Its within-cohort median is 970m against 2,290m
for the others, so it is genuinely closer, but the sample median is the wrong cut
point to separate it. A pre-specified median split is a blunt instrument here.

**By StoreType:**

| Type | Treated | ATT | SE | p |
|---|---|---|---|---|
| a | 62 | **+2.47%** | 0.0181 | **0.211** |
| b | 1 | — | — | not estimable |
| c | 8 | +10.27% | 0.0460 | 0.005 |
| d | 25 | +7.22% | 0.0212 | 0.005 |

Type a holds nearly two-thirds of treated stores and shows **no significant
effect**, at +2.47% — below the 3.34% empirical MDE. Type c rests on 8 stores and
carries little weight. Type d, at 25 stores and +7.22%, is the substantive
contrast.

**By Assortment:**

| Level | Treated | ATT | SE | p |
|---|---|---|---|---|
| a | 52 | +4.14% | 0.0189 | 0.030 |
| b | 0 | — | — | not estimable |
| c | 44 | +4.64% | 0.0221 | 0.010 |

Identical within noise.

**By PromoInterval pattern:**

| Pattern | Treated | ATT | SE | p |
|---|---|---|---|---|
| Feb,May,Aug,Nov | 27 | +7.94% | 0.0205 | 0.005 |
| Jan,Apr,Jul,Oct | 40 | **+2.55%** | 0.0239 | **0.261** |
| Mar,Jun,Sept,Dec | 29 | +3.45% | 0.0220 | 0.121 |

Only one of three patterns is significant, and it is not the largest group.

### Reading across the splits

The full-sample +4.37% is **not a common effect present throughout**. It is absent
in the largest subgroup by store type (a, 62 stores, p = 0.21) and absent in the
largest by promo interval (Jan/Apr/Jul/Oct, 40 stores, p = 0.26), while being
large in smaller groups. Together with the leave-one-out result — the estimate
falls to +1.71% without one 31-store cohort — the estimate is concentrated in
pockets rather than broad-based.

**Multiple comparisons.** Eleven estimable cells across five pre-specified splits.
At α = 0.05 roughly one false positive is expected. §9 limited the splits in
advance for this reason, but the individual p-values are not corrected and should
not be read as independent confirmations.

Code: `src/heterogeneity.py`.

---

## 2026-10-04 — §11 Specification curve

128 specifications across six branches, each a choice that could plausibly have
been primary. Estimation method (dr/reg/ipw) excluded — all three returned
+0.0428 to four decimals. The row-gaps-only closure rule excluded as the
implementation bug corrected on 2026-09-29. `pre_min = 8` excluded as below
§8.1's requirement of 8 observed pre-periods.

All 128 fits clean, none flagged implausible.

### Distribution

| | ATT | % |
|---|---|---|
| Minimum | −0.0055 | −0.55% |
| 25th percentile | +0.0229 | +2.32% |
| **Median** | **+0.0352** | **+3.58%** |
| 75th percentile | +0.0419 | +4.28% |
| Maximum | +0.0606 | +6.24% |
| SD | 0.0156 | |

| | Count |
|---|---|
| Negative | 8 / 128 |
| **Below the empirical MDE of 3.34%** | **62 / 128** |
| Primary specification | +0.0428 |

**Just under half the defensible analytic space produces an estimate this design
cannot detect.** The eight negative specifications are all near zero, worst case
−0.55%. The primary specification sits at roughly the 75th percentile — on the
optimistic side of the range, though not an outlier.

**§12's third condition does not fire as written.** There is no sign flip across
reasonable specifications; 120 of 128 are positive and the negatives are
negligible in magnitude. But "62 of 128 fall below the detection threshold" is
the substantive version of the fragility that condition was pointing at.

### Which choice moves the answer

| Branch | Spread of means |
|---|---|
| **pre_min** | **0.0346** |
| gapped | 0.0062 |
| grain | 0.0061 |
| closure_rule | 0.0023 |
| control | 0.0015 |
| outcome | 0.0002 |

Five of six branches are essentially inert. The entire spread comes from the
§6.5 pre-period threshold.

| pre_min | Mean ATT | Range |
|---|---|---|
| 13 weeks | +0.0422 | [+0.0265, +0.0606] |
| 20 weeks | +0.0342 | [+0.0221, +0.0449] |
| 26 weeks | +0.0346 | [+0.0221, +0.0451] |
| **39 weeks** | **+0.0076** | **[−0.0055, +0.0278]** |

13, 20 and 26 cluster between +3.4% and +4.2%. **At 39 weeks the estimate
collapses to +0.76%.**

Requiring 39 weeks of pre-adoption history cuts the treated sample from ~96 to
53 and removes the earliest adopters — which is where the 2013-07-29 cohort
sits. This is the leave-one-out result arriving through a different route: the
same 31 stores, the same collapse.

**The fragility is about which stores are in the sample, not how the data are
modelled.** Grain, outcome definition, control group and closure rule barely
move the estimate; the pre-period requirement — the one branch that changes the
composition of the treated group — moves it by a factor of five.

### Other observations

The `outcome` branch has a spread of 0.0002, essentially zero, despite §8.4
finding composition contributes 0.50pp at the primary specification. That
contribution does not persist across the specification space.

Grain contributes 0.0061: quarterly +2.66%, weekly +3.27%. Once the quarterly
panel is constructed coherently, cohort granularity is nearly immaterial to the
aggregate.

Code: `src/spec_curve.py`. Output: `outputs/spec_curve.csv`.