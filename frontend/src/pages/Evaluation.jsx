import { useState } from "react";
import { PageHeader } from "../components/AppLayout";
import { metrics, runs } from "../data/sample";

function TargetBar({ pct, target }) {
  return (
    <span className="relative block h-1.5 w-[180px] bg-rule">
      <span className="block h-1.5 bg-brand" style={{ width: `${pct}%` }} />
      <span className="absolute -top-1 h-3.5 w-0.5 bg-ink" style={{ left: `${target}%` }} />
    </span>
  );
}

// Replace with: GET /eval/latest, GET /eval/runs, POST /eval/run
export default function Evaluation() {
  const [running, setRunning] = useState(false);

  return (
    <>
      <PageHeader title="Evaluation" lead="How well SearchLab.AI finds and answers, measured on a fixed test set." />
      <p className="m-0 max-w-[880px] rounded-md border border-rule bg-white px-4 py-3 text-sm text-graphite">
        Figures on this page are sample data for the demo. Real results appear after the first evaluation run.
      </p>

      <section className="sheet overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse text-[15px]">
          <caption className="caption">Latest run against the 25-question test set</caption>
          <thead><tr>{["Measure", "Result", "Against target", "Target", "Status"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}</tr></thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={m.label}>
                <td className="td font-serif text-lg">{m.label}</td>
                <td className="td font-serif text-[26px] font-medium">{m.value}</td>
                <td className="td align-middle"><TargetBar pct={m.pct} target={m.target} /></td>
                <td className="td text-graphite">{m.targetLabel}</td>
                <td className="td font-semibold text-brand">Met</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="flex flex-wrap gap-10">
        <section className="sheet flex-[2_1_460px] overflow-x-auto">
          <table className="w-full min-w-[460px] border-collapse text-[15px]">
            <caption className="caption">Previous runs</caption>
            <thead><tr>{["Run", "Date", "Correct passage found", "Hit rate", "Outcome"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}</tr></thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.run}>
                  <td className="td">{r.run}</td><td className="td">{r.date}</td><td className="td">{r.found}</td><td className="td">{r.rate}</td>
                  <td className={`td font-semibold ${r.met ? "text-brand" : "text-[#7A4E00]"}`}>{r.met ? "Met target" : "Below target"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <section className="flex flex-[1_1_280px] flex-col gap-3.5">
          <h2 className="m-0 font-serif text-[21px] font-medium">User feedback</h2>
          <p className="m-0 text-[15px] leading-relaxed text-graphite">46 answers marked helpful, 7 marked not helpful.</p>
          <span className="flex h-2 bg-rule"><span className="bg-brand" style={{ width: "87%" }} /></span>
          <button type="button" className="btn mt-3 self-start" disabled={running}
            onClick={() => { setRunning(true); setTimeout(() => setRunning(false), 2500); }}>
            {running ? "Running evaluation…" : "Run evaluation"}
          </button>
          <p role="status" className="m-0 text-sm text-graphite">
            {running ? "Running 25 test questions. You can leave this page." : "Runs all 25 test questions against the current documents. Takes about 2 minutes."}
          </p>
        </section>
      </div>
    </>
  );
}
