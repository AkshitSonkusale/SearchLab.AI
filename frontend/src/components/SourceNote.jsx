export default function SourceNote({ s, dim = false }) {
  const pct = Math.round(s.score * 100);
  return (
    <li id={`n${s.n}`} className="flex gap-3.5 border-t border-rule py-[18px] transition-colors hover:bg-white hover:shadow-[-12px_0_0_#fff,12px_0_0_#fff]">
      <span className={`min-w-[14px] font-serif text-[22px] font-semibold leading-none ${dim ? "text-graphite" : "text-brand"}`}>{s.n}</span>
      <div className="flex min-w-0 flex-col gap-2">
        <div className="flex flex-col gap-0.5">
          <span className="break-words text-sm font-semibold">{s.file}</span>
          <span className="text-[13px] text-graphite">{s.loc}</span>
        </div>
        <p className="m-0 font-serif text-base leading-relaxed">
          “{s.before}{s.hl && <mark className="bg-highlight px-0.5 text-ink">{s.hl}</mark>}{s.after}”
        </p>
        <span className="flex items-center gap-2 text-[13px] text-graphite">
          Match {s.score.toFixed(2)}
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
