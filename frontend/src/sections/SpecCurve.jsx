import * as Plot from "@observablehq/plot";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { usePlot } from "../usePlot";

// Branch order drives the panel beneath the curve. pre_min goes first because
// it is the only choice that moves the estimate appreciably.
const BRANCHES = [
  ["pre_min", "Pre-period required"],
  ["gapped", "Refurbished stores"],
  ["grain", "Time grain"],
  ["outcome", "Outcome"],
  ["closure_rule", "Closure rule"],
  ["control", "Comparison group"],
];

const LEVEL_LABEL = {
  13: "13 weeks", 20: "20 weeks", 26: "26 weeks", 39: "39 weeks",
  exclude: "excluded", include: "included",
  weekly: "weekly", quarterly: "quarterly",
  mean_daily: "sales per open day", total: "weekly total",
  literal: "any long closure", refurb_only: "refurbishment only",
  never_treated: "never joined", not_yet_treated: "not yet joined",
};

export default function SpecCurve({ data }) {
  const [raw, setRaw] = useState(null);
  const [branches, setBranches] = useState(null);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    api.specCurve().then((d) => {
      setRaw(d.rows);
      setBranches(d.branches);
    });
  }, []);

  const mde = data.diagnostics.mde_empirical.value;

  // A filter with no levels selected means "all levels", so an empty filter
  // set shows the full grid rather than nothing.
  const shown = useMemo(() => {
    if (!raw) return null;
    return raw.filter((r) =>
      Object.entries(filters).every(
        ([k, levels]) => levels.length === 0 || levels.includes(r[k])
      )
    );
  }, [raw, filters]);

  const sorted = useMemo(
    () =>
      shown
        ? [...shown].sort((a, b) => a.att - b.att).map((r, i) => ({ ...r, rank: i }))
        : null,
    [shown]
  );

  const belowMde = sorted?.filter((r) => r.att < mde).length ?? 0;

  function toggle(branch, level) {
    setFilters((f) => {
      const cur = f[branch] ?? [];
      const next = cur.includes(level)
        ? cur.filter((x) => x !== level)
        : [...cur, level];
      return { ...f, [branch]: next };
    });
  }

  const curveRef = usePlot(
    (width) => {
      if (!sorted || sorted.length === 0) return null;

      return Plot.plot({
        width,
        height: 300,
        marginLeft: 56,
        marginRight: 24,
        marginTop: 20,
        marginBottom: 44,
        x: {
          label: "Specifications, ordered by estimate",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-2, Math.max(sorted.length, 20) + 1],
        },
        y: {
          label: "Estimated effect (%)",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-0.02, 0.07],
          grid: true,
          tickFormat: (d) => (d * 100).toFixed(0),
        },
        style: {
          background: "transparent",
          fontFamily: "Archivo, system-ui, sans-serif",
          fontSize: "13px",
          color: "var(--ink)",
        },
        marks: [
          Plot.rect([{ y1: -0.02, y2: mde }], {
            y1: "y1",
            y2: "y2",
            fill: "var(--band)",
          }),
          Plot.ruleY([0], { stroke: "var(--graphite)" }),
          Plot.dot(sorted, {
            x: "rank",
            y: "att",
            // Below the detection band, an estimate is not distinguishable
            // from nothing, so it is drawn as such.
            fill: (d) => (d.att < mde ? "var(--ghost)" : "var(--mark)"),
            r: 3,
          }),
          Plot.tip(
            sorted,
            Plot.pointer({
              x: "rank",
              y: "att",
              title: (d) =>
                [
                  `${(d.att * 100).toFixed(2)}%`,
                  `${d.n_treated} treated stores`,
                  "",
                  `pre-period  ${LEVEL_LABEL[d.pre_min]}`,
                  `refurbished ${LEVEL_LABEL[d.gapped]}`,
                  `grain       ${LEVEL_LABEL[d.grain]}`,
                  `outcome     ${LEVEL_LABEL[d.outcome]}`,
                ].join("\n"),
            })
          ),
        ],
      });
    },
    [sorted, mde]
  );

  if (!sorted || !branches) {
    return <section><div className="prose" /></section>;
  }

  return (
    <section>
      <div className="prose">
        <h2>Every defensible way to run it</h2>
        <p>
          Every analysis makes choices that could reasonably have gone the other
          way. How long a run-up should a store need before it counts? Should
          stores closed for refurbishment be in or out? Weekly data or
          quarterly? Six such choices, each with two to four settings, make 128
          complete analyses — all of them defensible, none of them cherry-picked
          after the fact.
        </p>
        <p>
          Each dot is one of those analyses. Grey dots fall inside the detection
          band, where the estimate can’t be told apart from nothing. Turn
          settings on and off to see which choices matter.
        </p>
      </div>

      <figure className="figure">
        <div className="spec-head">
          <span className="spec-count num">
            <strong>{belowMde}</strong> of {sorted.length} below detection
          </span>
          {Object.values(filters).some((v) => v.length) && (
            <button className="link-btn" onClick={() => setFilters({})}>
              Clear filters
            </button>
          )}
        </div>

        <div ref={curveRef} />

        <div className="branch-grid">
          {BRANCHES.map(([key, label]) => (
            <div key={key} className="branch">
              <span className="branch-label">{label}</span>
              <div className="segmented">
                {branches[key].map((lvl) => {
                  const on = (filters[key] ?? []).includes(lvl);
                  return (
                    <button
                      key={String(lvl)}
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggle(key, lvl)}
                    >
                      {LEVEL_LABEL[lvl] ?? String(lvl)}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        <figcaption>
          128 Callaway–Sant’Anna estimates, one per combination of analytic
          choices. Selecting nothing in a row leaves all of its settings in.
        </figcaption>
      </figure>

      <div className="prose">
        <p>
          Across all 128, the estimate runs from −0.55% to +6.24%, with a median
          of +3.58% — and <strong>62 of them land inside the band</strong>.
          Nearly half the defensible analytic space produces a number this study
          could not have detected.
        </p>
        <p>
          Five of the six choices barely matter. Switch the outcome, the time
          grain, the comparison group or the closure rule and the curve hardly
          moves. The exception is the pre-period requirement: demand 39 weeks of
          history instead of 26 and the average estimate falls from +3.46% to{" "}
          <strong>+0.76%</strong>.
        </p>
        <p>
          That requirement is not a modelling choice. It decides which stores
          are in the study — and at 39 weeks it drops the earliest adopters,
          including a single cohort of 31 stores that joined in one week in July
          2013. Remove that cohort alone and the headline falls from +4.37% to
          +1.71%.
        </p>
      </div>
    </section>
  );
}