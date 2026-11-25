import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "../components/AppLayout";
import { UploadIcon } from "../components/Icons";
import SourceNote, { SourceSkeleton } from "../components/SourceNote";
import { documents, notFound, sampleAnswer } from "../data/sample";

// Demo logic: questions about leave get the sample answer (streamed in),
// anything else shows the "not in your documents" state.
// Replace with: POST /ask → stream answer tokens + sources (SSE).
const isAnswerable = (q) => /leave|intern/i.test(q);

function Cite({ n }) {
  return (
    <a href={`#n${n}`} aria-label={`Source ${n}`}
      className="px-px align-super text-xs font-semibold leading-none text-brand no-underline transition-colors hover:rounded-sm hover:bg-highlight">
      {n}
    </a>
  );
}

export default function Answer() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const question = params.get("q") || sampleAnswer.question;
  const [draft, setDraft] = useState(question);
  const answerable = isAnswerable(question);

  // Flatten the answer into word / citation tokens so it can be revealed progressively.
  const tokens = useMemo(() => {
    const out = [];
    sampleAnswer.paragraphs.forEach((para, p) =>
      para.forEach(([text, n]) => {
        text.split(/(?<= )/).forEach((w) => out.push({ p, w }));
        out.push({ p, n });
      })
    );
    return out;
  }, []);

  const [shown, setShown] = useState(0);
  const [feedback, setFeedback] = useState(null);
  const [copied, setCopied] = useState(false);
  const streaming = answerable && shown < tokens.length;

  useEffect(() => {
    setDraft(question); setShown(0); setFeedback(null);
    if (!answerable) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) { setShown(tokens.length); return; }
    const id = setInterval(() => setShown((s) => (s >= tokens.length ? s : s + 1)), 45);
    return () => clearInterval(id);
  }, [question, answerable, tokens.length]);

  const sourcesShown = streaming ? Math.min(3, 1 + Math.floor((shown / tokens.length) * 3)) : 3;
  const paragraphs = sampleAnswer.paragraphs.map((_, p) => tokens.slice(0, shown).filter((t) => t.p === p)).filter((p) => p.length);
  const plainAnswer = tokens.filter((t) => t.w).map((t) => t.w).join("");

  const ask = (e) => {
    e.preventDefault();
    if (draft.trim()) navigate(`/answer?q=${encodeURIComponent(draft.trim())}`);
  };

  return (
    <>
      <PageHeader
        title="Answer"
        lead={answerable ? "Highlighted text in each source is what the answer relies on." : `Answers need a passage with a match of ${notFound.threshold} or higher.`}
      >
        <Link to="/ask" className="text-[15px]">New question</Link>
      </PageHeader>

      <form onSubmit={ask} className="flex max-w-[880px] flex-wrap gap-2.5">
        <label htmlFor="q2" className="sr-only-x">Your question</label>
        <input id="q2" value={draft} onChange={(e) => setDraft(e.target.value)} className="inp flex-[1_1_360px] font-serif text-lg" />
        <button type="submit" className="btn">Ask</button>
      </form>

      <div className="flex flex-wrap items-start gap-10">
        <article className="sheet flex min-w-0 flex-[3_1_520px] flex-col gap-[22px] px-6 py-8 sm:px-12 sm:py-10">
          <h2 className="m-0 font-serif text-[32px] font-medium leading-[1.2] tracking-[-0.01em]">{question}</h2>

          {answerable ? (
            <>
              <p role="status" className="m-0 text-sm text-graphite">
                {streaming ? "Writing the answer from 3 passages" : sampleAnswer.meta}
              </p>
              <div className="flex max-w-[62ch] flex-col gap-4 font-serif text-xl leading-[1.75]">
                {paragraphs.map((toks, i) => (
                  <p key={i} className="m-0">
                    {toks.map((t, j) => (t.n ? <Cite key={j} n={t.n} /> : <span key={j}>{t.w}</span>))}
                    {streaming && i === paragraphs.length - 1 && (
                      <span className="caret ml-[3px] inline-block h-[22px] w-[9px] bg-brand align-[-4px]" />
                    )}
                  </p>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-2.5 border-t border-rule pt-5">
                {streaming ? (
                  <button type="button" className="btn2" onClick={() => setShown(tokens.length)}>Stop generating</button>
                ) : (
                  <>
                    <span className="text-[15px] text-graphite">
                      {feedback ? "Thanks, your feedback is saved." : "Did this answer your question?"}
                    </span>
                    <button type="button" aria-pressed={feedback === "yes"} onClick={() => setFeedback("yes")}
                      className={`btn2 ${feedback === "yes" ? "border-brand text-brand" : ""}`}>Yes</button>
                    <button type="button" aria-pressed={feedback === "no"} onClick={() => setFeedback("no")}
                      className={`btn2 ${feedback === "no" ? "border-brand text-brand" : ""}`}>No</button>
                    <button type="button" className="btn2 ml-auto border-transparent text-brand"
                      onClick={() => { navigator.clipboard?.writeText(plainAnswer); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
                      {copied ? "Copied" : "Copy answer"}
                    </button>
                  </>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="flex flex-col gap-3 rounded-md bg-[#FBF3D9] px-6 py-[22px] text-[#5C3D00]">
                <p className="m-0 font-serif text-[22px] font-medium">This isn’t in your documents.</p>
                <p className="m-0 max-w-[60ch] text-base leading-relaxed">
                  None of your {documents.filter((d) => d.status === "ready").length} documents cover this. SearchLab.AI only answers from your files, so it won’t guess.
                  The closest passages are listed alongside, but none match well enough to answer.
                </p>
              </div>
              <div className="flex flex-wrap gap-2.5">
                <Link to="/documents" className="btn"><UploadIcon />Upload a document</Link>
                <Link to="/ask" className="btn2">Rephrase the question</Link>
              </div>
            </>
          )}
        </article>

        <aside aria-label={answerable ? "Sources" : "Closest passages"} className="flex min-w-0 flex-[1_1_280px] flex-col">
          <h2 className="mb-1 mt-0 text-[15px] font-semibold">{answerable ? "Sources" : "Closest passages"}</h2>
          <p className="mb-2.5 mt-0 text-sm text-graphite">
            {answerable ? (streaming ? "Finding passages" : "3 passages, best match first") : "Below the match threshold, so not used"}
          </p>
          <ol className="m-0 list-none p-0">
            {answerable
              ? <>
                  {sampleAnswer.sources.slice(0, sourcesShown).map((s) => <SourceNote key={s.n} s={s} />)}
                  {streaming && sourcesShown < 3 && <SourceSkeleton />}
                </>
              : notFound.closest.map((s) => <SourceNote key={s.n} s={s} dim />)}
          </ol>
        </aside>
      </div>
    </>
  );
}
