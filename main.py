"""Entry point: candidate pool → geometric siever → Lucas–Lehmer confirmation → 3-D Mersenne Star map,
optionally followed by the research dashboards (``--research``).

    python main.py                       # p ≤ 2500, logistic siever, HTML + PNG + CSV in output/
    python main.py --full --model both   # p ≤ 5000, logistic and torch MLP
    python main.py --research            # add growth law, NMC, Wieferich, Wall–Sun–Sun, periodicity, discovery ledger

Everything printed is reproducible (fixed seed) and every number-theoretic claim is exact.
"""
from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np

import config as cfg
from core_math.geometry import build_star, exponent_coordinates
from core_math.mersenne import (KNOWN_MERSENNE_EXPONENTS, is_known_mersenne_exponent, lucas_lehmer, sophie_germain_factor, trial_factor, wagstaff_probability)
from core_math.psi_sequence import eight_level, golden_level
from core_math.symbolic_bridge import bridge_report
from ml_models.dataset import build_dataset
from ml_models.features import FEATURE_NAMES, GEOMETRY_ONLY_FEATURE_NAMES
from ml_models.siever import LogisticSiever, default_model_factories, evaluate_cv, format_cv_table, honesty_line, score_candidates, train_default


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p-max", type=int, default=cfg.P_MAX_DEFAULT, help="largest candidate exponent")
    ap.add_argument("--full", action="store_true", help=f"use p ≤ {cfg.P_MAX_FULL}")
    ap.add_argument("--model", choices=("logistic", "mlp", "both"), default="logistic")
    ap.add_argument("--no-arithmetic", action="store_true", help="geometry-only features (ablation)")
    ap.add_argument("--cv-repeats", type=_positive_int, default=cfg.CV_REPEATS, help="stratified CV repeats (>= 1)")
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--research", action="store_true", help="run the research dashboards and update the ledger")
    ap.add_argument("--out", type=Path, default=cfg.OUTPUT_DIR)
    ap.add_argument("--seed", type=int, default=cfg.SEED)
    ap.add_argument("--layout", choices=cfg.STAR_LAYOUTS, default=cfg.STAR_LAYOUT)
    return ap.parse_args(argv)


def _positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return value


def banner(title: str) -> None:
    print(f"\n=== {title} " + "=" * max(0, 72 - len(title)))


def run(args: argparse.Namespace) -> dict[str, object]:
    t0 = time.perf_counter()
    p_max = cfg.P_MAX_FULL if args.full else args.p_max
    use_arith = not args.no_arithmetic
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    names = FEATURE_NAMES if use_arith else GEOMETRY_ONLY_FEATURE_NAMES

    # ------------------------------------------------------------------ 1. candidate pool + features
    banner("1. candidate pool")
    X, y, ps = build_dataset(cfg.P_MIN, p_max, use_arith)
    trivial = [p for p in (2, 3) if p <= p_max]
    print(f"prime exponents {cfg.P_MIN} ≤ p ≤ {p_max}: {len(ps)}  |  known Mersenne primes among them: {int(y.sum())}"
          f"  |  trivial cases reported separately: {trivial}")
    print(f"features: {X.shape[1]} ({'geometry + arithmetic' if use_arith else 'geometry only'})")

    # ------------------------------------------------------------------ 2. cross-validated evaluation
    banner("2. siever evaluation (repeated stratified CV)")
    include_mlp = args.model in ("mlp", "both")
    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    if min(n_pos, n_neg) < 2:
        raise SystemExit(f"candidate pool p ≤ {p_max} has {n_pos} positive and {n_neg} negative exponents; "
                         "stratified cross-validation needs at least two of each — raise --p-max")
    folds = min(cfg.CV_FOLDS, n_pos, n_neg)
    if folds < cfg.CV_FOLDS:
        print(f"note: using {folds} folds (smallest class has {min(n_pos, n_neg)} samples)")
    factories = default_model_factories(use_arith, include_mlp=include_mlp)
    report = evaluate_cv(factories, X, y, folds=folds, repeats=args.cv_repeats, seed=args.seed)
    print(format_cv_table(report))
    print(honesty_line(report, "logistic"))
    if include_mlp:
        print(honesty_line(report, "mlp"))
    logit_all = LogisticSiever().fit(X, y)
    print(f"constant features removed by VarianceThreshold: {logit_all.n_dropped_constant} "
          f"(all '*_at_pow2' ring coordinates of the Lucas–Lehmer index are constant for p ≥ 5)")
    print("largest |coefficients| of the logistic siever: " + ", ".join(f"{n}={c:+.2f}" for n, c in logit_all.coefficients(names)[:6]))

    # ------------------------------------------------------------------ 3. plausibility scores
    banner("3. plausibility index")
    primary_kind = "mlp" if args.model == "mlp" else "logistic"
    scores: dict[str, np.ndarray] = {"logistic": score_candidates(logit_all, X)}
    if include_mlp:
        scores["mlp"] = score_candidates(train_default("mlp", X, y, use_arith), X)
    plaus = scores[primary_kind]
    order = np.argsort(-plaus, kind="stable")
    print(f"primary model: {primary_kind}; top-10 candidates by plausibility: "
          + ", ".join(f"{ps[i]}({plaus[i]:.2f})" for i in order[:10]))

    # ------------------------------------------------------------------ 4. Lucas–Lehmer confirmation
    banner("4. Lucas–Lehmer confirmation (ordered by plausibility, time-budgeted)")
    ll_result: dict[int, bool | None] = {p: None for p in ps}
    t_ll = time.perf_counter()
    tests_to_recover_all = None
    found = 0
    for rank, i in enumerate(order, start=1):
        if time.perf_counter() - t_ll > cfg.LL_TIME_BUDGET_S:
            print(f"time budget of {cfg.LL_TIME_BUDGET_S}s reached after {rank - 1} tests; remaining exponents left untested")
            break
        ll_result[ps[i]] = lucas_lehmer(ps[i])
        if ll_result[ps[i]]:
            found += 1
            if found == int(y.sum()):
                tests_to_recover_all = rank
    ll_time = time.perf_counter() - t_ll
    confirmed = sorted(p for p, r in ll_result.items() if r)
    print(f"Lucas–Lehmer primes found: {confirmed}")
    print(f"agreement with the known table: {confirmed == [p for p in KNOWN_MERSENNE_EXPONENTS if cfg.P_MIN <= p <= p_max]}")
    if tests_to_recover_all is not None:
        oof = report[primary_kind]["ll_tests_to_full_recall"]
        print(f"tests needed (in plausibility order) to recover all {int(y.sum())} known exponents: {tests_to_recover_all} of {len(ps)}"
              f"  — IN-SAMPLE (the model saw these labels); the honest out-of-fold figure is {oof[0]:.0f} ± {oof[1]:.0f}"
              f" vs {report['wagstaff']['ll_tests_to_full_recall'][0]:.0f} for the Wagstaff prior")
    print(f"LL sweep time: {ll_time:.2f}s")

    # ------------------------------------------------------------------ 5. symbolic bridge
    banner("5. symbolic bridge (sympy identities)")
    br = bridge_report(10)
    print(", ".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in br.items()))

    # ------------------------------------------------------------------ 6. geometry + figures
    points = [exponent_coordinates(p) for p in ps]
    known = set(KNOWN_MERSENNE_EXPONENTS)
    tfs = {p: trial_factor(p, cfg.TRIAL_FACTOR_K_MAX) for p in ps}
    if not args.no_plot:
        banner("6. Mersenne Star map")
        from visualization.plotter import build_star_figure, plot_period20_wheel_png, write_html

        star = build_star(args.layout)
        fig = build_star_figure(star, points, plaus, ll_result, known, tfs)
        html = write_html(fig, out / cfg.HTML_NAME)
        png = plot_period20_wheel_png(points, plaus, ll_result, known, out / cfg.WHEEL_PNG_NAME)
        print(f"wrote {html} and {png}")

    # ------------------------------------------------------------------ 7. summary table + CSV
    banner("7. summary")
    header = ["p", "plausibility", "wagstaff_prior", "lucas_lehmer", "known", "eight_level", "golden_level", "theta20_deg",
              "trial_factor", "sophie_germain"]
    if include_mlp and args.model == "both":
        header.insert(2, "plausibility_mlp")
    rows = []
    for i, p in enumerate(ps):
        row = [p, round(float(plaus[i]), 4), round(wagstaff_probability(p), 4),
               {True: "prime", False: "composite", None: ""}[ll_result[p]], is_known_mersenne_exponent(p),
               eight_level(p), round(golden_level(p), 4), (54 * p) % 360, tfs[p] or "", sophie_germain_factor(p)]
        if include_mlp and args.model == "both":
            row.insert(2, round(float(scores["mlp"][i]), 4))
        rows.append(row)
    csv_path = out / cfg.SUMMARY_CSV_NAME
    with csv_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    show = sorted(rows, key=lambda r: -r[1])[:12]
    widths = [max(len(h), 9) for h in header]
    print("  ".join(h.rjust(w) for h, w in zip(header, widths, strict=True)))
    for r in show:
        print("  ".join((f"{v:.3f}" if isinstance(v, float) else (str(v) if v != "" else "-")).rjust(w) for v, w in zip(r, widths, strict=True)))
    print(f"wrote {csv_path}")

    # ------------------------------------------------------------------ 8. research dashboards
    results: dict[str, object] = {"ps": ps, "plausibility": plaus, "ll": ll_result, "cv": report, "bridge": br}
    if args.research:
        banner("8. research dashboards")
        from research.discovery import Ledger
        from research.lean_export import export
        from research.report import research_report

        md, res = research_report(bridge_report=br, growth_png=out / cfg.GROWTH_PNG_NAME, stats_n_rep=cfg.STATS_N_REP,
                                  rank_p_max_factor=cfg.RANK_P_MAX_FACTOR, rank_p_max_check=cfg.RANK_P_MAX_CHECK)
        md_path = out / cfg.RESEARCH_REPORT_NAME
        md_path.write_text(md, encoding="utf-8")
        lean_path = out / "lean_skeletons.lean"
        lean_path.write_text(export(Ledger.load().entries), encoding="utf-8")
        print(md)
        print(f"wrote {md_path}, {lean_path} and updated {cfg.LEDGER_PATH}")
        results["research"] = res

    print(f"\ntotal time: {time.perf_counter() - t0:.1f}s")
    return results


def main(argv: list[str] | None = None) -> int:
    run(parse_args(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
