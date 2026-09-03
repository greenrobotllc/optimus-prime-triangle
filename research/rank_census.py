"""Census of the Fibonacci rank of apparition of Mersenne primes, at scale (goal G4b, extended).

For a Mersenne prime ``M_p`` with ``p ≡ 3 (mod 4)`` the rank of apparition is ``2^p`` (theorem in
:mod:`research.conjectures`); this script re-verifies it without factoring.  For ``p ≡ 1 (mod 4)``
the rank divides ``N = M_p − 1 = 2(2^{p−1} − 1)`` and the odd cofactor ``c = N/α`` is unknown in
general; but **whether a given small prime q divides c needs no factorisation**: ``q | c`` iff
``M_p | F_{N/q}`` (for ``q | N``).  This script tests every prime ``q ≤ 200`` dividing ``N`` for
every known Mersenne prime up to ``--p-max``, using GMP (gmpy2) with the shift-and-add Mersenne
reduction, and appends one JSON record per exponent as it finishes.

Cost: one Fibonacci fast-doubling evaluation is ``p`` doublings of ``p``-bit numbers.

    python research/rank_census.py --p-max 1398269 --out discoveries/rank_of_apparition_census.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core_math.mersenne import KNOWN_MERSENNE_EXPONENTS, sieve_primes  # noqa: E402

try:
    from gmpy2 import mpz
except ImportError:  # pragma: no cover - gmpy2 is optional
    mpz = int  # type: ignore[misc,assignment]


def reduce_mersenne(x, p: int, M):
    """``x mod M_p`` for ``0 ≤ x < M_p²`` via ``x ↦ (x & M) + (x >> p)``."""
    x = (x & M) + (x >> p)
    x = (x & M) + (x >> p)
    if x >= M:
        x -= M
    return x


def fib_pair_mod_mersenne(n, p: int, M):
    """``(F_n, F_{n+1}) mod M_p`` by iterative fast doubling over the bits of ``n``."""
    f, g = mpz(0), mpz(1)
    for i in range(n.bit_length() - 1, -1, -1):
        c = reduce_mersenne(f * ((2 * g - f) % M), p, M)      # F_{2k}
        d = reduce_mersenne(f * f + g * g, p, M)              # F_{2k+1}
        if (n >> i) & 1:
            f, g = d, reduce_mersenne(c + d, p, M)
        else:
            f, g = c, d
    return f, g


def fib_mod_mersenne(n, p: int, M):
    return fib_pair_mod_mersenne(n, p, M)[0]


def lucas_mod_mersenne(n, p: int, M):
    f, g = fib_pair_mod_mersenne(n, p, M)
    return (2 * g - f) % M


def small_prime_divisors_of_N(p: int, q_max: int = 200) -> list[int]:
    """Odd primes ``q ≤ q_max`` dividing ``N = 2(2^{p−1} − 1)``: ``ord_q(2) | p − 1``."""
    return [q for q in sieve_primes(q_max) if q > 2 and pow(2, p - 1, q) == 1]


def census_record(p: int) -> dict:
    t0 = time.perf_counter()
    M = mpz(2) ** p - 1
    rec: dict = {"p": p, "p_mod_4": p % 4}
    if p % 4 == 3:
        n = mpz(2) ** (p - 1)
        f, g = fib_pair_mod_mersenne(n, p, M)
        rec["F_2^(p-1)_is_zero"] = bool(f == 0)
        rec["L_2^(p-1)_is_zero"] = bool((2 * g - f) % M == 0)
        rec["F_2^p_is_zero"] = bool(reduce_mersenne(f * ((2 * g - f) % M), p, M) == 0)
        rec["alpha_is_2^p"] = rec["F_2^p_is_zero"] and not rec["F_2^(p-1)_is_zero"]
    else:
        N = M - 1
        qs = small_prime_divisors_of_N(p)
        rec["q_dividing_N"] = qs
        rec["F_N_is_zero"] = bool(fib_mod_mersenne(N, p, M) == 0)             # must hold: (5|M_p) = +1
        rec["F_N/2_is_zero"] = bool(fib_mod_mersenne(N // 2, p, M) == 0)      # must fail: v2(alpha) = 1
        rec["q_dividing_cofactor"] = [q for q in qs if fib_mod_mersenne(N // q, p, M) == 0]
    rec["seconds"] = round(time.perf_counter() - t0, 1)
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--p-max", type=int, default=216091)
    ap.add_argument("--p-min", type=int, default=5)
    ap.add_argument("--out", type=Path, default=Path("discoveries/rank_of_apparition_census.json"))
    args = ap.parse_args(argv)
    records: list[dict] = json.loads(args.out.read_text()) if args.out.exists() else []
    done = {r["p"] for r in records}
    for p in KNOWN_MERSENNE_EXPONENTS:
        if p < args.p_min or p > args.p_max or p in done:
            continue
        print(f"START p={p}", flush=True)
        try:
            rec = census_record(p)
        except Exception as exc:  # pragma: no cover
            print(f"ERROR p={p}: {exc!r}", flush=True)
            continue
        records.append(rec)
        records.sort(key=lambda r: r["p"])
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(records, indent=1))
        print(f"DONE p={p} {json.dumps({k: v for k, v in rec.items() if k != 'p'})}", flush=True)
    print("CENSUS COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
