import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/AppLayout";
import { api } from "../api";

export default function History() {
  const [items, setItems] = useState([]);
  const [term, setTerm] = useState("");
  const [loading, setLoading] = useState(true);

  const loadHistory = async (query = "") => {
    try {
      const data = await api.getHistory(query);
      setItems(data || []);
    } catch (e) {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory(term);
  }, [term]);

  const handleClear = async () => {
    await api.clearHistory();
    setItems([]);
  };

  return (
    <>
      <PageHeader title="History" lead="Only you can see your questions." />
      <form onSubmit={(e) => e.preventDefault()} className="flex max-w-[880px] flex-wrap gap-2.5">
        <label htmlFor="hs" className="sr-only-x">Search your history</label>
        <input id="hs" type="search" value={term} onChange={(e) => setTerm(e.target.value)} placeholder="Search your past questions" className="inp flex-[1_1_320px]" />
        <button type="button" className="btn2" onClick={handleClear} disabled={!items.length}>Clear history</button>
      </form>

      {items.length === 0 ? (
        <p className="m-0 max-w-[60ch] text-[15px] text-graphite">
          No questions yet. <Link to="/ask">Ask your first question</Link> and it will appear here.
        </p>
      ) : (
        <ul className="m-0 max-w-[1000px] list-none p-0">
          {items.map((h) => (
            <li key={h.id || h.question}>
              <Link to={`/answer?q=${encodeURIComponent(h.question)}`} className="row-link flex flex-wrap gap-x-6 gap-y-2 border-t border-rule py-5">
                <div className="flex min-w-0 flex-[1_1_420px] flex-col gap-1.5">
                  <span className="font-serif text-[21px] font-medium">{h.question}</span>
                  <span className="text-[15px] leading-relaxed text-graphite line-clamp-2">{h.answer}</span>
                </div>
                <div className="flex flex-[0_0_160px] flex-col gap-1.5 text-sm">
                  <span className="text-graphite">{h.asked_at ? new Date(h.asked_at).toLocaleDateString() : "Recent"}</span>
                  <span className={`font-medium ${h.found ? "text-brand" : "text-[#7A4E00]"}`}>
                    {h.found ? `${(h.sources || []).length || 1} sources` : "Not found"}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
