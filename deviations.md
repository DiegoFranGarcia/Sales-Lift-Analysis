# Deviations Log

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

## 2026-09-14 — Exploratory work preceding the plan

Prior to writing this plan, `Promo` (the daily flag) was briefly explored as a
candidate treatment. It was rejected: all 1,115 stores show their first promo day on
2013-01-07, i.e. the flag is chain-synchronized with no cross-store variation in
timing, so no DiD design is possible on it. No outcome estimate was computed.
This is recorded for completeness, not as a deviation.