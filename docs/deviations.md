# Deviations Log

Append-only. Entries are added in chronological order; earlier entries are never
edited, including when later work shows them to be wrong. Corrections appear as
new entries.

---

## 2026-09-14 — Exploratory work preceding the plan

Prior to writing this plan, `Promo` (the daily flag) was briefly explored as a
candidate treatment. It was rejected: all 1,115 stores show their first promo day on
2013-01-07, i.e. the flag is chain-synchronized with no cross-store variation in
timing, so no DiD design is possible on it. No outcome estimate was computed.
This is recorded for completeness, not as a deviation.

---

## 2026-09-14 — Feasibility gate (§2) run

**Counts (from `store.csv`, classified against panel window 2013-01-01 to 2015-07-31):**

| Group | Stores |
|---|---|
| Never-treated (`Promo2 = 0`) | 544 |
| Always-treated (adopted before 2013-01-01) | 346 |
| In-window adopters | 225 |
| Missing adoption date while `Promo2 = 1` | 0 |
| Adopted after panel end | 0 |

**Distinct (year, week) adoption points among all Promo2 participants:** 55
**In-window adoption date range:** 2013-01-07 to 2015-06-08

**Decision:** 225 in-window adopters, well above the ≥100 threshold, spread across
multiple year-quarter cohorts. **Gate passes. Proceeding with Promo2 as the primary
design.** No switch to competitor openings needed.

---

## 2026-09-14 — Adoption date recomputed under ISO week numbering

The gate counts (§2) were produced in pandas using `%W`, which is not ISO week
numbering. The SQL panel build uses `to_date(year || '-' || week, 'IYYY-IW')`,
per plan §4.

| Group | Gate (pandas `%W`) | SQL (ISO) |
|---|---|---|
| Never-treated | 544 | 544 |
| Always-treated | 346 | 359 |
| In-window | 225 | 212 |

Thirteen stores recorded as "2013, week 1" resolve to Monday 2012-12-31 under ISO,
one day before panel start, and are therefore always-treated rather than in-window.
The ISO figure is correct. 212 still clears the §2 threshold of 100, so the gate
decision is unchanged. These stores would have been dropped by §6.5 (≥26 weeks
pre-adoption) regardless.

---

## 2026-09-15 — §6 restrictions applied; treated sample falls to 99

| Step | Never-treated | In-window |
|---|---|---|
| After §6.1 (drop always-treated) | 544 | 212 |
| After §6.4 (drop refurbishment gap) | 520 | 147 |
| After §6.5 (≥26 pre-adoption weeks) | 520 | **99** |

§6.2 (missing adoption date while `Promo2 = 1`) is a no-op — no such stores exist.
§6.3 (zero-open-day store-weeks) is applied in the `panel_primary` view.

The §6.4 gap is a single uniform block, 2014-07-07 to 2014-12-22, identical across
all 180 affected stores — not the heterogeneous gaps §6.4 anticipated. The rule
applies as written.

**Gapped stores are strongly non-random by treatment status:** 30.7% of in-window
adopters (65/212) vs. 4.4% of never-treated (24/544). The drop is mechanical and
pre-committed, so identification is unaffected, but the estimand becomes the ATT
among non-refurbished stores — a population that differs systematically from the
full chain. Added to §13 limitations. The §6.4 robustness run is correspondingly
more important than a routine sensitivity check.

**Gate re-read:** 99 falls one store below the §2 threshold of 100, in the 30–99
band. Taking the conservative branch: proceeding with Promo2 as the primary design,
but the effect estimate is treated as underpowered and the methods contrast
(naive → TWFE → Goodman-Bacon → CS) is the headline rather than the ATT. §10's MDE
is the binding evidence on what this sample can detect.

**Cohort thinness:** the 99 treated stores are unevenly distributed — 2013Q3 (47)
and 2014Q1 (30) hold 77 of them; the remaining five cohorts hold 3–7 each. Per §7,
the CS multiplier bootstrap is therefore mandatory rather than optional.

---

## 2026-09-15 — Pre-period threshold (§6.5) sensitivity checked; unchanged

| Threshold | Treated stores |
|---|---|
| 8 weeks | 118 |
| 13 weeks | 109 |
| 20 weeks | 100 |
| 26 weeks (as planned) | 99 |
| 39 weeks | 54 |

Checked after §6 restrictions left 99 treated stores, one below the §2 threshold of
100. Relaxing to 20 weeks reaches exactly 100 by adding a single store — a ~0.5%
reduction in standard error. Relaxing to 13 weeks adds 10 stores, all adopting
between 2013-04-01 and 2013-06-03, for a ~5% reduction. Both would break §8.3's
placebo design, which requires 26 weeks of pre-period by construction.

**Decision: threshold held at 26 weeks.** The power gain does not justify weakening
the pre-trend evidence, and no change is warranted that would only have been
considered because it increased the sample.

---

## 2026-09-17 — §9 heterogeneity by StoreType: type b not estimable

The §8.2 selection check shows the primary sample contains only 1 treated store of
`StoreType = b` (against 12 never-treated). The §9 split by store type will
therefore be reported for types a, c and d only; type b is named as not estimable
rather than reported with a meaningless interval. No change to the other §9 splits.

---

## 2026-09-19 — §2 underpowered framing withdrawn on power-analysis evidence

The 2026-09-15 entry took the conservative §2 branch (30–99 adopters → treat the
estimate as underpowered, foreground the methods contrast). §10 now gives a
corrected MDE of ~1.2%, well below plausible promotion effects.

**Revised decision:** the ATT is reported as a primary result. The methods contrast
(naive → TWFE → Goodman-Bacon → CS) remains a headline finding per §7, but no longer
as a substitute for an effect estimate the design was assumed unable to support.

This reverses a prior decision on evidence that did not exist when it was made.
The §2 threshold is a headcount proxy for power; §10 measures power directly.

---

## 2026-09-22 — §1 Naive benchmarks

Computed before any causal estimate. Both specifications omit store and week
fixed effects deliberately. SEs clustered at store level.

| Benchmark | Estimate | 95% CI |
|---|---|---|
| Cross-sectional (adopters vs never-adopters) | **−8.34%** | [−14.09%, −2.21%] |
| Before/after (adopters, post vs pre) | **+2.45%** | [−2.28%, +7.41%] |

Group means of log sales:

| Group | Period | Mean | Store-weeks |
|---|---|---|---|
| Never-treated | — | 8.824 | 70,079 |
| Adopters | Pre | 8.723 | 5,200 |
| Adopters | Post | 8.747 | 8,125 |

**Interpretation.** The cross-sectional benchmark says Promo2 *reduces* sales by
8.3%, significant at conventional levels. This is almost certainly the wrong sign,
and §8.2 explains why: adopters were ~12% smaller before adopting. The estimate is
measuring selection into the program, not the program's effect.

The before/after benchmark gives +2.45% but with a CI spanning zero. It is
uncontaminated by selection (composition is held fixed) but absorbs all calendar-
time variation — chain-wide growth and seasonality are attributed to the program.

These are the reference points for the §7 contrast. The distance between −8.3% and
whatever the Callaway–Sant'Anna estimate turns out to be is the project's headline.