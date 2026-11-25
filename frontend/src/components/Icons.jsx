const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true };
const I = ({ size = 18, children }) => <svg width={size} height={size} viewBox="0 0 24 24" {...base}>{children}</svg>;

export const SearchIcon = (p) => <I {...p}><circle cx="11" cy="11" r="7" /><path d="M20 20l-3.5-3.5" /></I>;
export const DocIcon = (p) => <I {...p}><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6" /></I>;
export const HistoryIcon = (p) => <I {...p}><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 3" /></I>;
export const ChartIcon = (p) => <I {...p}><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M22 20H2" /></I>;
export const UsersIcon = (p) => <I {...p}><circle cx="9" cy="8" r="4" /><path d="M2 21c0-4 3-6 7-6s7 2 7 6" /><path d="M17 4a4 4 0 0 1 0 8" /><path d="M22 21c0-3-1.5-5-4-5.7" /></I>;
export const UploadIcon = (p) => <I {...p}><path d="M12 16V4" /><path d="M7 9l5-5 5 5" /><path d="M4 20h16" /></I>;
