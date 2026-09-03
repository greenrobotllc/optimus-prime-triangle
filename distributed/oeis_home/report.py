"""The static results page (``docs/index.html`` + ``docs/data.json``): terms found and by whom,
unit map, progress, contributors, and a self-check snippet generated from a real verified line."""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .families import Family

STATE_COLORS = {"open": "var(--open)", "claimed": "var(--claimed)", "pending": "var(--pending)", "verified": "var(--verified)",
                "double_checked": "var(--double)", "disputed": "var(--disputed)", "invalid": "var(--disputed)"}

CSS = """
:root{--bg:#f6f7f4;--surface:#ffffff;--ink:#1c2321;--muted:#5d6763;--rule:#d9ded9;--accent:#1f6f5f;
--open:#e3e7e2;--claimed:#cfe3da;--pending:#f2e2b8;--verified:#8fcbb4;--double:#2f9e7a;--disputed:#e2a49a;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#121816;--surface:#1a2220;--ink:#e6ece9;--muted:#9fb0aa;--rule:#2c3733;--accent:#5fc7a6;
--open:#26312d;--claimed:#2f4a41;--pending:#5a4b21;--verified:#2c7a5d;--double:#3fbf92;--disputed:#8a3f36;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#121816;--surface:#1a2220;--ink:#e6ece9;--muted:#9fb0aa;--rule:#2c3733;--accent:#5fc7a6;
--open:#26312d;--claimed:#2f4a41;--pending:#5a4b21;--verified:#2c7a5d;--double:#3fbf92;--disputed:#8a3f36;color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "IBM Plex Sans",system-ui,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 20px 64px;display:flex;flex-direction:column;gap:32px}
h1,h2{font-family:"Newsreader",Georgia,serif;font-weight:600;margin:0;text-wrap:balance}
h1{font-size:clamp(30px,5vw,44px)} h2{font-size:24px}
p{margin:0;max-width:70ch} .muted{color:var(--muted)} code,pre{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:13px}
pre{background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:12px 14px;overflow-x:auto}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}
.stats div{border-top:2px solid var(--rule);padding-top:8px}.stats dt{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.stats dd{margin:2px 0 0;font-family:"IBM Plex Mono",monospace;font-size:22px;font-variant-numeric:tabular-nums}
.wrap{overflow-x:auto;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--rule);white-space:nowrap}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:500}tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--rule)}
.map{display:grid;grid-template-columns:repeat(auto-fill,minmax(22px,1fr));gap:3px}
.cell{aspect-ratio:1;border-radius:3px;background:var(--open)}.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.legend span::before{content:"";display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px;background:var(--sw)}
a{color:var(--accent)}footer{font-size:13px;color:var(--muted)}
"""


def _self_check_snippet(ledger: dict) -> str:
    for u in ledger["units"].values():
        for rec in u.get("verdicts", []):
            if rec.get("method") == "factor":
                b = -1 if rec["variant"] in ("m1", "even") else 1
                return ("# run from the repository root after `pip install -e distributed` (or with PYTHONPATH=.:distributed)\n"
                        f"# a verified factor line from unit {u['unit_id']}\n"
                        f"from core_math.psi_sequence import psi_mod\nprint(psi_mod(2, {b}, {rec['n']}, {rec['factor']}) == 0)   # True\n"
                        f"from oeis_home.families import abs_value\nprint(abs_value({rec['variant']!r}, {rec['n']}) % {rec['factor']} == 0)   # True")
    return "# no verified factor line yet"


def render_site(ledger: dict, contributors: dict[str, dict], fam: Family, out: Path, built_from: str = "") -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    c = ledger["counts"]
    total = len(ledger["units"])
    terms = sorted(ledger["positive_claims"], key=lambda p: (p["n"], p["variant"]))
    rows = "".join(
        f"<tr><td>{p['n']}</td><td>{p['variant']}</td><td>{p['digits']}</td>"
        f"<td><span class=badge>{'prime' if p.get('maintainer_pari') == 'isprime' else ('prp' if p.get('verifier_login') else 'prp — awaiting second result')}</span></td>"
        f"<td>{html.escape(contributors.get(p.get('discoverer_login', ''), {}).get('display_name', p.get('discoverer_login', '')))}</td>"
        f"<td>{html.escape(p.get('discovered_at', '')[:10])}</td>"
        f"<td>{html.escape(contributors.get(p.get('verifier_login', ''), {}).get('display_name', p.get('verifier_login', '') or '—'))}</td>"
        f"<td>{html.escape(str(p.get('ci_run_id', 'local')) if p.get('ci_confirmed') else 'local only')}</td><td>{html.escape(p.get('maintainer_pari', 'none'))}</td></tr>"
        for p in terms)
    cells = "".join(f'<div class=cell style="background:{STATE_COLORS[u["state"]]}" title="{uid}: {u["state"]}; {", ".join(r["login"] for r in u["results"]) or "nobody yet"}"></div>'
                    for uid, u in ledger["units"].items())
    contrib_rows = "".join(f"<tr><td>{html.escape(c2['display_name'])}</td><td>{html.escape(login)}</td><td>{c2['role']}</td><td>{c2['units_verified']}</td><td>{c2['double_checks']}</td><td>{c2['first_finds']}</td></tr>"
                           for login, c2 in sorted(ledger["contributors"].items()))
    page = f"""<title>OEIS@home · Lehmer companion primes</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:wght@600&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono&display=swap">
<style>{CSS}</style>
<main>
<header>
<p class=muted>OEIS@home pilot · family <code>lehmer-q2</code> · <code>{html.escape(fam.hash)}</code></p>
<h1>Primes in the Lehmer companion sequences with Q = 2</h1>
<p>a(n) = Ψ(2, −1, n) = V̄<sub>n</sub>(√5, 2) and Ψ(2, 1, n) = V̄<sub>n</sub>(√3, 2); even indices share V<sub>n/2</sub>(1, 4). Every line of every result is recomputed with the volunteer's own test base; rows marked "local only" were checked by a local rebuild, not by CI. A second result from a different account is the double check that earns credit. Rebuilt {now}{(' from ' + html.escape(built_from)) if built_from else ''}{' (unsigned local rebuild)' if any(u.get('unsigned') for u in ledger['units'].values()) else ''}.</p>
<dl class=stats>
<div><dt>Units verified</dt><dd>{c['verified'] + c['double_checked']} / {total}</dd></div>
<div><dt>Double-checked</dt><dd>{c['double_checked']}</dd></div>
<div><dt>Verified through n</dt><dd>{ledger['verified_through']}</dd></div>
<div><dt>Prime / prp indices found</dt><dd>{len(terms)}</dd></div>
<div><dt>Contributors</dt><dd>{len(ledger['contributors'])}</dd></div>
</dl>
</header>
<section><h2>Terms found</h2>
<div class=wrap><table><thead><tr><th>n</th><th>variant</th><th>digits</th><th>status</th><th>discoverer</th><th>discovered</th><th>verifier</th><th>CI run</th><th>gp check</th></tr></thead><tbody>{rows or '<tr><td colspan=9>none yet</td></tr>'}</tbody></table></div>
<p class=muted>Seed indices n ≤ 120 were known before the pilot (repository); everything larger is new data. "prp" = BPSW plus strong probable-prime tests to bases 2, 3 and the worker base; "prime" = proven with PARI isprime or deterministic below 2^64.</p></section>
<section><h2>Unit map</h2><div class=map>{cells}</div>
<div class=legend><span style="--sw:var(--open)">open</span><span style="--sw:var(--claimed)">claimed</span><span style="--sw:var(--pending)">pending</span><span style="--sw:var(--verified)">verified (1 result, CI recomputed)</span><span style="--sw:var(--double)">double-checked (2 accounts)</span><span style="--sw:var(--disputed)">disputed / invalid</span></div>
<p class=muted>Units get smaller as n grows so that one unit takes roughly 10–20 minutes. Open units: {c['open']}; disputed: {c['disputed']}.</p></section>
<section><h2>Contributors</h2><div class=wrap><table><thead><tr><th>name</th><th>login</th><th>role</th><th>units verified</th><th>double checks</th><th>first finds</th></tr></thead><tbody>{contrib_rows or '<tr><td colspan=6>none yet</td></tr>'}</tbody></table></div></section>
<section><h2>Verify any row yourself</h2><pre>{html.escape(_self_check_snippet(ledger))}</pre></section>
<footer>Data (results, verified records, ledger, exports) are CC0; code is MIT. Only your login and display name are published; use a GitHub noreply commit e-mail. Exports for OEIS live in <code>distributed/exports/</code>.</footer>
</main>
"""
    (out / "index.html").write_text(page, encoding="utf-8")
    (out / "data.json").write_text(json.dumps({"built_at": now, "counts": c, "verified_through": ledger["verified_through"],
                                               "positive_claims": terms, "contributors": ledger["contributors"]}, indent=1, ensure_ascii=False), encoding="utf-8")
