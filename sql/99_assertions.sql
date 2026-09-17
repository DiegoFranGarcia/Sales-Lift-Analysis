-- =====================================================================
-- 99_assertions.sql
-- Fails loudly if the constructed sample drifts from its specification.
-- Run after every rebuild. Each block raises an exception on violation.
-- =====================================================================

DO $$
DECLARE n INT;
BEGIN

    -- §6.1 — no always-treated stores anywhere in the sample
    SELECT COUNT(*) INTO n
    FROM store_sample WHERE treat_group = 'always_treated';
    IF n > 0 THEN
        RAISE EXCEPTION 'Always-treated stores present in store_sample: %', n;
    END IF;

    -- Primary sample composition (see deviations.md, 2026-09-14)
    SELECT COUNT(*) INTO n
    FROM store_sample_primary WHERE treat_group = 'in_window';
    IF n <> 99 THEN
        RAISE EXCEPTION 'Treated store count is %, expected 99', n;
    END IF;

    SELECT COUNT(*) INTO n
    FROM store_sample_primary WHERE treat_group = 'never_treated';
    IF n <> 520 THEN
        RAISE EXCEPTION 'Never-treated store count is %, expected 520', n;
    END IF;

    -- §6.4 — no gapped stores in the primary sample
    SELECT COUNT(*) INTO n
    FROM store_sample_primary WHERE is_gapped;
    IF n > 0 THEN
        RAISE EXCEPTION 'Gapped stores in primary sample: %', n;
    END IF;

    -- §6.5 — every treated store has ≥26 pre-adoption weeks
    SELECT COUNT(*) INTO n
    FROM store_sample_primary
    WHERE treat_group = 'in_window' AND pre_weeks < 26;
    IF n > 0 THEN
        RAISE EXCEPTION 'Treated stores below 26 pre-weeks: %', n;
    END IF;

    -- §6.3 — no store-weeks with zero open days
    SELECT COUNT(*) INTO n FROM panel_primary WHERE open_days = 0;
    IF n > 0 THEN
        RAISE EXCEPTION 'Store-weeks with zero open days: %', n;
    END IF;

    -- Outcome is well-defined everywhere
    SELECT COUNT(*) INTO n
    FROM panel_primary WHERE log_sales IS NULL OR log_sales = 'NaN';
    IF n > 0 THEN
        RAISE EXCEPTION 'Rows with null/NaN log_sales: %', n;
    END IF;

    -- Treatment indicator consistency: post_treatment iff event_time >= 0
    SELECT COUNT(*) INTO n
    FROM panel_primary
    WHERE ever_treated
      AND (post_treatment <> (event_time >= 0));
    IF n > 0 THEN
        RAISE EXCEPTION 'post_treatment inconsistent with event_time: % rows', n;
    END IF;

    -- Never-treated stores are never flagged as treated
    SELECT COUNT(*) INTO n
    FROM panel_primary
    WHERE NOT ever_treated AND (post_treatment OR event_time IS NOT NULL);
    IF n > 0 THEN
        RAISE EXCEPTION 'Never-treated rows carry treatment timing: %', n;
    END IF;

    -- §8.1 — every treated store has at least 8 observed pre-periods
    SELECT COUNT(*) INTO n
    FROM (
        SELECT store
        FROM panel_primary
        WHERE ever_treated AND event_time < 0
        GROUP BY store
        HAVING COUNT(*) < 8
    ) t;
    IF n > 0 THEN
        RAISE EXCEPTION 'Treated stores with <8 observed pre-periods: %', n;
    END IF;

    -- Panel is unique at store-week
    SELECT COUNT(*) INTO n
    FROM (
        SELECT store, week_start
        FROM panel_primary
        GROUP BY store, week_start HAVING COUNT(*) > 1
    ) d;
    IF n > 0 THEN
        RAISE EXCEPTION 'Duplicate store-week rows: %', n;
    END IF;

    RAISE NOTICE 'All assertions passed.';
END $$;