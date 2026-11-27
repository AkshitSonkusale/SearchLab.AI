export default function SourceNote({ s, dim = false }) {
  const scoreNum = typeof s?.score === "number" && !isNaN(s.score) ? s.score : 0;
  const pct = Math.min(100, Math.max(0, Math.round(scoreNum * 100)));
  const fileName = s?.file || s?.title || s?.name || "Document";
  const location = s?.loc || "Passage";
  const contentBefore = s?.before ?? s?.text ?? "";
  const highlight = s?.hl || s?.highlight || "";
  const contentAfter = s?.after ?? "";

  return (
    <li id={`n${s?.n || 1}`} className="flex gap-3.5 border-t border-rule py-[18px] transition-colors hover:bg-white hover:shadow-[-12px_0_0_#fff,12px_0_0_#fff]">
      <span className={`min-w-[14px] font-serif text-[22px] font-semibold leading-none ${dim ? "text-graphite" : "text-brand"}`}>{s?.n || 1}</span>
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex flex-col gap-0.5">
          <span className="break-words text-sm font-semibold">{fileName}</span>
          <span className="text-[13px] text-graphite">{location}</span>
        </div>
        <p className="m-0 font-serif text-base leading-relaxed">
          “{contentBefore}{highlight && <mark className="bg-highlight px-0.5 text-ink">{highlight}</mark>}{contentAfter}”
        </p>
        <span className="flex items-center gap-2 text-[13px] text-graphite">
          Match {scoreNum.toFixed(2)}
          <span className="inline-block h-1 w-[72px] bg-rule">
            <span className={`block h-1 ${dim ? "bg-graphite" : "bg-brand"}`} style={{ width: `${pct}%` }} />
          </span>
        </span>
      </div>
    </li>
  );
}

export function SourceSkeleton() {
  return (
    <li aria-label="Loading source" className="flex flex-col gap-2 border-t border-rule py-[18px] pl-7">
      {[60, 90, 75].map((w) => <span key={w} className="block h-2.5 rounded-sm bg-rule" style={{ width: `${w}%` }} />)}
    </li>
  );
}
