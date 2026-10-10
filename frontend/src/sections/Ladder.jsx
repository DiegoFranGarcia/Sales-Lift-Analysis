import * as Plot from "@observablehq/plot";
import { usePlot } from "../usePlot";

const ORDER = [
  "naive_cross_sectional",
  "naive_before_after",
  "twfe",
  "cs_att",
];

const SHORT = {
  naive_cross_sectional: "Adopters vs never-adopters",
  naive_before_after:    "Adopters, before vs after",
  twfe:                  "Two-way fixed effects",
  cs_att:                "Callaway–Sant'Anna",
};

export default function Ladder({ data }) {
  const mde = data.diagnostics.mde_empirical.pct;

  const rows = ORDER.map((k) => {
    const e = data.estimates[k];
    return {
      key: k,
      label: SHORT[k],
      pct: e.pct,
      lo: e.pct_lo,
      hi: e.pct_hi,
      // An estimate is "invisible" when its whole interval sits inside the
      // detection band - the design could not have told it apart from zero.
      ghost: Math.abs(e.pct) < mde,
    };
  });

  const ref = usePlot(
    (width) =>
      Plot.plot({
        width,
        height: 280,
        marginLeft: 190,
        marginRight: 24,
        marginTop: 16,
        marginBottom: 44,
        x: {
          domain: [-16, 13],
          label: "Change in sales (%)",
          labelAnchor: "center",
          labelArrow: null,
          grid: true,
          tickFormat: (d) => (d > 0 ? `+${d}` : `${d}`),
        },
        y: { domain: rows.map((r) => r.label), label: null },
        style: {
          background: "transparent",
          fontFamily: "Archivo, system-ui, sans-serif",
          fontSize: "13px",
          color: "var(--ink)",
        },
        marks: [
          // The detection band: anything in here is below what this design
          // can resolve. It reappears in every later chart.
          Plot.rect([{ x1: -mde, x2: mde }], {
            x1: "x1",
            x2: "x2",
            fill: "var(--band)",
          }),
          Plot.ruleX([0], { stroke: "var(--graphite)", strokeWidth: 1 }),
          Plot.ruleY(rows, {
            y: "label",
            x1: "lo",
            x2: "hi",
            stroke: (d) => (d.ghost ? "var(--ghost)" : "var(--mark)"),
            strokeWidth: 1.5,
          }),
          Plot.dot(rows, {
            y: "label",
            x: "pct",
            fill: (d) => (d.ghost ? "var(--ghost)" : "var(--mark)"),
            r: 5,
          }),
          Plot.text(rows, {
            y: "label",
            x: "hi",
            text: (d) => `${d.pct > 0 ? "+" : ""}${d.pct.toFixed(2)}%`,
            dx: 10,
            textAnchor: "start",
            fill: (d) => (d.ghost ? "var(--ghost)" : "var(--ink)"),
            fontWeight: 600,
          }),
        ],
      }),
    [data]
  );

  return (
    <section>
      <div className="prose">
        <h2>Four ways to ask the same question</h2>
        <p>
          Each row adds a correction to the one above it. The first compares
          adopters to non-adopters and finds a large negative effect, because
          stores that joined were already smaller. Holding store identity fixed
          removes that. Holding calendar time fixed removes chain-wide trends.
        </p>
        <p>
          The shaded band is the smallest effect this study can reliably detect:
          3.34%, measured by assigning fake adoption dates to stores that never
          adopted and watching how much the estimate moves on its own. An
          estimate inside the band is indistinguishable from nothing.
        </p>
      </div>

      <figure className="figure">
        <div ref={ref} />
        <figcaption>
          Point estimates with 95% confidence intervals. Standard errors
          clustered by store; the Callaway–Sant'Anna interval comes from 999
          multiplier bootstrap replications.{" "}
          <span className="band-key">below detection</span>
        </figcaption>
      </figure>

      <div className="prose">
        <p>
          The last row is the one to take seriously. Callaway–Sant'Anna compares
          each group of stores only against stores that never joined, which
          avoids a known failure of the standard approach when adoption happens
          at different times. It gives <strong>+4.37%</strong>, well clear of
          the detection band, with a confidence interval that excludes zero.
        </p>
        <p>That looks like an answer. The rest of this page is about why it isn't.</p>
      </div>
    </section>
  );
}