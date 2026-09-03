"""Static page generator for the zeta-zeros diffraction bridge (no external libraries).

``write_page(data, path)`` embeds the output of :func:`research.quasicrystal_bridge.build_bridge`
into a self-contained HTML page with two inline-SVG charts and their tables.
"""
from __future__ import annotations

import json
from pathlib import Path

TEMPLATE = r"""<title>Diffraction of the Zeta Zeros</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --bg:#f4f5f9; --surface:#ffffff; --ink:#141a2a; --muted:#5b6479; --rule:#d6dae6; --grid:#e6e9f0;
  --zeta:#0a8fa8; --gold:#9a6b12; --zeta-soft:rgba(10,143,168,.14); --gold-soft:rgba(154,107,18,.14);
  --tip-bg:#141a2a; --tip-ink:#f4f5f9; color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#0e1220; --surface:#161b2e; --ink:#e8ebf3; --muted:#9aa3bd; --rule:#2a3350; --grid:#212940;
    --zeta:#1f9bb1; --gold:#bd8622; --zeta-soft:rgba(31,155,177,.18); --gold-soft:rgba(189,134,34,.18);
    --tip-bg:#e8ebf3; --tip-ink:#0e1220; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0e1220; --surface:#161b2e; --ink:#e8ebf3; --muted:#9aa3bd; --rule:#2a3350; --grid:#212940;
  --zeta:#1f9bb1; --gold:#bd8622; --zeta-soft:rgba(31,155,177,.18); --gold-soft:rgba(189,134,34,.18);
  --tip-bg:#e8ebf3; --tip-ink:#0e1220; color-scheme:dark;
}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:16px;line-height:1.55;-webkit-text-size-adjust:100%}
.page{max-width:960px;margin:0 auto;padding:32px 20px 72px;display:flex;flex-direction:column;gap:48px}
.prose{max-width:68ch}
h1,h2{font-family:"Newsreader",Georgia,"Times New Roman",serif;font-weight:600;text-wrap:balance;margin:0;letter-spacing:-.01em}
h1{font-size:clamp(34px,6vw,54px);line-height:1.05}
h2{font-size:clamp(24px,3.6vw,32px);line-height:1.15}
p{margin:0}
.eyebrow{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.hero{display:flex;flex-direction:column;gap:18px}
.lede{font-family:"Newsreader",Georgia,serif;font-size:clamp(19px,2.4vw,23px);line-height:1.4;max-width:60ch}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:8px 0 0}
.stats div{border-top:2px solid var(--rule);padding-top:8px}
.stats dt{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:0}
.stats dd{margin:2px 0 0;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:20px;font-variant-numeric:tabular-nums}
section{display:flex;flex-direction:column;gap:18px}
figure{margin:0;display:flex;flex-direction:column;gap:10px}
.chart-wrap{background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:8px 6px 4px;overflow-x:auto;position:relative}
svg{display:block;width:100%;height:auto;font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px}
figcaption{color:var(--muted);font-size:14px;max-width:72ch}
.legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);padding:0 4px}
.legend span::before{content:"";display:inline-block;width:14px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle;background:var(--sw)}
.table-wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:7px 12px;text-align:right;border-bottom:1px solid var(--rule);white-space:nowrap}
th{font-weight:500;color:var(--muted);font-size:12px;letter-spacing:.04em;text-transform:uppercase}
td:first-child,th:first-child{text-align:left;font-family:"IBM Plex Mono",ui-monospace,monospace}
tr:last-child td{border-bottom:none}
.formula{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:14px;background:var(--surface);border-left:3px solid var(--zeta);padding:12px 16px;overflow-x:auto;white-space:nowrap}
.formula.gold{border-left-color:var(--gold)}
.verdict{border:1px solid var(--rule);border-radius:6px;padding:20px 22px;background:var(--surface);display:grid;gap:14px}
.verdict p strong{font-weight:600}
.tip{position:absolute;pointer-events:none;background:var(--tip-bg);color:var(--tip-ink);font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;padding:6px 8px;border-radius:4px;white-space:nowrap;transform:translate(-50%,-115%);display:none;z-index:2}
.tip[data-on="1"]{display:block}
a{color:var(--zeta);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,button:focus-visible{outline:2px solid var(--zeta);outline-offset:2px}
.sources{font-size:14px;color:var(--muted);display:grid;gap:6px;max-width:72ch}
.sources li{margin:0}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
</style>

<main class="page">
  <header class="hero">
    <p class="eyebrow">Landau 1911 · Odlyzko's zeros · Dyson's quasicrystal picture</p>
    <h1>The zeta zeros diffract into the primes</h1>
    <p class="lede">Take the first hundred thousand zeros of the Riemann zeta function, add up cosines, and the primes appear as sharp lines at their logarithms. Next to it, a golden quasicrystal does the same trick with a different alphabet. The comparison shows exactly how far Dyson's road toward the Riemann Hypothesis goes, and where it stops.</p>
    <dl class="stats">
      <div><dt>Zeros used</dt><dd id="s-zeros">–</dd></div>
      <div><dt>Height T</dt><dd id="s-T">–</dd></div>
      <div><dt>Prime-power lines checked</dt><dd id="s-peaks">–</dd></div>
      <div><dt>Worst relative error</dt><dd id="s-err">–</dd></div>
    </dl>
  </header>

  <section id="zeta">
    <h2>1. The zeros as a crystal</h2>
    <p class="prose">Write each zero as ρ = ½ + iγ. Landau proved in 1911 that summing x<sup>ρ</sup> over the zeros up to height T picks out the prime powers: the sum is −(T/2π)·Λ(x) plus a small error, where Λ(x) = log p when x = p<sup>k</sup> and 0 otherwise. Written as a cosine sum in the variable u = log x, that is a diffraction pattern.</p>
    <div class="formula">F(u) = Σ<sub>γ ≤ T</sub> cos(γ u)  ≈  −(T/2π) · Λ(n)/√n   at u = log n,   noise of size √T elsewhere</div>
    <figure>
      <div class="legend"><span style="--sw:var(--zeta)">F(u) normalised by T/2π</span><span style="--sw:var(--ink)">Landau's predicted depth −Λ(n)/√n</span></div>
      <div class="chart-wrap" id="zeta-wrap"><svg id="zeta-chart" viewBox="0 0 960 400" role="img" aria-label="Diffraction pattern of the zeta zeros: sharp downward lines at the logarithms of prime powers"></svg><div class="tip" id="zeta-tip"></div></figure>
      <figcaption>Each downward line sits at u = log n for a prime power n, labelled by n. The lines are about 5·10⁻⁵ wide in u, so the chart samples them exactly at log n; between lines the sum is noise. Hover or tap to read a point.</figcaption>
    </figure>
    <div class="table-wrap"><table id="zeta-table"><thead><tr><th>n</th><th>log n</th><th>predicted −Λ(n)/√n</th><th>measured</th><th>relative error</th></tr></thead><tbody></tbody></table></div>
  </section>

  <section id="fib">
    <h2>2. A golden quasicrystal for comparison</h2>
    <p class="prose">Lay tiles of length φ and 1 in the order of the Fibonacci word (L → LS, S → L). Every vertex lands in Z + Zφ, the set is aperiodic, and its diffraction is pure point: Bragg peaks at k = 2π(m + nφ)/√5, the dual module of Z[φ]. The bright peaks are the ones whose conjugate m + nφ̄ is small, which is why the Fibonacci index pairs (1, 1), (1, 2), (2, 3) dominate.</p>
    <div class="formula gold">I(k) = |Σ<sub>j</sub> e<sup>i k x<sub>j</sub></sup>|² / N²   with peaks at   k = 2π (m + n φ) / √5</div>
    <figure>
      <div class="legend"><span style="--sw:var(--gold)">Bragg peaks, sampled exactly on the module</span><span style="--sw:var(--muted)">uniform grid between peaks (noise floor)</span></div>
      <div class="chart-wrap" id="fib-wrap"><svg id="fib-chart" viewBox="0 0 960 400" role="img" aria-label="Diffraction of the Fibonacci chain: Bragg peaks on the golden module"></svg><div class="tip" id="fib-tip"></div></div>
      <figcaption>Log scale. Stems mark the exact positions 2π(m + nφ)/√5 with their measured intensity per point; the faint trace is a uniform grid of k values, which misses every peak because the peaks are narrower than any grid. Labels give (m, n).</figcaption>
    </figure>
    <div class="table-wrap"><table id="fib-table"><thead><tr><th>(m, n)</th><th>k</th><th>intensity per point</th><th>|m + nφ̄|</th></tr></thead><tbody></tbody></table></div>
  </section>

  <section id="verdict">
    <h2>3. Where Dyson's road ends</h2>
    <div class="verdict">
      <p><strong>What the two pictures share.</strong> Both point sets are aperiodic and both have a discrete spectrum: the Fibonacci chain diffracts onto the golden module, the zeros onto the logarithms of prime powers. This is the observation behind Dyson's 2009 suggestion that the zeros form a one-dimensional quasicrystal and that classifying such quasicrystals would prove the Riemann Hypothesis.</p>
      <p><strong>What has happened since.</strong> Kurasov and Sarnak built one-dimensional Fourier quasicrystals from Lee–Yang polynomials, and Olevskii–Ulanovskii and Alon–Cohen–Vinzant proved that this construction gives all of them with integer weights. The classification Dyson asked for was, in that sense, carried out.</p>
      <p><strong>Why it did not reach RH.</strong> The Fibonacci chain is uniformly discrete: its points keep a minimum distance. The zeros are not: their density grows like log T, visible above as lines that keep coming without bound. They fall outside the classified class, and whether they form a crystalline measure at all is equivalent to the Riemann Hypothesis itself. The paved road ends at a different destination; the remaining step is new mathematics no one has.</p>
    </div>
  </section>

  <section id="method">
    <h2>Method and sources</h2>
    <ul class="sources">
      <li>Zeros: A. M. Odlyzko, table zeros1 (first 100 000 zeros, 9 decimals). Sum computed exactly at u = log n and on a uniform grid; predictions from Landau's theorem with T the largest zero used.</li>
      <li>Fibonacci chain: 4 000 tiles; intensities evaluated at the module positions 2π(m + nφ)/√5 for |m|, |n| ≤ 8 and on a uniform grid of 3 000 points.</li>
      <li>E. Landau, Über die Nullstellen der Zetafunktion, Math. Ann. 71 (1912). F. Dyson, Birds and frogs, Notices AMS 56 (2009). P. Kurasov and P. Sarnak, Stable polynomials and crystalline measures, J. Math. Phys. 61 (2020). L. Alon, A. Cohen and C. Vinzant, arXiv:2303.03201 (2023). V. Elser, Indexing problems in quasicrystal diffraction, Phys. Rev. B 32 (1985).</li>
      <li>Code: research/quasicrystal_bridge.py and tests/test_quasicrystal_bridge.py in the optimus-prime-triangle repository. Nothing on this page is new mathematics.</li>
    </ul>
  </section>
</main>

<script>
const DATA = __DATA__;
const PHI = (1 + Math.sqrt(5)) / 2;
const fmt = (x, d) => Number(x).toLocaleString("en-US", {minimumFractionDigits: d, maximumFractionDigits: d});
const svgNS = "http://www.w3.org/2000/svg";
function el(name, attrs, text){ const e = document.createElementNS(svgNS, name); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text !== undefined) e.textContent = text; return e; }

// ---------- stats
document.getElementById("s-zeros").textContent = DATA.n_zeros.toLocaleString("en-US");
document.getElementById("s-T").textContent = fmt(DATA.T, 1);
document.getElementById("s-peaks").textContent = DATA.zeta_peaks.length;
document.getElementById("s-err").textContent = fmt(100 * Math.max(...DATA.zeta_peaks.map(r => r.rel_err)), 2) + " %";

// ---------- zeta chart
(function(){
  const svg = document.getElementById("zeta-chart"), tip = document.getElementById("zeta-tip");
  const W = 960, H = 400, L = 54, R = 16, T = 18, B = 44;
  const xmin = 0, xmax = 4.5, ymin = -0.85, ymax = 0.3;
  const sx = u => L + (u - xmin) / (xmax - xmin) * (W - L - R);
  const sy = v => T + (ymax - v) / (ymax - ymin) * (H - T - B);
  const ink = "var(--ink)", muted = "var(--muted)", grid = "var(--grid)";
  for (let v = -0.8; v <= 0.3001; v += 0.2){ const y = sy(v); svg.appendChild(el("line", {x1: L, x2: W - R, y1: y, y2: y, stroke: grid, "stroke-width": 1})); svg.appendChild(el("text", {x: L - 8, y: y + 4, "text-anchor": "end", fill: muted}, fmt(v, 1))); }
  for (let u = 0; u <= 4.5001; u += 0.5){ const x = sx(u); svg.appendChild(el("line", {x1: x, x2: x, y1: sy(ymax), y2: sy(ymin), stroke: grid, "stroke-width": 1})); svg.appendChild(el("text", {x: x, y: H - B + 18, "text-anchor": "middle", fill: muted}, fmt(u, 1))); }
  svg.appendChild(el("text", {x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle", fill: muted}, "u = log x"));
  svg.appendChild(el("text", {x: 14, y: T + 10, fill: muted}, "F / (T/2π)"));
  svg.appendChild(el("line", {x1: L, x2: W - R, y1: sy(0), y2: sy(0), stroke: muted, "stroke-width": 1, "stroke-dasharray": "3 3"}));
  let d = "";
  for (let i = 0; i < DATA.u.length; i++){ d += (i ? "L" : "M") + sx(DATA.u[i]).toFixed(1) + " " + sy(DATA.F_normalised[i]).toFixed(1); }
  svg.appendChild(el("path", {d, fill: "none", stroke: "var(--zeta)", "stroke-width": 1.4, "stroke-linejoin": "round"}));
  const labelled = new Set([2,3,4,5,7,8,9,11,13,16,17,19,23,25,27,29,31,32,37,41,43,47,49,53,59,61,64,67,71,73,79,81,83,89]);
  DATA.zeta_peaks.forEach((r, idx) => {
    svg.appendChild(el("circle", {cx: sx(r.u), cy: sy(r.predicted), r: 3.2, fill: "var(--surface)", stroke: ink, "stroke-width": 1.2}));
    if (labelled.has(r.n)) svg.appendChild(el("text", {x: sx(r.u), y: sy(r.measured) + 14 + (idx % 2) * 11, "text-anchor": "middle", fill: ink, "font-weight": 500}, String(r.n)));
  });
  // crosshair + tooltip
  const cross = el("line", {x1: 0, x2: 0, y1: sy(ymax), y2: sy(ymin), stroke: ink, "stroke-width": 1, "stroke-dasharray": "2 3", opacity: 0}); svg.appendChild(cross);
  const dot = el("circle", {r: 4, fill: "var(--zeta)", stroke: "var(--surface)", "stroke-width": 2, opacity: 0}); svg.appendChild(dot);
  const wrap = document.getElementById("zeta-wrap");
  function nearestIndex(u){ let lo = 0, hi = DATA.u.length - 1; while (hi - lo > 1){ const m = (lo + hi) >> 1; (DATA.u[m] < u) ? lo = m : hi = m; } return (u - DATA.u[lo] < DATA.u[hi] - u) ? lo : hi; }
  function show(evt){
    const rect = svg.getBoundingClientRect(); const px = (evt.clientX - rect.left) * W / rect.width;
    const u = xmin + (px - L) / (W - L - R) * (xmax - xmin); if (u < xmin || u > xmax) return hide();
    // snap to a spike if within 0.012
    let best = null; for (const r of DATA.zeta_peaks){ if (Math.abs(r.u - u) < 0.012 && (!best || Math.abs(r.u - u) < Math.abs(best.u - u))) best = r; }
    const i = best ? nearestIndex(best.u) : nearestIndex(u);
    const uu = DATA.u[i], v = DATA.F_normalised[i];
    cross.setAttribute("x1", sx(uu)); cross.setAttribute("x2", sx(uu)); cross.setAttribute("opacity", 1);
    dot.setAttribute("cx", sx(uu)); dot.setAttribute("cy", sy(v)); dot.setAttribute("opacity", 1);
    tip.textContent = best ? `n = ${best.n}  u = log ${best.n} = ${fmt(best.u, 4)}  F = ${fmt(v, 3)}  predicted ${fmt(best.predicted, 3)}` : `u = ${fmt(uu, 3)}  F = ${fmt(v, 3)}`;
    tip.style.left = (sx(uu) * rect.width / W) + "px"; tip.style.top = (sy(v) * rect.height / H) + "px"; tip.dataset.on = "1";
  }
  function hide(){ cross.setAttribute("opacity", 0); dot.setAttribute("opacity", 0); tip.dataset.on = "0"; }
  wrap.addEventListener("mousemove", show); wrap.addEventListener("mouseleave", hide); wrap.addEventListener("touchstart", e => show(e.touches[0]), {passive: true}); wrap.addEventListener("touchmove", e => show(e.touches[0]), {passive: true});
  const tb = document.querySelector("#zeta-table tbody");
  for (const r of DATA.zeta_peaks){ const tr = document.createElement("tr"); tr.innerHTML = `<td>${r.n}</td><td>${fmt(r.u, 5)}</td><td>${fmt(r.predicted, 4)}</td><td>${fmt(r.measured, 4)}</td><td>${fmt(100 * r.rel_err, 2)} %</td>`; tb.appendChild(tr); }
})();

// ---------- Fibonacci chart
(function(){
  const svg = document.getElementById("fib-chart"), tip = document.getElementById("fib-tip");
  const W = 960, H = 400, L = 54, R = 16, T = 18, B = 44;
  const xmin = 0, xmax = 12, ymin = -4.2, ymax = 0.15;    // log10 scale
  const sx = k => L + (k - xmin) / (xmax - xmin) * (W - L - R);
  const sy = v => T + (ymax - v) / (ymax - ymin) * (H - T - B);
  const ink = "var(--ink)", muted = "var(--muted)", grid = "var(--grid)";
  for (let e = -4; e <= 0; e++){ const y = sy(e); svg.appendChild(el("line", {x1: L, x2: W - R, y1: y, y2: y, stroke: grid})); svg.appendChild(el("text", {x: L - 8, y: y + 4, "text-anchor": "end", fill: muted}, e === 0 ? "1" : "10^" + e)); }
  for (let k = 0; k <= 12.001; k += 2){ const x = sx(k); svg.appendChild(el("line", {x1: x, x2: x, y1: sy(ymax), y2: sy(ymin), stroke: grid})); svg.appendChild(el("text", {x, y: H - B + 18, "text-anchor": "middle", fill: muted}, String(k))); }
  svg.appendChild(el("text", {x: (L + W - R) / 2, y: H - 6, "text-anchor": "middle", fill: muted}, "wavenumber k"));
  svg.appendChild(el("text", {x: 14, y: T + 10, fill: muted}, "intensity / N²"));
  let d = "";
  for (let i = 0; i < DATA.k.length; i++){ const v = Math.log10(Math.max(DATA.background[i], 1e-6)); d += (i ? "L" : "M") + sx(DATA.k[i]).toFixed(1) + " " + sy(Math.max(v, ymin)).toFixed(1); }
  svg.appendChild(el("path", {d, fill: "none", stroke: muted, "stroke-width": 1, opacity: 0.55}));
  const stems = [];
  for (const b of DATA.bragg_peaks){
    const x = sx(b.k), y = sy(Math.log10(b.amplitude2));
    const g = el("g", {}); g.appendChild(el("line", {x1: x, x2: x, y1: sy(ymin), y2: y, stroke: "var(--gold)", "stroke-width": 2.2, "stroke-linecap": "round"}));
    g.appendChild(el("circle", {cx: x, cy: y, r: 4, fill: "var(--gold)", stroke: "var(--surface)", "stroke-width": 1.5}));
    if (b.amplitude2 > 0.03) g.appendChild(el("text", {x, y: y - 9, "text-anchor": "middle", fill: ink, "font-weight": 500}, `(${b.m}, ${b.n})`));
    svg.appendChild(g); stems.push({b, x, y, g});
  }
  const wrap = document.getElementById("fib-wrap");
  function show(evt){
    const rect = svg.getBoundingClientRect(); const px = (evt.clientX - rect.left) * W / rect.width;
    let best = null; for (const s of stems){ if (!best || Math.abs(s.x - px) < Math.abs(best.x - px)) best = s; }
    if (!best || Math.abs(best.x - px) > 14) return hide();
    tip.textContent = `(m, n) = (${best.b.m}, ${best.b.n})   k = ${fmt(best.b.k, 4)}   I/N² = ${fmt(best.b.amplitude2, 4)}   |m + nφ̄| = ${fmt(best.b.conjugate, 3)}`;
    tip.style.left = (best.x * rect.width / W) + "px"; tip.style.top = (best.y * rect.height / H) + "px"; tip.dataset.on = "1";
  }
  function hide(){ tip.dataset.on = "0"; }
  wrap.addEventListener("mousemove", show); wrap.addEventListener("mouseleave", hide); wrap.addEventListener("touchstart", e => show(e.touches[0]), {passive: true}); wrap.addEventListener("touchmove", e => show(e.touches[0]), {passive: true});
  const tb = document.querySelector("#fib-table tbody");
  for (const b of [...DATA.bragg_peaks].sort((a, c) => c.amplitude2 - a.amplitude2).slice(0, 12)){ const tr = document.createElement("tr"); tr.innerHTML = `<td>(${b.m}, ${b.n})</td><td>${fmt(b.k, 4)}</td><td>${fmt(b.amplitude2, 4)}</td><td>${fmt(b.conjugate, 3)}</td>`; tb.appendChild(tr); }
})();
</script>
"""


def write_page(data: dict, path: Path) -> Path:
    """Embed ``data`` (from ``build_bridge``) into the template and write the page."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.replace("__DATA__", json.dumps(data, separators=(",", ":"))), encoding="utf-8")
    return path
