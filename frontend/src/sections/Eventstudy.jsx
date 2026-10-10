import * as Plot from "@observablehq/plot";
import { useEffect, useState } from "react";
import { api } from "../api";
import { usePlot } from "../usePlot";

// Horizons beyond about -60 rest on 1-9 of 15 cohorts, so they describe a
// handful of late adopters rather than the sample. The control stops at -52.
const WINDOWS = [12, 26, 39, 52];

export default function EventStudy() {
  const [rows, setRows] = useState(null);
  const [win, setWin] = useState(12);

  useEffect(() => {
    api.eventStudy().then((d) => setRows(d.rows));
  }, []);

  const shown = rows?.filter((r) => r.event_time >= -win && r.event_time <= 26);

  // Pre-adoption horizons only, excluding the reference period at -1.
  const pre = shown?.filter((r) => r.event_time < 0 && !r.is_reference) ?? [];

  // A violation is a horizon whose SIMULTANEOUS band clears zero. Pointwise
  // intervals flag far more, which is the point of the comparison.
  const violating = pre.filter(
    (r) => r.cband_lower != null && (r.cband_lower > 0 || r.cband_upper < 0)
  );

  const ref = usePlot(
    (width) => {
      if (!shown) return null;

      return Plot.plot({
        width,
        height: 440,
        marginLeft: 64,
        marginRight: 24,
        marginTop: 24,
        marginBottom: 52,
        x: {
          label: "Weeks relative to joining Promo2",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-win - 1, 27],
        },
        y: {
          label: "Effect on log sales",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-0.08, 0.14],
          grid: true,
          tickFormat: (d) => d.toFixed(2),
        },
        style: {
          background: "transparent",
          fontFamily: "Archivo, system-ui, sans-serif",
          fontSize: "13px",
          color: "var(--ink)",
        },
        marks: [
          // Pre-adoption region: where nothing should be happening.
          Plot.rect([{ x1: -win - 1, x2: 0 }], {
            x1: "x1",
            x2: "x2",
            fill: "var(--ink)",
            fillOpacity: 0.03,
          }),
          Plot.text([{ x: -win / 2, y: 0.132 }], {
            x: "x",
            y: "y",
            text: () => `${win} weeks before joining`,
            fill: "var(--graphite)",
            fontSize: 12,
            textAnchor: "start",
            dx: 6,
          }),

          Plot.ruleY([0], { stroke: "var(--graphite)" }),

          // Simultaneous (uniform) band - wide, pale.
          Plot.ruleX(
            shown.filter((d) => d.cband_lower != null),
            {
              x: "event_time",
              y1: "cband_lower",
              y2: "cband_upper",
              stroke: "var(--mark)",
              strokeOpacity: 0.2,
              strokeWidth: 7,
            }
          ),

          // Pointwise 95% interval - narrow, darker, drawn on top.
          Plot.ruleX(shown, {
            x: "event_time",
            y1: "conf_int_lower",
            y2: "conf_int_upper",
            stroke: "var(--mark)",
            strokeOpacity: 0.6,
            strokeWidth: 2,
          }),

          Plot.dot(shown, {
            x: "event_time",
            y: "att",
            fill: "var(--mark)",
            r: 2.5,
          }),

          // The drift, made explicit. 26 noisy bars do not show a trend on
          // their own; the fitted line does.
          pre.length > 2 &&
            Plot.linearRegressionY(pre, {
              x: "event_time",
              y: "att",
              stroke: "var(--fired)",
              strokeWidth: 1.5,
              strokeDasharray: "5,4",
              ci: 0,
            }),

          // Horizons whose simultaneous band excludes zero.
          Plot.dot(violating, {
            x: "event_time",
            y: "att",
            fill: "var(--fired)",
            r: 4.5,
          }),

          // Adoption week.
          Plot.ruleX([0], { stroke: "var(--ink)", strokeDasharray: "3,3" }),

          Plot.tip(
            shown,
            Plot.pointerX({
              x: "event_time",
              y: "att",
              title: (d) =>
                [
                  `week ${d.event_time}`,
                  `effect ${(d.att * 100).toFixed(2)}%`,
                  `${d.n} of 15 cohorts`,
                ].join("\n"),
            })
          ),
        ].filter(Boolean),
      });
    },
    [shown, win]
  );

  return (
    <section>
      <div className="prose">
        <h2>What was happening before they joined</h2>
        <p>
          Difference-in-differences rests on one assumption: that joining and
          non-joining stores would have moved together if the program had never
          existed. You can’t verify that, but you can check whether they moved
          together <em>before</em> anyone joined.
        </p>
        <p>
          Week zero is the week each store joined. Everything to the left should
          sit flat at zero. Widen the window to look further back.
        </p>
      </div>

      <figure className="figure">
        <div className="controls">
            <span className="controls-label">Look back</span>
            <div className="segmented">
                {WINDOWS.map((w) => (
                <button
                    key={w}
                    type="button"
                    onClick={() => setWin(w)}
                    aria-pressed={win === w}
                >
                    {w} weeks
                </button>
                ))}
            </div>
            <span className={violating.length ? "tally tally-fired" : "tally"}>
                {violating.length === 0
                ? "no violations"
                : `${violating.length} violation${violating.length > 1 ? "s" : ""}`}
            </span>
        </div>

        <div ref={ref} />

        <figcaption>
          Narrow dark bars are pointwise 95% intervals; the pale wider bars are
          simultaneous intervals, which account for testing many horizons at
          once. Red points mark horizons whose simultaneous band excludes zero.
          The dashed red line is a linear fit through the pre-period
          coefficients.
        </figcaption>
      </figure>

      <div className="prose">
        <p>
          At twelve weeks the pre-period looks clean — no violations, nothing to
          worry about. That is the window most analyses would check, and it is
          the window this one checked first.
        </p>
        <p>
          Widen it and a slope appears. Across the full year before adoption,
          joining stores sit a few percent above the comparison group and slide
          steadily toward it, arriving at parity around the week they sign up.
          Nothing in the twelve-week view hints at this.
        </p>
        <p>
          Which matters because of where the estimator takes its baseline:
          Callaway–Sant’Anna measures each store’s change from the single week
          before it joined. That week is the bottom of the slide.
        </p>
      </div>
    </section>
  );
}