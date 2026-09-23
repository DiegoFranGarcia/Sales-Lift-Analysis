# Findings Log

Results produced in plan order. Records what was found, not what changed;
design changes go in `deviations.md`.

---

## 2026-09-17 — §8.2 Selection check (adopters vs. never-adopters, pre-period)

Treated stores are measured over pre-adoption weeks only; never-treated over the
full panel. Calendar spans therefore differ slightly between groups.

|          | Never-treated (520) | Adopters (99) |
|-----------------------------|-------|-------|
| Mean daily sales            | 7,335 | 6,441 |
| SD of mean daily sales      | 2,730 | 2,227 |
| Mean daily customers        | 845   | 733   |
| Mean transaction value      | 8.99  | 9.03  |
| Mean competition distance   | 6,349 | 3,887 |
| Median competition distance | 2,505 | 1,900 |

**Store type:**

|Type| Never-treated | Adopters |
|---|-----|----|
| a | 307 | 64 |
| b | 12  |  1 |
| c | 72  |  9 |
| d | 129 | 25 |

**Interpretation.** Selection is present and in the direction §8.2 anticipated.
Adopters were ~12% lower in daily sales and ~13% lower in daily customers before
adoption, while average transaction value was effectively identical (9.03 vs 8.99).
The baseline gap is therefore entirely footfall, not basket size. Adopters also sit
closer to competitors (median 1,900m vs 2,505m), consistent with competitive
pressure driving enrollment.

This is selection on **levels**, which DiD differences out via store fixed effects.
It does not by itself threaten identification. Selection on **trends** would, and is
untested until the §8.1 event study.

**Specific risk flagged:** if the chain enrolled underperforming stores, any
post-adoption improvement could be mean reversion rather than treatment effect. The
lower adopter baseline makes this more plausible, so the pre-period event-study
coefficients carry more weight than usual.

---

## 2026-09-19 — §10 Power analysis

Residual SD of log sales, pre-adoption store-weeks only, after absorbing store
and week fixed effects: **σ = 0.0889** (75,279 store-weeks).

|                  Quantity                  |  Value  |
|--------------------------------------------|---------|
| Treated stores                             |      99 |
| Never-treated stores                       |     520 |
| Mean weeks per store                       |   134.7 |
| Mean lag-1 residual autocorrelation (ρ)    |   0.195 |
| Effective independent weeks per store      |    4.97 |
| MDE, assuming independent weeks            |   0.24% |
| MDE, geometric-decay correlation (approx.) |   ~0.3% |
| **MDE, equicorrelation correction (conservative bound)** | **1.22%** |

α = 0.05, power = 0.80, two-sided.

**Method.** Serial correlation within stores means 135 weekly observations carry
far less than 135 observations' worth of information. The effective sample size
per store was computed as n / (1 + (n−1)ρ), which assumes **equicorrelation**:
every pair of weeks within a store correlated at ρ. Using the lag-1 autocorrelation
for all pairs, including weeks far apart, very likely overstates the true
correlation, so the resulting MDE is a conservative upper bound. Under independence
the MDE is 0.24%; under geometric decay it is ~0.3%. The true value lies within
0.24–1.22%.

**Interpretation.** Even at the conservative bound, the design has 80% power to
detect a true effect of roughly 1.2% on log sales. Plausible retail promotion
effects are substantially larger, so a null result would be informative rather than
inconclusive — the study could have detected an effect of the size the program would
need to justify itself.

**This supersedes the §2 underpowered framing.** The 30–99 band in §2 is a headcount
heuristic; the power analysis is direct evidence, and it shows 99 treated stores is
adequate given a 135-week panel and low residual variance. The effect estimate will
be reported as a primary result rather than downweighted, with the methods contrast
still reported alongside it per §7.

**Empirical check pending.** The §8.5 in-time placebo (fake adoption dates assigned
to never-adopters) will produce a distribution of estimates whose spread directly
measures the design's standard error without assuming any correlation structure.
That result will be compared against the 0.24–1.22% range above.