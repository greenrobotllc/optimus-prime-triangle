"""Assemble the research dashboards into one markdown report."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import config as cfg
from core_math.mersenne import KNOWN_MERSENNE_EXPONENTS
from research import conjectures as cj
from research import exponent_statistics as es
from research import growth_laws as gl
from research import periodicity as pr
from research.discovery import run_discovery


def research_report(nmc_p_max: int = cfg.NMC_P_MAX, wieferich_limit: int = cfg.WIEFERICH_LIMIT, wss_limit: int = cfg.WSS_LIMIT,
                    bridge_report: dict[str, bool] | None = None, ledger_path: Path | None = None,
                    growth_png: Path | None = None, stats_n_rep: int = cfg.STATS_N_REP,
                    rank_p_max_factor: int = cfg.RANK_P_MAX_FACTOR, rank_p_max_check: int = cfg.RANK_P_MAX_CHECK) -> tuple[str, dict[str, Any]]:
    """Run every dashboard; return ``(markdown, results)``."""
    results: dict[str, Any] = {}
    lines: list[str] = ["# Research report", ""]

    # G1
    rows = gl.hypothesis_table()
    results["growth"] = rows
    lines += ["## G1 · Growth law of the known exponents", "",
              f"Observed geometric-mean successive ratio over {len(KNOWN_MERSENNE_EXPONENTS)} exponents: **{gl.growth_factor():.4f}** "
              f"(least squares {gl.least_squares_growth_factor():.4f}, q_N^(1/N) = {gl.root_growth_factor():.4f}).", "",
              "```", gl.format_table(rows), "```", "",
              "Reading: the Lenstra–Pomerance–Wagstaff factor sits inside the 95% interval; the golden ratio does not. "
              "With 52 data points this is a preference, not a proof.", ""]
    if growth_png is not None:
        gl.plot_growth_law(growth_png)
        lines += [f"Plot: `{growth_png}`", ""]

    # G1b statistics
    stats = es.run_all(n_rep=stats_n_rep)
    results["statistics"] = stats
    n_tests = len(stats["residues"])
    lines += ["## G1b · Do the known exponents show any golden / residue structure?", "",
              f"Size-matched Monte-Carlo null (each exponent replaced by a random prime within a factor 1.5), {stats_n_rep} replications.", "",
              es.format_report(stats), "",
              f"Reading: none of the φ-zone metrics differs from the null; after a Bonferroni correction for the {n_tests} residue tests "
              "no residue class is significant. The mild lean seen mod 12 (deficit at 11 mod 12) is the Sophie-Germain obstruction: "
              "2p + 1 can be a prime factor of M_p only when p ≡ 11 (mod 12).", ""]

    # G2
    nmc = cj.nmc_dashboard(nmc_p_max)
    results["nmc"] = nmc
    lines += ["## G2 · New Mersenne Conjecture (Bateman–Selfridge–Wagstaff)", "",
              f"Odd primes p ≤ {nmc_p_max}: all three conditions hold for p ∈ {nmc['all_three']}; "
              f"counterexamples (exactly two hold): {nmc['counterexamples'] or 'none'}.", "",
              f"Wagstaff prime exponents found: {nmc['wagstaff_primes']}", ""]

    # G3
    wief = cj.wieferich_search(wieferich_limit)
    sq = cj.mersenne_square_factor_check(cfg.SQUAREFREE_P_MAX, cfg.SQUAREFREE_Q_MAX)
    results["wieferich"] = wief
    results["squarefree"] = sq
    lines += ["## G3 · Squarefree Mersenne numbers / Wieferich primes", "",
              f"Wieferich primes below {wieferich_limit}: {wief}.  Admissible prime factors q = 2kp+1 ≤ {sq['q_max']} of M_p for p ≤ {sq['p_max']} "
              f"checked for q² | M_p: {sq['checked']} candidates, hits: {sq['hits'] or 'none'}.", ""]

    # G4
    wss = cj.wall_sun_sun_search(wss_limit)
    entry = cj.fibonacci_entry_point_check([p for p in KNOWN_MERSENNE_EXPONENTS if 5 <= p <= 127])
    results["wall_sun_sun"] = wss
    results["entry_points"] = entry
    lines += ["## G4 · Wall–Sun–Sun primes and the Fibonacci fingerprint of Mersenne primes", "",
              f"Wall–Sun–Sun primes below {wss_limit}: {wss or 'none'}.  "
              f"M_p | F_(M_p − (5|M_p)) for p ∈ {sorted(entry)}: {'all hold' if all(entry.values()) else entry}.", ""]

    # G4b rank of apparition
    rank_rows = cj.mersenne_fibonacci_rank_table(rank_p_max_factor, rank_p_max_check)
    results["rank_of_apparition"] = rank_rows
    r3 = [r for r in rank_rows if r["p_mod_4"] == 3]
    r1 = [r for r in rank_rows if r["p_mod_4"] == 1]
    lines += ["## G4b · Fibonacci rank of apparition of Mersenne primes", "",
              "Theorem: if M_p is prime and p ≡ 3 (mod 4) then the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 "
              "(M_p | L_{2^{p−1}} by Lucas's golden-seed test, F_{2^p} = F_{2^{p−1}}·L_{2^{p−1}}, gcd(F_n, L_n) | 2).", "",
              f"Checked for every known Mersenne prime with p ≡ 3 (mod 4) up to {rank_p_max_check}: "
              f"{sum(bool(r['alpha_is_2p']) for r in r3)} of {len(r3)} hold.", "",
              "For p ≡ 1 (mod 4) the rank divides M_p − 1 and is not always maximal: " +
              ", ".join(f"p={r['p']}: (M_p−1)/α = {r['cofactor']}" for r in r1) + ".", ""]

    # G7
    golden = pr.golden_rings()
    paper = pr.paper_rings()
    results["golden_rings"] = golden
    lines += ["## G7 · Periodicity classification and the golden rings", "", f"> {pr.THEOREM_STATEMENT}", "",
              "| ring | b | rotation θ | predicted period | verified exactly | in source paper |", "|---|---|---|---|---|---|"]
    for r in paper:
        lines.append(f"| paper | {r['b']} | {r['theta_deg']:.1f}° | {r['predicted_period']} | {r['verified_exact']} | yes |")
    for r in golden:
        lines.append(f"| golden {r['name']} | {r['b']} | {r['theta_deg']:.1f}° | {r['predicted_period']} | {r['verified_exact']} | {'yes' if r['in_source_paper'] else 'no'} |")
    lines.append("")

    # G8
    ledger, cen, density = run_discovery(ledger_path, bridge_report)
    results["census"] = cen
    results["density"] = density
    periodic = [c for c in cen if c["kind"] == "periodic"]
    known = [c for c in cen if c["kind"] == "known_sequence"]
    lines += ["## G8 · Discovery census", "",
              f"Points enumerated: {len(cen)} · periodic: {len(periodic)} · matched a classical sequence: {len(known)} · unclassified: {len(cen) - len(periodic) - len(known)}.", "",
              "Periodic points (period, predicted):", ""]
    for c in periodic:
        rule = "divides predicted" if c.get("prediction_rule") == "divides" else "predicted"
        lines.append(f"- {c['point']}: period {c['period']}, {rule} {c.get('predicted_period')}")
    lines += ["", "Integer points richest in primes among |Ψ(a, b, n)|, 2 ≤ n < 40, ranked by observed / size-expected "
              "(a random integer of size N is prime with probability ≈ 1/ln N):", ""]
    for d in density[:8]:
        lines.append(f"- {d['point']}: {d['primes']} primes (size-expected {d['expected_by_size']:.1f}, ratio {d['ratio']:.2f}) at n = {d['indices']}")
    lines += ["", f"Ledger: `{ledger.path}` ({len(ledger.entries)} entries, label **{cfg.DISCOVERY_LABEL}**, novelty unchecked unless stated).", ""]
    return "\n".join(lines), results
