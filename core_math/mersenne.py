"""Mersenne numbers, the Lucas–Lehmer test and classical pre-sieving helpers.

Everything in this module works on Python ``int`` so that exponents in the tens of
thousands are exact.  Nothing here imports the machine-learning code: the
Lucas–Lehmer result is the *label* of the siever and must never leak into features.

Mathematical background
-----------------------
Mersenne numbers are ``M_p = 2^p − 1``.  For ``M_p`` to be prime, ``p`` must be prime.

**Lucas–Lehmer test (Lucas 1878, Lehmer 1930).**  With ``s_0 = 4`` and
``s_{k+1} = s_k² − 2 (mod M_p)``, an odd prime ``p`` gives a prime ``M_p`` if and only
if ``s_{p−2} ≡ 0 (mod M_p)``.  The closed form is ``s_k = ω^{2^k} + ω̄^{2^k}`` with
``ω = 2 + √3``; the test lives in the ring ``Z[√3]``, and ``3`` is a quadratic
non-residue modulo every ``M_p`` (``M_p ≡ 7 (mod 12)``), which is why the seed 4 is
universal.  Other universal seeds are 10 and 52 (OEIS A018844).

**Golden-ratio seed.**  The seed ``s_0 = 3 = L_2`` yields ``s_k = L_{2^{k+1}}``,
the Lucas numbers ``L_n = φ^n + ψ^n`` (``φ = (1+√5)/2``).  It is valid exactly when
``p ≡ 3 (mod 4)``: then ``M_p ≡ 2 (mod 5)`` and 5 is a non-residue modulo ``M_p``.  For
``p ≡ 1 (mod 4)`` we have ``M_p ≡ 1 (mod 5)``, 5 becomes a residue and the seed fails
(``p = 5`` is the smallest counterexample).  This is the one genuine bridge between the
golden ratio and Mersenne primality; it is also Lucas's original 1876 route to M_127.

**Ψ-sequence connection (Ibrahim, arXiv:2404.05772).**  ``Ψ(1, 4, 2^k)`` equals the
Lucas–Lehmer term ``s_{k−1}``, so Ibrahim's Theorem 26 (``2^p − 1`` prime iff
``2^p − 1 | Ψ(1, 4, 2^{p−1})``) is the Lucas–Lehmer test in different clothing.
See :mod:`core_math.psi_sequence`.

**Pre-sieving facts used by :func:`trial_factor` and :func:`sophie_germain_factor`.**
Every prime factor ``q`` of ``M_p`` (``p`` an odd prime) satisfies ``q ≡ 1 (mod 2p)`` and
``q ≡ ±1 (mod 8)``.  If ``p ≡ 3 (mod 4)`` and ``2p + 1`` is prime (``p`` a Sophie Germain
prime) then ``2p + 1`` divides ``M_p`` (Euler), so ``M_p`` is composite for ``p > 3``.

**Wagstaff heuristic (1983).**  The probability that ``M_p`` is prime is roughly
``e^γ · ln(a·p) / (p · ln 2)`` with ``a = 2`` when ``p ≡ 3 (mod 4)`` and ``a = 6``
otherwise.  It is the honest baseline every "smart siever" must beat.
"""
from __future__ import annotations

import math
from typing import Iterator

EULER_GAMMA: float = 0.5772156649015329

#: Exponents of all known Mersenne primes (GIMPS / Wikipedia, table dated 2024-10-21).
KNOWN_MERSENNE_EXPONENTS: tuple[int, ...] = (
    2, 3, 5, 7, 13, 17, 19, 31, 61, 89, 107, 127, 521, 607, 1279, 2203, 2281, 3217,
    4253, 4423, 9689, 9941, 11213, 19937, 21701, 23209, 44497, 86243, 110503, 132049,
    216091, 756839, 859433, 1257787, 1398269, 2976221, 3021377, 6972593, 13466917,
    20996011, 24036583, 25964951, 30402457, 32582657, 37156667, 42643801, 43112609,
    57885161, 74207281, 77232917, 82589933, 136279841,
)
#: Ranks whose position is provisional (GIMPS has not finished the gap below them).
PROVISIONAL_RANKS: tuple[int, ...] = (51, 52)
KNOWN_TABLE_DATE: str = "2024-10-21"
_KNOWN_SET = frozenset(KNOWN_MERSENNE_EXPONENTS)

#: Seeds proven to work for every odd prime exponent (OEIS A018844, first three).
UNIVERSAL_LL_SEEDS: tuple[int, ...] = (4, 10, 52)

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)   # 13 bases: deterministic below 3.3·10^24
_MR_DETERMINISTIC_BOUND = 3_317_044_064_679_887_385_961_981


# --------------------------------------------------------------------------- primes
def is_prime_int(n: int) -> bool:
    """Deterministic primality for ``n < 3.3·10^24`` (Miller–Rabin with the first 13 prime bases);
    delegates to ``sympy.isprime`` beyond that bound."""
    if n < 2:
        return False
    for q in _MR_BASES:
        if n % q == 0:
            return n == q
    if n >= _MR_DETERMINISTIC_BOUND:
        from sympy import isprime  # local import keeps the fast path import-free

        return bool(isprime(n))
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


is_probable_prime = is_prime_int  # alias used by the research modules


def sieve_primes(limit: int) -> list[int]:
    """All primes ``≤ limit`` by a byte sieve."""
    if limit < 2:
        return []
    flags = bytearray([1]) * (limit + 1)
    flags[0] = flags[1] = 0
    for i in range(2, math.isqrt(limit) + 1):
        if flags[i]:
            flags[i * i :: i] = bytes(len(range(i * i, limit + 1, i)))
    return [i for i, f in enumerate(flags) if f]


def prime_exponents(p_min: int = 2, p_max: int = 2500) -> list[int]:
    """Prime candidate exponents in ``[p_min, p_max]``."""
    return [q for q in sieve_primes(p_max) if q >= p_min]


# --------------------------------------------------------------------------- Mersenne numbers
def mersenne_number(p: int) -> int:
    """``M_p = 2^p − 1``."""
    if p < 1:
        raise ValueError("p must be a positive integer")
    return (1 << p) - 1


def wagstaff_number(p: int) -> int:
    """``W_p = (2^p + 1) / 3`` for odd ``p ≥ 3``; note ``Ψ(2, −5, p) = W_p``."""
    if p < 3 or p % 2 == 0:
        raise ValueError("Wagstaff numbers need an odd exponent p >= 3")
    return ((1 << p) + 1) // 3


def iter_mersenne_numbers(p_max: int, prime_exponents_only: bool = True) -> Iterator[tuple[int, int]]:
    """Yield ``(p, M_p)`` for ``p ≤ p_max``."""
    ps = prime_exponents(2, p_max) if prime_exponents_only else range(1, p_max + 1)
    for p in ps:
        yield p, mersenne_number(p)


def is_known_mersenne_exponent(p: int) -> bool:
    """Membership in the known table (used only for labels and plotting)."""
    return p in _KNOWN_SET


# --------------------------------------------------------------------------- Lucas–Lehmer
def mod_mersenne(x: int, p: int) -> int:
    """``x mod (2^p − 1)`` using the shift-and-add reduction ``x ↦ (x & M) + (x >> p)``.

    Because ``2^p ≡ 1 (mod M_p)`` the high bits fold onto the low bits; two folds
    suffice for ``x < M_p²``.  Negative inputs fall back to ``%``.
    """
    m = (1 << p) - 1
    if x < 0:
        x %= m
    while x > m:
        x = (x & m) + (x >> p)
    return 0 if x == m else x


def _validate_ll_inputs(p: int, s0: int) -> None:
    if p < 3 or not is_prime_int(p):
        raise ValueError(f"Lucas–Lehmer needs an odd prime exponent, got p={p}")
    if s0 == 3 and p % 4 != 3:
        raise ValueError(
            "seed 3 (the golden-ratio seed s_k = L_{2^{k+1}}) is only valid for p ≡ 3 (mod 4): "
            f"for p={p} we have M_p ≡ 1 (mod 5), so 5 is a quadratic residue and the test fails"
        )


def lucas_lehmer_sequence(p: int, s0: int = 4, reduce: bool = True) -> list[int]:
    """The terms ``s_0, …, s_{p−2}`` of the Lucas–Lehmer recurrence for ``M_p``.

    With ``reduce=False`` the raw integers are returned (``4, 14, 194, 37634, …`` for
    seed 4; ``3, 7, 47, 2207, …`` = ``L_2, L_4, L_8, L_16, …`` for seed 3).
    """
    _validate_ll_inputs(p, s0)
    s = s0
    seq = [s]
    for _ in range(p - 2):
        s = s * s - 2
        if reduce:
            s = mod_mersenne(s, p)
        seq.append(s)
    return seq


def lucas_lehmer_residue(p: int, s0: int = 4) -> int:
    """``s_{p−2} mod M_p``; zero exactly when ``M_p`` is prime (for a valid seed)."""
    _validate_ll_inputs(p, s0)
    m = (1 << p) - 1
    s = s0 % m
    for _ in range(p - 2):
        s = mod_mersenne(s * s - 2, p)
    return s


def lucas_lehmer(p: int, s0: int = 4) -> bool:
    """Is ``M_p`` prime?  ``p = 2`` is handled as the special case ``M_2 = 3``."""
    if p == 2:
        return True
    return lucas_lehmer_residue(p, s0) == 0


# --------------------------------------------------------------------------- pre-sieving
def trial_factor(p: int, k_max: int = 64) -> int | None:
    """Smallest factor ``q = 2kp + 1`` of ``M_p`` with ``k ≤ k_max``, or ``None``.

    Only ``q ≡ ±1 (mod 8)`` are tried.  The first hit is automatically prime, because a
    composite hit would have a prime factor of the same shape with a smaller ``k``.
    """
    if p < 3 or p % 2 == 0:
        return None
    m = (1 << p) - 1
    for k in range(1, k_max + 1):
        q = 2 * k * p + 1
        if q >= m:
            return None
        if q % 8 in (1, 7) and pow(2, p, q) == 1:
            return q
    return None


def sophie_germain_factor(p: int) -> bool:
    """True iff ``p > 3``, ``p ≡ 3 (mod 4)`` and ``2p + 1`` is prime, in which case
    ``2p + 1 | M_p`` (checked) and ``M_p`` is composite."""
    if p <= 3 or p % 4 != 3:
        return False
    q = 2 * p + 1
    return is_prime_int(q) and pow(2, p, q) == 1


def wagstaff_probability(p: int) -> float:
    """Wagstaff's heuristic probability that ``M_p`` is prime, clipped to ``[0, 1]``."""
    if p < 2:
        return 0.0
    a = 2.0 if p % 4 == 3 else 6.0
    value = math.exp(EULER_GAMMA) * math.log(a * p) / (p * math.log(2.0))
    return min(1.0, max(0.0, value))
