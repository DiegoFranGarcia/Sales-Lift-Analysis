import { useEffect, useState } from "react";
import { api } from "./api";
import Ladder from "./sections/Ladder";
import EventStudy from "./sections/Eventstudy";
import Placebos from "./sections/Placebos";
import SpecCurve from "./sections/SpecCurve";
import Verdict from "./sections/Verdict";

export default function App() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    api.headline().then(setData).catch((e) => setErr(e.message));
  }, []);

  if (err)
    return (
      <div className="shell prose" style={{ padding: "6rem 1.5rem" }}>
        <h2>The analysis server isn’t running</h2>
        <p>
          Start it with <code>python -m uvicorn api.main:app --reload</code>{" "}
          from the project root, then reload this page.
        </p>
        <p style={{ color: "var(--graphite)" }}>{err}</p>
      </div>
    );

  if (!data) return <div className="shell" style={{ padding: "6rem 1.5rem" }} />;

  const naive = data.estimates.naive_cross_sectional;

  return (
    <main className="shell">
      <section>
        <div className="prose">
          <h1>Did Rossmann’s promotion program work?</h1>
          <p className="bignum num">{naive.pct.toFixed(1)}%</p>
          <p className="bignum-label">
            What a direct comparison of participating and non-participating
            stores says the program did to sales.
          </p>
        </div>
        <div className="prose" style={{ marginTop: "3rem" }}>
          <p className="lede">
            That number is almost certainly backwards. Fixing it takes four
            estimators, five diagnostic tests and 128 specifications — and the
            answer at the end is not the one the data first appears to give.
          </p>
          <p>
            Rossmann is a German drugstore chain. Between 2013 and 2015, 96 of
            its stores joined a continuing promotional program called Promo2,
            at fifteen different points in time. 514 never joined. This is an
            attempt to find out whether joining raised sales.
          </p>
        </div>
      </section>

      <Ladder data={data} />
      <EventStudy />
      <Placebos data={data} />
      <SpecCurve data={data} />
      <Verdict data={data} />
    </main>
  );
}