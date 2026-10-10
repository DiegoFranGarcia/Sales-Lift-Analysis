import * as Plot from "@observablehq/plot";
import { useEffect, useState } from "react";
import { api } from "../api";
import { usePlot } from "../usePlot";

export default function Placebos({ data }) {
  const [draws, setDraws] = useState(null);

  useEffect(() => {
    api.placebo().then((d) => setDraws(d.draws));
  }, []);

  const real = data.estimates.cs_att.att;
  const mde = data.diagnostics.mde_empirical.value;
  const intime = data.diagnostics.placebo_intime;
  const dose = data.diagnostics.placebo_dose.rows;

  // ------------------------------------------------------------------
  // Figure 1: the null distribution.
  // 500 fake treatment assignments among stores that never adopted. If the
  // method invents effects, this is where it shows up.
  // ------------------------------------------------------------------
  const histRef = usePlot(
    (width) => {
      if (!draws) return null;
      const rows = draws.map((d) => ({ att: d }));

      return Plot.plot({
        width,
        height: 300,
        marginLeft: 56,
        marginRight: 24,
        marginTop: 28,
        marginBottom: 52,
        x: {
          label: "Estimated effect when nothing happened (%)",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-0.055, 0.055],
          tickFormat: (d) => (d * 100).toFixed(0),
        },
        y: { label: "Draws", labelAnchor: "center", labelArrow: null, grid: true },
        style: {
          background: "transparent",
          fontFamily: "Archivo, system-ui, sans-serif",
          fontSize: "13px",
          color: "var(--ink)",
        },
        marks: [
          // The detection band, carried over from the first figure.
          Plot.rect([{ x1: -mde, x2: mde }], {
            x1: "x1",
            x2: "x2",
            fill: "var(--band)",
          }),
          Plot.rectY(rows, Plot.binX({ y: "count" }, {
            x: "att",
            thresholds: 44,
            fill: "var(--mark)",
            fillOpacity: 0.75,
          })),
          Plot.ruleY([0], { stroke: "var(--graphite)" }),
          Plot.ruleX([0], { stroke: "var(--graphite)", strokeDasharray: "3,3" }),
          // Where the real estimate sits relative to this null.
          Plot.ruleX([real], { stroke: "var(--fired)", strokeWidth: 2 }),
          Plot.text([{ x: real, y: 0 }], {
            x: "x",
            y: "y",
            text: () => "the real estimate",
            fill: "var(--fired)",
            fontWeight: 600,
            textAnchor: "end",
            dy: -124,
            dx: -8,
          }),
        ],
      });
    },
    [draws, real, mde]
  );

  // ------------------------------------------------------------------
  // Figure 2: dose response.
  // Move the fake adoption date further back and the "effect" grows. A
  // treatment effect would not behave this way; an accumulating trend does.
  // ------------------------------------------------------------------
  const doseRef = usePlot(
    (width) =>
      Plot.plot({
        width,
        height: 300,
        marginLeft: 56,
        marginRight: 80,
        marginTop: 28,
        marginBottom: 52,
        x: {
          label: "Weeks the fake adoption date was moved back",
          labelAnchor: "center",
          labelArrow: null,
          domain: [8, 44],
        },
        y: {
          label: "Estimated effect (%)",
          labelAnchor: "center",
          labelArrow: null,
          domain: [-0.07, 0.03],
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
          Plot.rect([{ x1: 8, x2: 44 }], {
            x1: "x1",
            x2: "x2",
            y1: -mde,
            y2: mde,
            fill: "var(--band)",
          }),
          Plot.ruleY([0], { stroke: "var(--graphite)" }),
          Plot.line(dose, {
            x: "shift",
            y: "att",
            stroke: "var(--fired)",
            strokeWidth: 1.5,
          }),
          Plot.dot(dose, {
            x: "shift",
            y: "att",
            fill: "var(--fired)",
            r: 5,
          }),
          Plot.text(dose, {
            x: "shift",
            y: "att",
            text: (d) => `${(d.att * 100).toFixed(1)}%`,
            dy: -16,
            fill: "var(--ink)",
            fontWeight: 600,
          }),
          Plot.text(dose, {
            x: "shift",
            y: "att",
            text: (d) => `${d.n_treated} stores`,
            dy: 20,
            fill: "var(--graphite)",
            fontSize: 11,
          }),
        ],
      }),
    [dose, mde]
  );

  return (
    <section>
      <div className="prose">
        <h2>Pointing the method at nothing</h2>
        <p>
          A drifting pre-period is a reason for suspicion, not a verdict. The
          way to settle it is to run the same analysis on situations where the
          answer has to be zero, and see what comes back.
        </p>
        <p>
          The first test takes only the 514 stores that never joined, picks 96
          of them at random, and pretends they joined — same dates, same group
          sizes as the real adopters. Nothing happened to these stores. Repeat
          five hundred times.
        </p>
      </div>

      <figure className="figure">
        <div ref={histRef} />
        <figcaption>
          {intime.n} estimates from randomly assigned fake adoption dates among
          never-adopters. Mean {(intime.mean * 100).toFixed(2)}%. None reached
          the real estimate.
        </figcaption>
      </figure>

      <div className="prose">
        <p>
          The method passes. The distribution sits on zero, and not one of the
          five hundred fake assignments produced anything close to{" "}
          {((Math.exp(real) - 1) * 100).toFixed(2)}%. That spread is also where the detection
          band comes from: 3.34% is 2.8 times the standard deviation of this
          histogram, measured rather than assumed.
        </p>
        <p>
          The second test is narrower and much less forgiving. Keep the real
          adopters, but move each store’s adoption date backwards and cut the
          data off at the real one, so the method is looking only at weeks
          before anything happened.
        </p>
      </div>

      <figure className="figure">
        <div ref={doseRef} />
        <figcaption>
          Each point is a separate estimate on a panel truncated at real
          adoption. Store counts fall at longer shifts because early adopters
          run out of room before their fake date.
        </figcaption>
      </figure>

        <div className="prose">
        <p>
          Thirteen weeks back, nothing — <strong>+0.98%</strong>, inside the
          band, which is the right answer. Push the fake date to twenty weeks
          and the method reports <strong>−4.02%</strong> on 93 of the 96
          stores. That is the same size as the real estimate, in the opposite
          direction, from a date on which nothing occurred.
        </p>
        <p>
          Beyond twenty weeks the pattern holds but the sample shrinks sharply —
          only 50 stores survive a 39-week shift — so those later points are
          noisier and bounce around. What matters is the jump between thirteen
          and twenty weeks. The drift lives in that stretch, and once the fake
          date reaches back far enough to include it, a non-effect turns into a
          significant one.
        </p>
      </div>
    </section>
  );
}