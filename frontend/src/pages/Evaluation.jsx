import { useState, useEffect } from "react";
import { PageHeader } from "../components/AppLayout";
import { api } from "../api";

function TargetBar({ pct, target }) {
  return (
    <span className="relative block h-1.5 w-[180px] bg-rule">
      <span className="block h-1.5 bg-brand" style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
      <span className="absolute -top-1 h-3.5 w-0.5 bg-ink" style={{ left: `${target}%` }} />
    </span>
  );
}

export default function Evaluation() {
  const [running, setRunning] = useState(false);
  const [latestMetrics, setLatestMetrics] = useState(null);
  const [coverageGaps, setCoverageGaps] = useState({ unanswered: [], conflicts: [] });
  const [notice, setNotice] = useState("");

  const loadData = async () => {
    try {
      const gaps = await api.getCoverageGaps();
      setCoverageGaps(gaps || { unanswered: [], conflicts: [] });
    } catch (e) {
      setNotice("Admin privileges required to view evaluation data.");
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const triggerRun = async () => {
    setRunning(true);
    setNotice("");
    try {
      const res = await api.runEvaluation();
      setLatestMetrics(res.metrics);
      loadData();
    } catch (err) {
      setNotice(err.message || "Evaluation run failed.");
    } finally {
      setRunning(false);
    }
  };

  const hitRate = latestMetrics?.hit_rate_percentage ?? 100;
  const faithfulness = latestMetrics?.out_of_scope_accuracy_percentage ?? 100;

  return (
    <>
      <PageHeader title="Evaluation & Coverage" lead="How well SearchLab.AI finds and answers, measured on a fixed test set." />

      {notice && (
        <div className="sheet max-w-[880px] p-4 text-[#8A2E25] bg-[#FDF2F1] rounded text-sm">
          {notice}
        </div>
      )}

      <section className="sheet overflow-x-auto">
        <table className="w-full min-w-[820px] border-collapse text-[15px]">
          <caption className="caption">Latest Evaluation Run</caption>
          <thead><tr>{["Measure", "Result", "Against target", "Target", "Status"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}</tr></thead>
          <tbody>
            <tr>
              <td className="td font-serif text-lg">Retrieval hit rate</td>
              <td className="td font-serif text-[26px] font-medium">{hitRate}%</td>
              <td className="td align-middle"><TargetBar pct={hitRate} target={80} /></td>
              <td className="td text-graphite">80% or higher</td>
              <td className={`td font-semibold ${hitRate >= 80 ? "text-brand" : "text-[#7A4E00]"}`}>
                {hitRate >= 80 ? "Met" : "Below target"}
              </td>
            </tr>
            <tr>
              <td className="td font-serif text-lg">Faithfulness / Out-of-scope gating</td>
              <td className="td font-serif text-[26px] font-medium">{faithfulness}%</td>
              <td className="td align-middle"><TargetBar pct={faithfulness} target={90} /></td>
              <td className="td text-graphite">90% or higher</td>
              <td className={`td font-semibold ${faithfulness >= 90 ? "text-brand" : "text-[#7A4E00]"}`}>
                {faithfulness >= 90 ? "Met" : "Below target"}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <div className="flex flex-wrap gap-10">
        <section className="sheet flex-[2_1_460px] overflow-x-auto">
          <table className="w-full min-w-[460px] border-collapse text-[15px]">
            <caption className="caption">Content Coverage Gaps & Conflicts ({coverageGaps.unanswered?.length || 0} unanswered)</caption>
            <thead><tr>{["Topic / Question", "Count / Severity", "Status"].map((h) => <th key={h} scope="col" className="th">{h}</th>)}</tr></thead>
            <tbody>
              {(coverageGaps.unanswered || []).slice(0, 5).map((u, i) => (
                <tr key={i}>
                  <td className="td font-medium">{u.question}</td>
                  <td className="td">{u.count} times asked</td>
                  <td className="td font-semibold text-[#A33A2F]">Needs documentation</td>
                </tr>
              ))}
              {(!coverageGaps.unanswered || coverageGaps.unanswered.length === 0) && (
                <tr>
                  <td colSpan={3} className="td text-center text-graphite py-4">No content gaps detected.</td>
                </tr>
              )}
            </tbody>
          </table>
        </section>

        <section className="flex flex-[1_1_280px] flex-col gap-3.5">
          <h2 className="m-0 font-serif text-[21px] font-medium">Evaluation Runner</h2>
          <p className="m-0 text-[15px] leading-relaxed text-graphite">
            Runs automated evaluation questions against current corpus to compute Hit Rate and Faithfulness metrics.
          </p>
          <button type="button" className="btn mt-3 self-start" disabled={running} onClick={triggerRun}>
            {running ? "Running benchmark…" : "Run evaluation benchmark"}
          </button>
          <p role="status" className="m-0 text-sm text-graphite">
            {running ? "Running evaluation benchmark. Results will refresh momentarily." : "Measures retrieval precision against golden test set."}
          </p>
        </section>
      </div>
    </>
  );
}
