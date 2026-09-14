# Analysis Plan — Sales Lift from Promo2 Adoption

**Author:** Diego Garcia
**Written:** 9-14-2026
**Status:** Pre-registered. Committed before any treatment-effect estimate was computed.

---

## 0. Purpose of this document

This plan is written *before* looking at outcomes. It fixes the sample, the outcome
variable, the estimator, and the robustness checks in advance so that the final
estimate is not the product of specification search.

Any deviation from this plan is allowed, but must be logged in
`deviations.md` with the date, the change, and the reason. Deviations discovered
to be necessary are normal; undocumented ones are what make results untrustworthy.

---

## 1. Research question

**Does adopting Promo2 — Rossmann's continuing, multi-month promotional program —
increase store-level sales, and by how much?**

Secondary question, and arguably the more interesting one:
**How much does a naive estimate overstate or understate that effect, and why?**

The naive benchmarks I will compute and report alongside the causal estimate:

- **Cross-sectional:** mean sales of Promo2 stores vs. non-Promo2 stores.
- **Before/after:** mean sales of adopting stores after adoption vs. before.

Both are almost certainly biased. Quantifying *how* biased is the headline result.

---

## 2. Feasibility gate (run this first)

The design depends on there being enough stores that adopt Promo2 *during* the
panel window. Stores with `Promo2SinceYear` before 2013 are already treated at the
first observation and cannot contribute a pre-period.

**Run before anything else:**

1. Count stores with `Promo2 = 1` and adoption date within 2013-01-01 to 2015-07-31.
2. Tabulate those stores by adoption cohort (year-quarter).
3. Count never-adopters (`Promo2 = 0`).

**Pre-committed decision rules:**

| Condition | Action |
|---|---|
| ≥ 100 in-window adopters across ≥ 3 cohorts | Proceed with Promo2 as primary design |
| 30–99 in-window adopters | Proceed, but treat the effect estimate as underpowered; foreground the methods contrast and the Goodman-Bacon decomposition instead |
| < 30 in-window adopters | **Abandon Promo2 as the primary design.** Switch to competitor openings (`CompetitionOpenSinceYear`/`Month`) as the intervention and rewrite this plan |

Record the actual counts in `deviations.md` when the gate is run. This gate exists
so that a weak design is caught before effort is sunk into it, not after.

---

## 3. Data

**Source:** Rossmann Store Sales (Kaggle). Files: `train.csv`, `store.csv`.

`test.csv` is **not used** — it has no `Sales` column and therefore no outcome.

**Panel:** 1,115 stores, daily, 2013-01-01 to 2015-07-31.

**Construction:** raw CSVs loaded to Postgres; panel built in SQL, not pandas.
Store-week panel written to a table that the estimation code reads. The SQL is part
of the deliverable.

---

## 4. Treatment definition

**Treated:** store with `Promo2 = 1` and adoption week derived from
`Promo2SinceYear` + `Promo2SinceWeek` (ISO week).

**Adoption week** = the Monday of the ISO week given by those two fields.

**Cohort** = adoption year-quarter. Quarterly rather than weekly cohorts, because
weekly cohorts will be too thin to estimate group-time effects.

**Never-treated (control):** stores with `Promo2 = 0` for the entire panel.

**Always-treated (excluded):** stores whose adoption week precedes 2013-01-01.
These are dropped entirely. They have no pre-period and, critically, must not be
used as controls — that is one of the specific ways staggered TWFE goes wrong.

**A note on `PromoInterval`:** Promo2 restarts in specific months (e.g.
"Jan,Apr,Jul,Oct"). I am estimating the effect of *program participation*, not of
the individual restart months. Once treated, a store stays treated. Treatment does
not turn off. Heterogeneity by `PromoInterval` pattern is a pre-specified
subgroup check (§9), not part of the main definition.

**Distinct from `Promo`:** the daily `Promo` flag in `train.csv` is a different,
short-run promotion that switches on and off and is plausibly targeted on expected
demand. It is **not** the treatment. It is a time-varying covariate I may control
for, and I will say so explicitly in the writeup, because conflating the two is the
most obvious way to get this project wrong.

---

## 5. Outcome variable

**Primary:** `log(mean daily sales on open days)`, aggregated to store-week.

Rationale for each choice:

- **Weekly, not daily.** Daily data carries strong day-of-week seasonality and
  makes the panel unwieldy. Weeks align naturally with `Promo2SinceWeek`.
- **Open days only.** `Sales = 0` whenever `Open = 0`. Including closed days makes
  the outcome a measure of opening frequency, not sales performance.
- **Mean per open day, not weekly total.** Otherwise a week with a public holiday
  looks like a sales decline.
- **Log.** Effects are plausibly multiplicative, the distribution is right-skewed,
  and the coefficient reads directly as an approximate percentage change.

**Secondary outcomes:**
- `log(mean daily customers)` — separates a footfall effect from a basket-size effect.
- `sales / customers` (average transaction value) — the other half of that split.

That decomposition is worth reporting even if the headline effect is small. "Promo2
raised footfall but cut average basket, netting out near zero" is a far better
finding than a null.

---

## 6. Sample restrictions

Applied in this order, with the number of stores dropped at each step logged:

1. Drop always-treated stores (adoption before 2013-01-01).
2. Drop stores missing `Promo2SinceYear`/`Week` while `Promo2 = 1`.
3. Drop store-weeks with zero open days.
4. **Refurbishment closures:** a subset of stores have a long continuous gap in the
   data during 2014. Identify stores with any gap of ≥ 4 consecutive weeks. Drop
   those stores entirely from the primary sample; include them in a robustness run.
   Doing this by a mechanical rule, decided in advance, prevents dropping stores
   based on whether they help the result.
5. Require ≥ 26 weeks of pre-adoption data for treated stores.

**Not restricted on:** `StoreType`, `Assortment`, `CompetitionDistance`, or any
outcome-related quantity.

---

## 7. Identification strategy

**Primary estimator: Callaway–Sant'Anna (2021)**, never-treated units as the
comparison group, aggregated to a single overall ATT and to an event-study profile.

Why not plain two-way fixed effects: with staggered adoption and treatment effects
that vary across cohorts or over time, the TWFE coefficient is a weighted average of
all possible 2x2 comparisons — including comparisons that use already-treated stores
as controls — and those weights can be negative. The estimate can be badly biased
and in principle carry the wrong sign.

**I will still run TWFE**, deliberately, and then run a **Goodman-Bacon
decomposition** on it to show which comparisons drive the estimate and how much
weight sits on the bad ones.

This is the intellectual centerpiece of the project. The narrative is:

> Here is the naive number. Here is the TWFE number. Here is the decomposition
> showing TWFE is contaminated. Here is the credible estimate. Here is the gap
> between them.

That story is more valuable than the effect size itself, and it is the thing that
distinguishes this from a portfolio project that calls one library function.

**Covariates:** `StoreType`, `Assortment`, and binned `CompetitionDistance` are
time-invariant, so they cannot enter as controls in a fixed-effects setting. They
enter through the covariate-conditional version of the CS estimator (conditional
parallel trends) and as subgroup splits.

**Inference:** standard errors clustered at the store level. Given the cluster count
is likely in the hundreds this should be adequate; if any cohort has very few stores,
report the CS multiplier bootstrap as well.

---

## 8. Parallel trends and placebo tests

Parallel trends is an assumption, not a fact. I will assess it and report the
assessment honestly whether or not it is flattering.

1. **Event-study pre-period coefficients.** Plot 8+ pre-adoption periods with
   confidence intervals. Flat and near zero supports the design.
2. **Selection check.** Compare adopters and never-adopters on pre-period sales
   level, sales trend, store type, assortment, and competition distance. I expect
   selection here — Rossmann plausibly enrolled stores based on performance. If
   pre-trends diverge, say so plainly and lean on the conditional-PT specification.
3. **Placebo treatment date.** Assign a fake adoption date 26 weeks before the real
   one, restrict to the pre-period, and estimate. A non-null result indicates the
   design is picking up something other than the treatment.
4. **Placebo outcome.** Estimate on an outcome the treatment should not affect
   (e.g. number of open days per week). A non-null result indicates a data artifact.
5. **In-time placebo on never-adopters.** Randomly assign fake adoption dates to
   never-adopters only; the distribution of estimates should center on zero.

**Pre-commitment:** if the pre-trend coefficients are jointly significant, I will
report that prominently and frame the estimate as suggestive rather than causal. I
will not search for a control group that makes the pre-trends flat.

---

## 9. Pre-specified heterogeneity

Only these splits, decided now, to limit multiple comparisons:

- By `StoreType` (a/b/c/d)
- By `Assortment` level
- By competition proximity (below vs. above median `CompetitionDistance`)
- By `PromoInterval` calendar pattern
- Dynamic effects by event time (does the lift decay?)

Any additional split discovered later is exploratory and will be labeled as such.

---

## 10. Power analysis

Run **before** estimating effects.

Using pre-period store-week residual variance after removing store and week fixed
effects, and the actual number of treated stores from §2, compute the **minimum
detectable effect** at 80% power, α = 0.05, clustered at store level.

Report the MDE in the writeup regardless of what the estimate turns out to be. If
the MDE is, say, 4% and the point estimate is 1%, then "no significant effect" means
the study could not have detected a plausible effect — a completely different
statement from "the program does not work." Most portfolio projects never make this
distinction.

---

## 11. Pre-committed outputs

Reported whether or not they are flattering:

- Naive cross-sectional estimate
- Naive before/after estimate
- TWFE estimate
- Goodman-Bacon decomposition (weights and component estimates)
- Callaway–Sant'Anna overall ATT with CI — **the headline number**
- Event-study plot, pre and post
- All five placebo/diagnostic results from §8
- Minimum detectable effect
- Specification curve across reasonable analytic choices

The specification curve matters: it shows the estimate under every defensible
combination of choices, rather than one chosen path.

---

## 12. What would make me distrust this result

Stated in advance so it cannot be rationalized away later:

- Pre-trend coefficients trending in the direction of the estimated effect
- The placebo treatment date producing an effect of similar magnitude
- The estimate flipping sign across reasonable specifications in the spec curve
- Goodman-Bacon showing nearly all weight on already-treated comparisons
- Fewer than 30 in-window adopters (see §2)

If several of these fire, the honest conclusion is that this data cannot identify
the effect. **That is a publishable conclusion for a portfolio project** and a
better interview answer than a confident number that does not survive scrutiny.

---

## 13. Known limitations

- Promo2 adoption is a business decision, not random. Conditional parallel trends is
  the best available assumption, and it is an assumption.
- No price, inventory, staffing, or local economic data — omitted variables that
  move with adoption cannot be ruled out.
- Panel ends July 2015; long-run effects are unobservable.
- 1,115 German drugstores over 31 months. Nothing here generalizes to other
  retailers or countries, and I will not claim it does.

---

## 14. Execution order

1. Load raw to Postgres; build store-week panel in SQL
2. **Run the feasibility gate (§2); log counts**
3. Apply sample restrictions (§6); log drops
4. Descriptives and selection check (§8.2)
5. **Power analysis (§10)**
6. Naive benchmarks (§1)
7. TWFE + Goodman-Bacon decomposition (§7)
8. Callaway–Sant'Anna primary estimate (§7)
9. Placebo suite (§8)
10. Heterogeneity (§9)
11. Specification curve (§11)
12. Interactive sensitivity app
13. Writeup

Steps 2, 5, and 6 come before any causal estimate on purpose. Knowing the MDE and
the naive benchmarks before seeing the real estimate is what keeps the analysis
honest.
