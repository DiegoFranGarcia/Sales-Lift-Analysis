-- =====================================================================
-- 03_sample.sql
-- Primary analysis sample (plan §6), applied in order.
--
-- Design note: exclusions are stored as FLAGS on a table that retains all
-- eligible stores, rather than being deleted. The primary sample is a view
-- over that table. This keeps one canonical definition of each restriction
-- while leaving the excluded stores available for the §6.4 robustness run
-- and the §11 specification curve.
-- =====================================================================

DROP VIEW IF EXISTS panel_primary;
DROP VIEW IF EXISTS store_sample_primary;
DROP TABLE IF EXISTS store_sample CASCADE;


-- ---------------------------------------------------------------------
-- Store-level sample with restriction flags
-- ---------------------------------------------------------------------
CREATE TABLE store_sample AS
WITH counts AS (
    SELECT store, COUNT(*) AS weeks_present
    FROM store_week
    GROUP BY store
),
panel AS (
    SELECT MIN(week_start) AS w0 FROM store_week
)
SELECT
    c.store,
    c.treat_group,
    c.adoption_week,
    c.cohort_quarter,
    c.store_type,
    c.assortment,
    c.competition_distance,
    c.promo_interval,
    n.weeks_present,

    -- §6.4: refurbishment closure, a uniform 25-week gap
    --       (2014-07-07 to 2014-12-22) affecting 180 stores
    (n.weeks_present = 110) AS is_gapped,

    -- Weeks of pre-adoption data available in the panel
    CASE WHEN c.adoption_week IS NOT NULL
         THEN (c.adoption_week - p.w0) / 7
    END AS pre_weeks,

    -- §6.5: ≥26 pre-adoption weeks. Applies to treated stores only;
    --       never-treated stores have no adoption date to precede.
    CASE
        WHEN c.treat_group = 'never_treated' THEN TRUE
        ELSE (c.adoption_week - p.w0) / 7 >= 26
    END AS meets_pre26

FROM store_classified c
JOIN counts n USING (store)
CROSS JOIN panel p
-- §6.1: drop always-treated stores (no observable pre-period).
-- §6.2: no stores have a missing adoption date while Promo2 = 1,
--       so that restriction is a no-op here; see deviations.md.
WHERE c.treat_group IN ('never_treated', 'in_window');

CREATE INDEX ON store_sample (store);


-- ---------------------------------------------------------------------
-- Primary store-level sample: all §6 restrictions applied
-- Expected: 99 treated, 520 never-treated
-- ---------------------------------------------------------------------
CREATE VIEW store_sample_primary AS
SELECT *
FROM store_sample
WHERE NOT is_gapped
  AND meets_pre26;


-- ---------------------------------------------------------------------
-- Primary estimation panel: store-week rows for the primary sample
-- This is the object the estimation code reads.
-- ---------------------------------------------------------------------
CREATE VIEW panel_primary AS
SELECT
    w.store,
    w.week_start,
    w.days_observed,
    w.open_days,

    -- Outcomes (§5)
    w.mean_daily_sales,
    w.mean_daily_customers,
    w.avg_transaction_value,
    LN(w.mean_daily_sales)                                  AS log_sales,
    LN(w.mean_daily_customers)                              AS log_customers,

    -- Time-varying covariates (§4: daily `promo` is NOT the treatment)
    w.promo_days,
    w.school_holiday_days,
    w.state_holiday_days,

    -- Store attributes (§9 heterogeneity, §7 conditional PT)
    s.treat_group,
    s.adoption_week,
    s.cohort_quarter,
    s.store_type,
    s.assortment,
    s.competition_distance,
    s.promo_interval,

    -- Treatment indicators
    (s.treat_group = 'in_window')                           AS ever_treated,
    (s.adoption_week IS NOT NULL
     AND w.week_start >= s.adoption_week)                   AS post_treatment,

    -- Event time in weeks relative to adoption; NULL for never-treated.
    -- Needed for the §8.1 event study.
    CASE WHEN s.adoption_week IS NOT NULL
         THEN (w.week_start - s.adoption_week) / 7
    END                                                     AS event_time

FROM store_week w
JOIN store_sample_primary s USING (store)
-- §6.3: drop store-weeks with no open days
WHERE w.open_days > 0
  AND w.mean_daily_sales > 0;