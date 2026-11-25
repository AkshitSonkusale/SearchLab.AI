import { useEffect, useRef } from "react";

// Interactive dot grid used behind the Sign in / Create account pages.
// Static dots come from CSS (always visible); the canvas adds the idle wave,
// hover lens, highlighted cell and click ripple on top.
const SPACING = 28;
const PAPER = "238,241,238";

export default function GridBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvas.parentElement;
    const ctx = canvas.getContext("2d");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const t0 = performance.now();
    let W = 0, H = 0, raf = 0;
    let mouse = null, smooth = null;
    let ripples = [];

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      const d = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.round(r.width * d));
      canvas.height = Math.max(1, Math.round(r.height * d));
      ctx.setTransform(d, 0, 0, d, 0, 0);
      W = r.width; H = r.height;
      draw(performance.now());
    };

    const draw = (now) => {
      const S = SPACING, t = (now - t0) / 1000, R = 170;
      if (mouse) {
        if (!smooth) smooth = { ...mouse };
        smooth.x += (mouse.x - smooth.x) * 0.18;
        smooth.y += (mouse.y - smooth.y) * 0.18;
      }
      const m = mouse ? smooth : null;
      ripples = ripples.filter((r) => now - r.t < 1600);
      ctx.clearRect(0, 0, W, H);
      const ox = S / 2, oy = S / 2;

      for (let y = oy; y <= H; y += S) {
        for (let x = ox; x <= W; x += S) {
          let k = 0, px = x, py = y;
          if (m) {
            const dx = x - m.x, dy = y - m.y, d = Math.hypot(dx, dy);
            if (d < R) {
              k = 1 - d / R; k = k * k * (3 - 2 * k);
              if (d > 0.5) { px += (dx / d) * k * 3; py += (dy / d) * k * 3; }
            }
          }
          for (const r of ripples) {
            const rad = ((now - r.t) / 1600) * 520;
            const d = Math.hypot(x - r.x, y - r.y);
            const band = Math.max(0, 1 - Math.abs(d - rad) / 34) * (1 - (now - r.t) / 1600);
            k = Math.max(k, band);
          }
          const wave = reduce ? 0 : Math.pow((Math.sin(x * 0.012 + y * 0.008 - t * 0.9) + 1) * 0.5, 4);
          if (k < 0.02 && wave < 0.08) continue;
          const size = 1.5 + wave * 0.8 + k * 2.6;
          const a = Math.min(1, wave * 0.55 * (0.15 + (0.85 * x) / W) + k * 0.85);
          const kk = Math.max(k, 0.7);
          const rr = Math.round(86 + (29 - 86) * kk), g = Math.round(96 + (91 - 96) * kk), b = Math.round(100 + (71 - 100) * kk);
          ctx.fillStyle = `rgba(${rr},${g},${b},${a.toFixed(3)})`;
          if (k > 0.55) {
            const s = size * 1.6;
            ctx.fillRect(px - s / 2, py - s / 2, s, s);
          } else {
            ctx.beginPath(); ctx.arc(px, py, size, 0, Math.PI * 2); ctx.fill();
          }
        }
      }
      if (m) {
        const cx = Math.round((m.x - ox) / S) * S + ox, cy = Math.round((m.y - oy) / S) * S + oy;
        ctx.strokeStyle = "rgba(29,91,71,0.55)"; ctx.lineWidth = 1;
        ctx.strokeRect(cx - S / 2 + 0.5, cy - S / 2 + 0.5, S - 1, S - 1);
        ctx.fillStyle = "rgba(245,226,124,0.55)";
        ctx.fillRect(cx - S / 2 + 1, cy - S / 2 + 1, S - 2, S - 2);
      }
    };

    const pos = (e) => {
      const r = canvas.getBoundingClientRect();
      return { x: e.clientX - r.left, y: e.clientY - r.top };
    };
    const onMove = (e) => { mouse = pos(e); if (reduce) { smooth = mouse; draw(performance.now()); } };
    const onLeave = () => { mouse = null; smooth = null; if (reduce) draw(performance.now()); };
    const onDown = (e) => { if (!reduce) ripples.push({ ...pos(e), t: performance.now() }); };

    host.addEventListener("pointermove", onMove);
    host.addEventListener("pointerleave", onLeave);
    host.addEventListener("pointerdown", onDown);
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();
    if (!reduce) {
      const loop = (now) => { draw(now); raf = requestAnimationFrame(loop); };
      raf = requestAnimationFrame(loop);
    }
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      host.removeEventListener("pointermove", onMove);
      host.removeEventListener("pointerleave", onLeave);
      host.removeEventListener("pointerdown", onDown);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 h-full w-full"
    />
  );
}

// Static dot grid + left-to-right fade. Apply to the page wrapper.
export const gridStyle = {
  backgroundColor: `rgb(${PAPER})`,
  backgroundImage: `linear-gradient(90deg, rgba(${PAPER},0.95) 0%, rgba(${PAPER},0.8) 30%, rgba(${PAPER},0.35) 65%, rgba(${PAPER},0) 100%), radial-gradient(circle, rgba(30,37,40,0.7) 1.4px, transparent 1.9px)`,
  backgroundSize: `100% 100%, ${SPACING}px ${SPACING}px`,
};
