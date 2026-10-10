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

## 2026-09-29 — §6.4 implementation gap: closures encoded as open_days = 0

§6.4 specifies dropping stores with any gap of ≥4 consecutive weeks. The
implementation detected gaps only as **missing rows** (`weeks_present = 110`).
Rossmann encodes some extended closures differently: rows present with `Open = 0`
every day. Those stores passed §6.4 and lost the affected weeks to §6.3 at the
week level instead of being excluded.

Found while investigating the unbalanced-panel warning from the Bacon
decomposition.

**Store 708 is the clear case:** 12 consecutive zero-open weeks from 2014-07-07 —
the exact first week of the refurbishment block that removed 180 stores under
§6.4 — at event time +10 to +21, inside its post-adoption period. A refurbishment
store the row-based test missed.

**Resolution.** §6.4 applied as written: any run of ≥4 consecutive weeks with no
open days excludes the store, however the closure is encoded. New flag
`has_long_closure`. The rule is unchanged; only its implementation is corrected.

| | Before | After |
|---|---|---|
| Treated | 99 | **96** |
| Never-treated | 520 | **514** |

Treated stores dropped: 708 (12 weeks, refurbishment window), 674 (5 weeks, event
time +81), 700 (4 weeks, event time −8).

**Considered and rejected:** restricting the fix to closures overlapping the
refurbishment window would drop only 708 (99 → 98). Better targeted, but it is a
distinction drawn after seeing which stores it affects. The literal application is
taken instead; the narrower variant is retained as a §11 specification-curve branch.

**Cost.** ~1.5% in standard error, immaterial against the §10 MDE. All prior
estimates were re-run on 96/514.

**Ambiguity noted.** §6.5 requires "≥26 weeks of pre-adoption data." `pre_weeks`
counts calendar weeks from panel start, but §6.3 drops zero-open weeks, so a
store's *observed* pre-period can be shorter — store 700 had 26 calendar, 22
observed. Moot here since 700 is dropped. Calendar weeks retained; the §8.1
assertion independently requires ≥8 observed pre-periods.

---

## 2026-09-30 — §4 cohort definition changed from quarterly to weekly for CS

§4 specifies cohorts as adoption year-quarter, "because weekly cohorts will be too
thin to estimate group-time effects." Callaway–Sant'Anna requires `first_treat` on
the same time grid as `time`, so with a weekly panel, quarterly cohorts mean coding
each store's adoption at the start of its quarter.

The primary sample has **15 distinct adoption weeks** across 96 treated stores —
fewer than §4 anticipated. Quarterly grouping yields 7 cohorts but dates the
2013Q3 cohort (45 stores) at 2013-07-01, while its members actually adopted between
2013-07-01 and 2013-09-30. Stores would be coded treated up to 13 weeks early,
labelling genuinely pre-treatment weeks as post-treatment and biasing the estimate
toward zero.

**Decision: weekly `first_treat`.** Timing error is a directional bias; thin
cohorts are a precision cost that size-weighted aggregation already handles. The
nine groups with ≤3 stores carry negligible weight in the overall ATT and will be
reported with their intervals rather than suppressed.

Quarterly cohorts are retained as a §11 specification-curve branch.

---

## 2026-09-30 — Weekly cohorts: per-cohort effects not reportable after all

The entry above stated that thin weekly cohorts "will be reported with their
intervals rather than suppressed." That is not possible. All 15 cohorts returned
non-finite multiplier-bootstrap standard errors; five contain a single store, and
the analytical influence-function SEs give t-statistics of 29 and 54 on those
cells, which are numerical artifacts rather than estimates.

**Revised:** the overall ATT is reported; cohort-level effects are named as not
estimable. §9 heterogeneity by `PromoInterval` and the other pre-specified splits
are unaffected, as those group stores by attribute rather than adoption week.

---

## 2026-10-01 — Honest DiD event window restricted to −26..+26

Rambachan–Roth sensitivity analysis requires an event-study surface. The full
surface spans −126 to +108. The relative-magnitude restriction benchmarks against
the largest pre-period first difference, and the largest movements in this surface
sit at horizons −126 to −100, which rest on 1–4 of 15 cohorts and are
predominantly noise. Including them would inflate the benchmark and make the
result appear robust for the wrong reason.

**Decision: restrict to −26..+26 for the Honest DiD fit only.** This covers the
window where §8.3 detected drift, retains all 96 treated stores and all 15
cohorts, and provides a year of post-treatment horizons. The ATT on this window
is +4.59% against +4.37% on the full window, so the restriction does not
materially change the estimand.

The primary CS estimate continues to use the full window.

---

## 2026-10-01 — Honest DiD fitted without bootstrap (upstream bug)

`diff-diff` issue #836: with `n_bootstrap > 0`, `CallawaySantAnna` clears
`event_study_vcov`, both at fit time and in the post-fit `aggregate("event_study")`
replay. Honest DiD then loses the cross-horizon covariance. In the reported
reproducer — parallel trends holding, effect path known — the Δ^SD(M = 0) interval
covered the truth 68% of the time at a nominal 95%.

The Honest DiD fit therefore uses `n_bootstrap=0` and analytical standard errors.
This does not affect the primary CS estimate, which continues to use 999
multiplier replications for its own inference.

Aggregation is requested at fit time rather than post-fit, since the sensitivity
analyses read the fit-time surface. This triggers a deprecation warning that is
unavoidable in the current version.

---

## 2026-10-02 — §8 placebo tests run out of listed order

§8 lists the in-time placebo on never-adopters as item 5. It was run first,
before §8.3 (placebo treatment date) and §8.4 (placebo outcome).

Reason: §8.5 is the test that could invalidate the others. If the design produced
sizeable effects on randomly assigned fake adoption dates, the remaining placebos
would be answering a question that no longer mattered. It also bore directly on
the concern raised by the CS/TWFE reconciliation — whether anchoring on week g−1
systematically generates positive estimates.

Sequencing only; no change to the content of any test. §8.4 and the §12
leave-one-out check remain outstanding.

---

## 2026-10-04 — §12 invoked: ATT withdrawn as a causal estimate

Three §12 distrust conditions have fired (findings.md, 2026-10-04). Per §12's
pre-committed instruction, the conclusion is that this data cannot cleanly
identify the effect of Promo2.

**Reporting decision:** the CS estimate of +4.37% is no longer presented as the
headline causal effect. It is reported together with the diagnostics that
undermine it — the §8.3 placebo, the Honest DiD breakdown value, and the
sample-composition result showing the estimate falls to +1.01% on 62 of 96 stores.

This supersedes the 2026-09-19 decision to report the ATT as a primary result.
That decision was made on power-analysis evidence; it is reversed on
identification evidence, which is the binding constraint.

Remaining plan steps are unaffected in content: §8.4, §9, §11 and the §12
leave-one-out still run, now as characterisation of a null rather than
robustness checks on a positive finding.

---

## 2026-10-06 — §11 specification curve rebuilt after a coding error

The first implementation remapped `first_treat` to the adoption quarter while
leaving the panel at weekly grain, coding stores as treated up to 12 weeks
early. It produced estimates up to +55%. Rebuilt with a genuinely quarterly
panel, partial quarters dropped, and `pre_min` measured in observed rather than
calendar weeks. Corrected curve spans −0.55% to +6.24%.

