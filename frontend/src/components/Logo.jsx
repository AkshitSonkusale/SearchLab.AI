export default function Logo({ size = "lg" }) {
  const big = size === "lg";
  return (
    <span className="flex items-center gap-2.5">
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#1D5B47" strokeLinecap="round" aria-hidden="true" className="block flex-none">
        <circle cx="12" cy="12" r="10.6" strokeWidth="1.5" />
        <circle cx="13.7" cy="10.2" r="3.5" strokeWidth="1.5" />
        <path d="M10.95 12.95 L11.8 12.1" strokeWidth="0.8" />
        <path d="M10.5 13.4 L7.9 16" strokeWidth="1.9" />
      </svg>
      <span
        className={`font-serif font-semibold leading-none tracking-[-0.015em] relative ${big ? "text-[30px] top-[3px]" : "text-[25px] top-[2px]"}`}
      >
        SearchLab.AI
      </span>
    </span>
  );
}
