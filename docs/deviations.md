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