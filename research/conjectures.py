"""Exact dashboards for named open problems (goals G2–G4).

* **New Mersenne Conjecture** (Bateman–Selfridge–Wagstaff, 1989).  For odd ``p``, of the
  three statements (1) ``p = 2^k ± 1`` or ``p = 4^k ± 3``, (2) ``M_p = 2^p − 1`` prime,
  (3) ``W_p = (2^p + 1)/3`` prime, any two imply the third.  In Ψ terms, ``M_p = Ψ(−2, −5, p)``
  and ``W_p = Ψ(2, −5, p)`` are two points of the same family.
* **Squarefree Mersenne numbers.**  ``q² | M_p`` forces ``2^{q−1} ≡ 1 (mod q²)``, i.e. ``q`` is
  a Wieferich prime; only 1093 and 3511 are known and neither divides an ``M_p`` with
  prime ``p`` (their orders are 364 = 4·7·13 and 1755 = 3³·5·13).
* **Wall–Sun–Sun primes**: ``p² | F_{p − (5/p)}``.  None are known; they are the
  golden-ratio mirror of Wieferich primes.
* **Fibonacci entry point of Mersenne primes**: for a prime ``q``, ``q | F_{q − (5/q)}``;
  applied to ``q = M_p`` this is a golden-ratio fingerprint of every Mersenne prime.
"""
from __future__ import annotations

from dataclasses import dataclass

from core_math.mersenne import is_prime_int, lucas_lehmer, mersenne_number, prime_exponents, sieve_primes, wagstaff_number
from core_math.psi_sequence import fibonacci_mod, lucas_number_mod


# --------------------------------------------------------------------------- NMC
def nmc_condition1(p: int) -> bool:
    """``p = 2^k ± 1`` or ``p = 4^k ± 3`` for some ``k ≥ 0``."""
    k = 0
    while 2**k - 1 <= p + 1:
        if p in (2**k - 1, 2**k + 1):
            return True
        k += 1
    k = 0
    while 4**k - 3 <= p + 3:
        if p in (4**k - 3, 4**k + 3):
            return True
        k += 1
    return False


@dataclass(frozen=True)
class NMCRow:
    p: int
    special_form: bool
    mersenne_prime: bool
    wagstaff_prime: bool

    @property
    def count(self) -> int:
        return int(self.special_form) + int(self.mersenne_prime) + int(self.wagstaff_prime)


def nmc_dashboard(p_max: int = 1000) -> dict[str, object]:
    """Evaluate the three NMC statements exactly for odd primes ``p ≤ p_max``."""
    rows = [NMCRow(p, nmc_condition1(p), lucas_lehmer(p), is_prime_int(wagstaff_number(p)))
            for p in prime_exponents(3, p_max)]
    return {
        "rows": rows,
        "all_three": [r.p for r in rows if r.count == 3],
        "counterexamples": [r.p for r in rows if r.count == 2],
        "wagstaff_primes": [r.p for r in rows if r.wagstaff_prime],
        "mersenne_primes": [r.p for r in rows if r.mersenne_prime],
        "p_max": p_max,
    }


# --------------------------------------------------------------------------- Wieferich / squarefree
def wieferich_search(limit: int = 100_000) -> list[int]:
    """Primes ``q < limit`` with ``2^{q−1} ≡ 1 (mod q²)``."""
    return [q for q in sieve_primes(limit - 1) if q > 2 and pow(2, q - 1, q * q) == 1]


def mersenne_square_factor_check(p_max: int = 200, q_max: int = 100_000) -> dict[str, object]:
    """Look for ``q² | M_p`` among admissible ``q = 2kp + 1 ≤ q_max``; expected to find nothing."""
    hits = []
    checked = 0
    for p in prime_exponents(3, p_max):
        for k in range(1, q_max // (2 * p) + 1):
            q = 2 * k * p + 1
            if q > q_max or q % 8 not in (1, 7) or not is_prime_int(q):
                continue
            checked += 1
            if pow(2, p, q * q) == 1:
                hits.append((p, q))
    return {"hits": hits, "checked": checked, "p_max": p_max, "q_max": q_max}


# --------------------------------------------------------------------------- Wall–Sun–Sun
def legendre_5(p: int) -> int:
    """``(5 | p)`` for a prime ``p ≠ 5``: ``+1`` if ``p ≡ ±1 (mod 5)``, ``−1`` otherwise."""
    return 1 if p % 5 in (1, 4) else -1


def wall_sun_sun_search(limit: int = 20_000) -> list[int]:
    """Primes ``p < limit`` (``p ≠ 2, 5``) with ``p² | F_{p − (5/p)}``."""
    out = []
    for p in sieve_primes(limit - 1):
        if p in (2, 5):
            continue
        if fibonacci_mod(p - legendre_5(p), p * p) == 0:
            out.append(p)
    return out


def fibonacci_entry_point_check(ps: list[int]) -> dict[int, bool]:
    """For Mersenne primes ``M_p``: does ``M_p`` divide ``F_{M_p − (5 | M_p)}``?"""
    out: dict[int, bool] = {}
    for p in ps:
        M = mersenne_number(p)
        out[p] = fibonacci_mod(M - legendre_5(M), M) == 0
    return out


# --------------------------------------------------------------------------- rank of apparition
def fibonacci_rank_of_apparition(M: int, factors: dict[int, int] | None = None) -> int:
    """Smallest ``n > 0`` with ``M | F_n`` for a prime ``M ≠ 2, 5`` (needs the factorisation of
    ``N = M − (5 | M)``; computed with ``sympy.factorint`` when not supplied)."""
    N = M - legendre_5(M)
    if factors is None:
        import sympy

        factors = sympy.factorint(N)
    alpha = N
    for q in factors:
        while alpha % q == 0 and fibonacci_mod(alpha // q, M) == 0:
            alpha //= q
    return alpha


def mersenne_fibonacci_rank_is_2p(p: int) -> bool:
    """Theorem: for a Mersenne prime ``M_p`` with ``p ≡ 3 (mod 4)``, the Fibonacci rank of
    apparition of ``M_p`` is exactly ``2^p = M_p + 1``.

    Proof.  ``M_p ≡ 2 (mod 5)`` so ``(5 | M_p) = −1`` and ``α(M_p) | M_p + 1 = 2^p``.  Lucas's
    golden-seed test (seed 3 = L_2, valid for p ≡ 3 mod 4) says ``M_p | L_{2^{p−1}}``.  Since
    ``F_{2^p} = F_{2^{p−1}} · L_{2^{p−1}}`` we get ``M_p | F_{2^p}``, and since
    ``gcd(F_n, L_n) | 2`` we get ``M_p ∤ F_{2^{p−1}}``; hence ``α(M_p) = 2^p``. ∎

    This function checks the two divisibilities directly (no factoring needed).
    """
    if p % 4 != 3 or not is_prime_int(p):
        raise ValueError("stated for primes p ≡ 3 (mod 4)")
    M = mersenne_number(p)
    if not lucas_lehmer(p):
        raise ValueError(f"M_{p} is not prime")
    return fibonacci_mod(1 << p, M) == 0 and fibonacci_mod(1 << (p - 1), M) != 0 and lucas_number_mod(1 << (p - 1), M) == 0


def mersenne_fibonacci_rank_table(p_max_factor: int = 127, p_max_check: int = 4423) -> list[dict[str, object]]:
    """Rank of apparition data for known Mersenne primes: exact theorem check for
    ``p ≡ 3 (mod 4)`` up to ``p_max_check`` (no factoring), cofactor ``(M_p − 1)/α`` for
    ``p ≡ 1 (mod 4)`` up to ``p_max_factor`` (factoring ``2(2^{p−1} − 1)``)."""
    from core_math.mersenne import KNOWN_MERSENNE_EXPONENTS

    rows = []
    for p in KNOWN_MERSENNE_EXPONENTS:
        if p < 5:
            continue
        M = mersenne_number(p)
        if p % 4 == 3 and p <= p_max_check:
            rows.append({"p": p, "p_mod_4": 3, "alpha_is_2p": mersenne_fibonacci_rank_is_2p(p)})
        elif p % 4 == 1 and p <= p_max_factor:
            alpha = fibonacci_rank_of_apparition(M)
            rows.append({"p": p, "p_mod_4": 1, "cofactor": (M - 1) // alpha, "alpha_is_maximal": alpha == M - 1})
    return rows
