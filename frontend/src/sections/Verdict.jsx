export default function Verdict({ data }) {
  const conds = data.distrust_conditions;
  const fired = conds.filter((c) => c.status === "FIRED").length;

  return (
    <section>
      <div className="prose">
        <h2>What would have to be true for this to be wrong</h2>
        <p>
          Before any of the analysis was run, the plan for this project listed
          five things that would mean the result could not be trusted. The point
          of writing them down in advance was to make it impossible to explain
          them away afterwards.{" "}
          <a href="https://github.com/DiegoFranGarcia/Sales-Lift-Analysis/blob/main/docs/analysis_plan.md">
            The plan
          </a>{" "}
          is in the repository, committed before the first estimate was
          computed.
        </p>
        <p>Here is how they stand.</p>
      </div>

      <div className="figure">
        <ol className="conditions">
          {conds.map((c, i) => (
            <li key={i} className={`cond cond-${c.status.toLowerCase().replace(" ", "-")}`}>
              <span className="cond-status">{c.status}</span>
              <div>
                <p className="cond-text">{c.text}</p>
                <p className="cond-evidence">{c.evidence}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>

      <div className="prose">
        <p>
          {fired === 1 ? "One has" : `${fired} have`} fired outright and a third
          is partly met. The plan said that if several fired, the honest
          conclusion is that the data cannot identify the effect — and called
          that a publishable result rather than a failure.
        </p>

        <h2 style={{ marginTop: "3rem" }}>So did the program work?</h2>
        <p className="lede">
          This data can’t say. Stores joined Promo2 while they were sliding, and
          they stopped sliding around the time they joined. Whatever happened
          next, no method here can separate the program from the recovery that
          was already underway.
        </p>
        <p>
          That is not the same as finding nothing. The estimate is{" "}
          <strong>+4.37%</strong>, it clears the detection threshold, and the
          confidence interval excludes zero. If you stopped at the headline it
          would look like a solid result. It took a fake adoption date, a
          sensitivity bound, a leave-one-out and 128 specifications to establish
          that it isn’t one.
        </p>
        <p>
          What would settle it: knowing why Rossmann enrolled the stores it did.
          If enrolment was triggered by a dip, the comparison group is wrong by
          construction and no amount of statistical machinery fixes it. That is
          a question for the business, not the dataset.
        </p>
      </div>

      <div className="prose colophon">
        <p>
          1,115 stores, 1,017,209 daily observations, January 2013 to July
          2015. Panel built in PostgreSQL; estimation in Python. The{" "}
          <a href="https://github.com/DiegoFranGarcia/Sales-Lift-Analysis/blob/main/docs/analysis_plan.md">
            analysis plan
          </a>
          , the{" "}
          <a href="https://github.com/DiegoFranGarcia/Sales-Lift-Analysis/blob/main/docs/deviations.md">
            log of every deviation from it
          </a>{" "}
          and the{" "}
          <a href="https://github.com/DiegoFranGarcia/Sales-Lift-Analysis">
            code
          </a>{" "}
          are public.
        </p>
      </div>
    </section>
  );
}