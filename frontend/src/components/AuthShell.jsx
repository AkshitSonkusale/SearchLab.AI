import GridBackground, { gridStyle } from "./GridBackground";
import Logo from "./Logo";

// Shared layout for Sign in and Create account: pitch on the left, floating card on the right.
export default function AuthShell({ children }) {
  return (
    <div className="relative min-h-screen overflow-hidden text-ink" style={gridStyle}>
      <GridBackground />
      <div className="relative mx-auto flex min-h-screen max-w-[1280px] flex-wrap items-stretch gap-x-20 gap-y-12 px-6 py-12 sm:px-16">
        <div className="flex flex-[1_1_460px] flex-col gap-12">
          <Logo />
          <div className="my-auto flex max-w-[540px] flex-col gap-10">
            <div className="flex w-max max-w-full flex-col gap-[18px]">
              <h1 className="m-0 font-serif text-[40px] font-medium leading-[1.02] tracking-[-0.028em] sm:text-[56px]">
                <span className="block">Get answers from</span>
                <span className="block">your own documents.</span>
              </h1>
              <p className="m-0 w-0 min-w-full font-serif text-[22px] leading-[1.45] text-graphite">
                Every answer comes with the page it came from, so you can check it yourself.
              </p>
            </div>
            <figure className="sheet m-0 flex flex-col gap-3.5 px-[30px] py-7">
              <p className="m-0 text-sm text-graphite">You asked</p>
              <p className="m-0 font-serif text-[21px] font-medium">How much paid leave do interns get?</p>
              <p className="m-0 font-serif text-lg leading-[1.65]">
                Interns get 1.5 days of paid leave for every month of their internship.
                <sup className="px-px text-xs font-semibold text-brand">1</sup>
              </p>
              <figcaption className="border-t border-rule pt-3 text-sm leading-relaxed text-graphite">
                <span className="font-semibold text-brand">1</span> Intern_Handbook_2026.pdf, page 12: “Interns are entitled to{" "}
                <mark className="bg-highlight px-0.5 text-ink">1.5 days of paid leave per month</mark> of internship.”
              </figcaption>
            </figure>
          </div>
        </div>
        <div className="flex flex-[0_1_420px] items-center justify-center">
          <div className="w-full max-w-[400px] rounded-[10px] border border-rule bg-white px-9 pb-8 pt-9 shadow-[0_1px_2px_rgba(30,37,40,0.06),0_18px_40px_rgba(30,37,40,0.10)]">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}

export function Field({ label, ...props }) {
  return (
    <label className="flex flex-col gap-1.5 text-sm font-medium">
      {label}
      <input className="inp" {...props} />
    </label>
  );
}

export function FormError({ children }) {
  if (!children) return null;
  return <p role="alert" className="m-0 rounded-md bg-[#FBEDEB] px-3 py-2 text-sm text-[#8A2E25]">{children}</p>;
}
