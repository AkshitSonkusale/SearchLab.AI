import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import Logo from "./Logo";
import { ChartIcon, DocIcon, HistoryIcon, SearchIcon, UsersIcon } from "./Icons";
import { getUser, api } from "../api";

const main = [
  { to: "/ask", label: "Ask", Icon: SearchIcon },
  { to: "/documents", label: "Documents", Icon: DocIcon },
  { to: "/history", label: "History", Icon: HistoryIcon },
];
const admin = [
  { to: "/evaluation", label: "Evaluation", Icon: ChartIcon },
  { to: "/users", label: "Users", Icon: UsersIcon },
];

function Item({ to, label, Icon }) {
  const { pathname } = useLocation();
  const alsoActive = to === "/ask" && pathname === "/answer";
  return (
    <NavLink
      to={to}
      className={({ isActive: active }) => { const isActive = active || alsoActive; return (
        `flex min-h-[44px] items-center gap-2.5 rounded-md px-3 text-[15px] no-underline transition-colors ${
          isActive
            ? "bg-white font-semibold text-brand shadow-[inset_0_0_0_1px_#D6DCD7] hover:text-brand"
            : "text-graphite hover:bg-white/65 hover:text-ink"
        }`); }
      }
    >
      <Icon />
      <span>{label}</span>
    </NavLink>
  );
}

// Grid behind the page title only, fading out by ~240px, darker to the right.
const headerGrid = {
  backgroundColor: "#EEF1EE",
  backgroundImage:
    "linear-gradient(180deg, rgba(238,241,238,0) 0px, rgba(238,241,238,0.55) 120px, rgba(238,241,238,1) 240px), linear-gradient(90deg, rgba(238,241,238,0.7) 0%, rgba(238,241,238,0) 60%), radial-gradient(circle, rgba(30,37,40,0.55) 1.3px, transparent 1.8px)",
  backgroundSize: "100% 100%, 100% 100%, 28px 28px",
  backgroundRepeat: "no-repeat, no-repeat, repeat",
};

export default function AppLayout() {
  const navigate = useNavigate();
  const currentUser = getUser();
  const isAdmin = currentUser?.role === "admin";

  const handleSignOut = async (e) => {
    e.preventDefault();
    await api.logout();
    navigate("/");
  };

  return (
    <div className="flex min-h-screen flex-wrap bg-paper text-ink">
      <nav aria-label="Main" className="flex flex-[1_1_210px] flex-col gap-7 border-r border-rule bg-[#E4E9E5] px-4 py-7">
        <div className="px-3 pb-1"><Logo size="sm" /></div>
        <div className="flex flex-col gap-0.5">{main.map((i) => <Item key={i.to} {...i} />)}</div>
        {isAdmin && (
          <div className="flex flex-col gap-0.5">
            <span className="px-3 pb-1.5 text-[13px] text-graphite">Admin</span>
            {admin.map((i) => <Item key={i.to} {...i} />)}
          </div>
        )}
        <div className="mt-auto flex flex-col gap-0.5 border-t border-rule px-2 pt-3.5">
          <span className="text-sm font-medium">{currentUser?.name || "User"}</span>
          <span className="text-xs text-graphite capitalize">{currentUser?.role || "user"}</span>
          <button type="button" onClick={handleSignOut} className="text-left text-sm text-brand hover:underline p-0 bg-transparent border-none cursor-pointer mt-1">Sign out</button>
        </div>
      </nav>
      <main className="flex min-w-0 flex-[999_1_600px] flex-col gap-7 px-6 pb-14 pt-9 sm:pl-10 sm:pr-12" style={headerGrid}>
        <Outlet />
      </main>
    </div>
  );
}

export function PageHeader({ title, lead, children }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-rule pb-5">
      <div className="flex flex-col gap-1.5">
        <h1 className="m-0 font-serif text-[34px] font-medium leading-[1.15] tracking-[-0.01em]">{title}</h1>
        {lead && <p className="m-0 text-[15px] text-graphite">{lead}</p>}
      </div>
      {children}
    </header>
  );
}
