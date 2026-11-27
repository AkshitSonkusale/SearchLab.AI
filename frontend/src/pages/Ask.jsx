import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PageHeader } from "../components/AppLayout";
import { SearchIcon } from "../components/Icons";
import { suggestions } from "../data/sample";
import { api } from "../api";

export default function Ask() {
  const [q, setQ] = useState("");
  const [scope, setScope] = useState("all");
  const [docs, setDocs] = useState([]);
  const [recentHistory, setRecentHistory] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.getDocuments().then((d) => setDocs(d || [])).catch(() => {});
    api.getHistory().then((h) => setRecentHistory((h || []).slice(0, 3))).catch(() => {});
  }, []);

  const ready = docs.filter((d) => d.status === "ready");
  const passages = ready.reduce((s, d) => s + (d.passages || 0), 0);

  const ask = (question) => {
    const text = (question ?? q).trim();
    if (!text) return;
    navigate(`/answer?q=${encodeURIComponent(text)}&scope=${encodeURIComponent(scope)}`);
  };

  return (
    <>
      <PageHeader title="What do you want to know?" lead="Answers come only from your documents, and every one shows its sources." />

      <form onSubmit={(e) => { e.preventDefault(); ask(); }} className="sheet flex max-w-[880px] flex-col gap-5 px-8 py-7">
        <label htmlFor="q" className="sr-only-x">Your question</label>
        <textarea
          id="q" rows={2} value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }}
          placeholder="Ask a question about your documents"
          className="resize-none border-none bg-transparent p-0 font-serif text-[28px] leading-[1.35] focus:outline-none"
        />
        <div className="flex flex-wrap items-center gap-3 border-t border-rule pt-[18px]">
          <label htmlFor="scope" className="text-sm text-graphite">Search in</label>
          <select id="scope" value={scope} onChange={(e) => setScope(e.target.value)} className="inp pr-8">
            <option value="all">All documents ({ready.length})</option>
            {ready.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <span className="text-sm text-graphite">{passages} passages indexed</span>
          <button type="submit" className="btn ml-auto" disabled={!q.trim()}><SearchIcon />Ask</button>
        </div>
      </form>

      <div className="flex max-w-[880px] flex-wrap gap-12">
        <section className="flex flex-[1_1_340px] flex-col">
          <h2 className="mb-1.5 mt-0 text-[15px] font-semibold">Try asking</h2>
          <ul className="m-0 list-none p-0">
            {suggestions.map((s) => (
              <li key={s}>
                <button type="button" onClick={() => ask(s)}
                  className="block w-full border-0 border-t border-solid border-rule bg-transparent py-3 text-left font-serif text-[19px] text-ink transition-all hover:pl-1.5 hover:text-brand">
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </section>
        <section className="flex flex-[1_1_280px] flex-col">
          <h2 className="mb-1.5 mt-0 text-[15px] font-semibold">Recent</h2>
          {recentHistory.map((h) => (
            <Link key={h.id || h.question} to={`/answer?q=${encodeURIComponent(h.question)}`} className="row-link flex justify-between gap-3 border-t border-rule py-3 text-[15px]">
              <span className="truncate">{h.question}</span>
              <span className="whitespace-nowrap text-graphite text-xs">{h.asked_at ? new Date(h.asked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Recently"}</span>
            </Link>
          ))}
          {recentHistory.length === 0 && (
            <p className="text-sm text-graphite py-2">No past questions yet.</p>
          )}
          <Link to="/history" className="border-t border-rule py-3 text-[15px]">See all history</Link>
        </section>
      </div>
    </>
  );
}
