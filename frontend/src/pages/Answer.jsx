import { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { PageHeader } from "../components/AppLayout";
import { UploadIcon } from "../components/Icons";
import SourceNote, { SourceSkeleton } from "../components/SourceNote";
import { api } from "../api";

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
  const question = params.get("q") || "";
  const scope = params.get("scope") || "all";
  const [draft, setDraft] = useState(question);

  const [sources, setSources] = useState([]);
  const [answer, setAnswer] = useState("");
  const [streaming, setStreaming] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [questionId, setQuestionId] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [copied, setCopied] = useState(false);
  const [errorNotice, setErrorNotice] = useState("");
  const [conflicts, setConflicts] = useState([]);

  useEffect(() => {
    if (!question) return;
    setDraft(question);
    setSources([]);
    setAnswer("");
    setStreaming(true);
    setNotFound(false);
    setFeedback(null);
    setErrorNotice("");
    setConflicts([]);

    const docIds = scope && scope !== "all" ? [scope] : null;

    api.askStream(
      question,
      docIds,
      (srcs) => {
        setSources(srcs || []);
      },
      (token) => {
        setAnswer((prev) => prev + token);
      },
      (doneData) => {
        setStreaming(false);
        if (doneData.found === false || doneData.answer?.includes("isn't in your documents")) {
          setNotFound(true);
        }
        if (doneData.question_id) {
          setQuestionId(doneData.question_id);
        }
        if (doneData.conflicts && doneData.conflicts.length) {
          setConflicts(doneData.conflicts);
        }
      },
      (err) => {
        setStreaming(false);
        setErrorNotice(err.message || "An error occurred while generating the answer.");
      }
    );
  }, [question, scope]);

  const ask = (e) => {
    e.preventDefault();
    if (draft.trim()) navigate(`/answer?q=${encodeURIComponent(draft.trim())}&scope=${encodeURIComponent(scope)}`);
  };

  const handleFeedback = async (helpful) => {
    setFeedback(helpful ? "yes" : "no");
    if (questionId) {
      await api.submitFeedback(questionId, helpful).catch(() => {});
    }
  };

  // Render text with clickable citations [1], [2]
  const renderFormattedAnswer = (text) => {
    if (!text) return null;
    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, i) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        return <Cite key={i} n={match[1]} />;
      }
      return <span key={i}>{part}</span>;
    });
  };

  const transformedSources = sources.map((s, idx) => {
    const rawScore = typeof s.score === "number" ? s.score : (typeof s.match === "number" ? s.match : 0);
    const scoreVal = isNaN(rawScore) ? 0 : rawScore;
    const file = s.file || s.name || s.document_name || "Document";
    const loc = s.loc || (s.page_number ? `Page ${s.page_number}` : (s.page ? `Page ${s.page}` : "Relevant passage"));
    const text = s.text || "";
    const hl = s.hl || s.highlight || s.evidence_sentence || "";

    return {
      n: s.n || s.passage_id || (idx + 1),
      file,
      loc,
      score: scoreVal,
      before: s.before !== undefined ? s.before : text,
      hl,
      after: s.after !== undefined ? s.after : "",
    };
  });

  return (
    <>
      <PageHeader
        title="Answer"
        lead={!notFound ? "Highlighted text in each source is what the answer relies on." : "Answers require matching document passages."}
      >
        <Link to="/ask" className="text-[15px]">New question</Link>
      </PageHeader>

      <form onSubmit={ask} className="flex max-w-[880px] flex-wrap gap-2.5">
        <label htmlFor="q2" className="sr-only-x">Your question</label>
        <input id="q2" value={draft} onChange={(e) => setDraft(e.target.value)} className="inp flex-[1_1_360px] font-serif text-lg" />
        <button type="submit" className="btn">Ask</button>
      </form>

      {errorNotice && (
        <div className="sheet max-w-[880px] p-4 text-[#8A2E25] bg-[#FDF2F1] rounded">
          {errorNotice}
        </div>
      )}

      <div className="flex flex-wrap items-start gap-10">
        <article className="sheet flex min-w-0 flex-[3_1_520px] flex-col gap-[22px] px-6 py-8 sm:px-12 sm:py-10">
          <h2 className="m-0 font-serif text-[32px] font-medium leading-[1.2] tracking-[-0.01em]">{question}</h2>

          {!notFound ? (
            <>
              <p role="status" className="m-0 text-sm text-graphite">
                {streaming ? "Synthesizing answer from retrieved passages..." : `${transformedSources.length} passages cited`}
              </p>

              {conflicts.length > 0 && (
                <div className="rounded bg-[#FBF3D9] p-4 text-[#5C3D00] text-sm">
                  <strong>Policy Discrepancy Detected:</strong> Sources contain divergent statements on this subject. Review the cited sources below.
                </div>
              )}

              <div className="flex max-w-[62ch] flex-col gap-4 font-serif text-xl leading-[1.75]">
                <p className="m-0 whitespace-pre-wrap">
                  {renderFormattedAnswer(answer)}
                  {streaming && (
                    <span className="caret ml-[3px] inline-block h-[22px] w-[9px] bg-brand align-[-4px]" />
                  )}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5 border-t border-rule pt-5">
                {!streaming ? (
                  <>
                    <span className="text-[15px] text-graphite">
                      {feedback ? "Thanks, your feedback is saved." : "Did this answer your question?"}
                    </span>
                    <button type="button" aria-pressed={feedback === "yes"} onClick={() => handleFeedback(true)}
                      className={`btn2 ${feedback === "yes" ? "border-brand text-brand" : ""}`}>Yes</button>
                    <button type="button" aria-pressed={feedback === "no"} onClick={() => handleFeedback(false)}
                      className={`btn2 ${feedback === "no" ? "border-brand text-brand" : ""}`}>No</button>
                    <button type="button" className="btn2 ml-auto border-transparent text-brand"
                      onClick={() => { navigator.clipboard?.writeText(answer); setCopied(true); setTimeout(() => setCopied(false), 1500); }}>
                      {copied ? "Copied" : "Copy answer"}
                    </button>
                  </>
                ) : (
                  <span className="text-sm text-graphite">Streaming live from Groq...</span>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="flex flex-col gap-3 rounded-md bg-[#FBF3D9] px-6 py-[22px] text-[#5C3D00]">
                <p className="m-0 font-serif text-[22px] font-medium">This isn’t in your documents.</p>
                <p className="m-0 max-w-[60ch] text-base leading-relaxed">
                  SearchLab.AI answers strictly from your uploaded files and will not fabricate or hallucinate facts.
                  The closest passages are listed alongside, but none matched the relevance threshold.
                </p>
              </div>
              <div className="flex flex-wrap gap-2.5">
                <Link to="/documents" className="btn"><UploadIcon />Upload a document</Link>
                <Link to="/ask" className="btn2">Rephrase the question</Link>
              </div>
            </>
          )}
        </article>

        <aside aria-label={!notFound ? "Sources" : "Closest passages"} className="flex min-w-0 flex-[1_1_280px] flex-col">
          <h2 className="mb-1 mt-0 text-[15px] font-semibold">{!notFound ? "Sources" : "Closest passages"}</h2>
          <p className="mb-2.5 mt-0 text-sm text-graphite">
            {!notFound ? `${transformedSources.length} passages retrieved` : "Below the match threshold"}
          </p>
          <ol className="m-0 list-none p-0">
            {transformedSources.map((s) => <SourceNote key={s.n} s={s} dim={notFound} />)}
            {streaming && transformedSources.length === 0 && <SourceSkeleton />}
          </ol>
        </aside>
      </div>
    </>
  );
}
