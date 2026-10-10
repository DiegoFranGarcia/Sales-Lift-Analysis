# Sales-Lift-Analysis

**Did a retail promotion program raise sales? A causal analysis that reaches a
significant answer, then takes it apart.**

Rossmann, a German drugstore chain, ran a continuing promotional program called
Promo2. 96 of its stores joined between 2013 and 2015, at fifteen different
points in time; 514 never joined. Difference-in-differences on 1,017,209 daily
observations gives a **+4.37% sales lift, p = 0.005**, with parallel trends
passing the standard test.

That estimate does not survive scrutiny, and establishing why is the point of
this project.

**[→ Read the interactive writeup](#)** · [Analysis plan](docs/analysis_plan.md) ·
[Deviations log](docs/deviations.md) · [Findings log](docs/findings.md)

---

## The finding

**Promo2 adoption is confounded with a pre-adoption sales decline. The apparent
lift cannot be separated from mean reversion.**

Stores did not join at random. They joined while they were sliding relative to
the rest of the chain, and the slide had bottomed out by the week they signed
up. Callaway–Sant'Anna measures each store's change from that week — the bottom
of the dip — so recovery that would have happened anyway is credited to the
program.

Four independent tests, each measuring the same thing a different way:

| Test | Result | What it means |
|---|---|---|
| Placebo adoption date | **−4.02%** on 93 of 96 stores | A date where nothing happened produces an effect as large as the real one |
| Honest DiD breakdown value | **0.034** | The result survives only if the post-treatment violation is under 3.4% of one already visible in the data. Applied work treats anything below 1 as fragile |
| Leave-one-cohort-out | **+4.37% → +1.71%** | Dropping one 31-store cohort takes the estimate below the detection threshold |
| Specification curve | **62 of 128** below detection | Nearly half the defensible analytic space yields an estimate this design could not have found |

The project's analysis plan listed five conditions, in advance, that would mean
the result could not be trusted. Two fired outright and a third is partly met.
The plan's pre-committed response was to conclude that the data cannot identify
the effect — and to treat that as a result rather than a failure.

---

## The part worth reading

**The standard pre-trends test passed.** Uniform confidence bands over the
twelve weeks before adoption: zero violations. By convention that clears the
design to proceed.

It was wrong. The drift sits further back than twelve weeks, and a pre-trends
test run on the conventional window has no view of it. What caught the problem
was a placebo adoption date — move each store's treatment 20 weeks earlier,
truncate the panel so the method only sees untreated weeks, and it reports a
−4.02% "effect."

A follow-up power calculation (Roth 2022) confirmed the test was not
underpowered. It had the power to detect a violation half this size. The window
was simply too narrow, and the conventional choice of window is what hid it.

---

## How the estimate was built

Five estimates, each correcting a flaw in the last:

| Estimator | Estimate | Problem it has |
|---|---|---|
| Cross-sectional | −8.06% | Adopters were ~12% smaller before adopting |
| Before/after | +1.67% | Absorbs all chain-wide time variation |
| Two-way fixed effects | +0.67% | Known to be biased under staggered adoption |
| **Callaway–Sant'Anna** | **+4.37%** | Baseline is the week before adoption — the bottom of the dip |

A Goodman-Bacon decomposition checked whether TWFE was actually contaminated
here: 94.6% of its weight sits on clean comparisons, so it was not. The 6.5×
gap between TWFE and Callaway–Sant'Anna traces entirely to the choice of
pre-treatment baseline, and the two reconcile to within 0.002 log points once
that is accounted for.

The detection threshold — 3.34% — was measured, not assumed. 500 fake
treatment assignments among never-adopters give the sampling distribution of
the estimator directly. A closed-form power calculation had put it at 1.19%,
understating it by a factor of three.

---

## What is in the repository, and why

```
docs/analysis_plan.md     Pre-registered. Committed before the first estimate.
docs/deviations.md        Append-only. Every departure from the plan, dated.
docs/findings.md          Every result, in plan order.
sql/                      Schema, panel build, sample construction, assertions.
src/                      Estimation, diagnostics, placebos.
api/ frontend/            The interactive writeup.
```

The analysis plan fixes the sample, the outcome, the estimator and the
robustness checks in advance, and lists what would make the result
untrustworthy. The git timestamp is what makes that claim checkable.

Three entries in the deviations log that are worth more than the estimate:

- **Sample restrictions left 99 treated stores against a pre-registered
  threshold of 100.** Relaxing the pre-period requirement from 26 to 20 weeks
  would have reached exactly 100 by adding a single store — about 0.5% off the
  standard error — and would have broken a placebo test that needs 26 weeks by
  construction. The threshold was held. The sensitivity analysis is logged.

- **A sample restriction was implemented incorrectly.** The rule said to drop
  stores with any gap of four or more consecutive weeks; the code detected gaps
  only as missing rows, and missed stores whose closures were recorded as
  present-but-closed. Fixing it cost three treated stores. A narrower fix would
  have cost one, but the distinction was only visible after seeing which stores
  it affected, so the literal reading was taken.

- **A power-analysis decision was reversed on later evidence.** An early
  conclusion that the sample was adequate rested on a formula that the
  simulation later showed understated variability threefold.

`sql/99_assertions.sql` encodes the sample definition as runnable checks, so a
change that silently alters the treated-store count fails loudly instead of
propagating.

---

## Stack

PostgreSQL for the panel build (1M daily rows → 82,300 store-weeks).
Python for estimation: `diff-diff` for Callaway–Sant'Anna, Goodman-Bacon,
Honest DiD and the placebo suite; `statsmodels` for the naive benchmarks and
TWFE. FastAPI serving precomputed results; React and Observable Plot for the
writeup.

```bash
./sql/run_all.sh          # raw CSVs to validated panel, with assertions
python src/build_headline.py
python -m uvicorn api.main:app --reload
cd frontend && npm run dev
```

Data: [Rossmann Store Sales](https://www.kaggle.com/competitions/rossmann-store-sales)
(Kaggle). Note that the Kaggle competition is a forecasting task; this is a
causal one, and the two are not comparable.

---

## What would settle the question

Knowing why Rossmann enrolled the stores it did. If enrolment was triggered by
a sales dip, the comparison group is wrong by construction and no estimator
fixes it. That is a question for the business, not the dataset.