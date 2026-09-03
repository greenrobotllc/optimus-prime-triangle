"""The Quanta Prime Sequence (QPS) of Ibrahim, arXiv:2502.06796.

Definition 6.1 (double-indexed sequence)::

    Ω_r(0 | ζ, ξ | n) = 1                                   for all r,
    Ω_r(k | ζ, ξ | n) = (2ζ − ξ)(n − r − k) · Ω_r(k−1)  −  2ζ (n − 2r − δ(n−1)) · Ω_{r+1}(k−1).

Theorem 25 ties it to the Ψ-sequence::

    Ω_0(⌊n/2⌋ | α, β | n) / ((n−1)(n−2)⋯(n−⌊n/2⌋)) = Ψ(α, β, n).

Two named special cases appear in the paper:

* ``A_r(k) = (p − r − k)·A_r(k−1) + 4(p − 2r)·A_{r+1}(k−1)`` is ``Ω`` at ``(ζ, ξ) = (−2, −5)``
  with ``n = p`` (odd), and Theorem 11 states ``2^p − 1 = A_0(⌊p/2⌋)/((p−1)⋯(p−⌊p/2⌋))``.
  By Theorem 25 this is just ``Ψ(−2, −5, p) = 2^p + (−1)^p``.
* ``B_r(k) = −2(n − r − k)·B_r(k−1) − 2(n − 2r − 1)·B_{r+1}(k−1)`` is ``Ω`` at ``(1, 4)`` with
  ``n = 2^{p−1}`` (even), and Theorem 9 states that ``2^p − 1`` is prime iff the A-ratio
  divides the B-ratio.  Because the B-ratio equals ``Ψ(1, 4, 2^{p−1})``, Theorem 9 is
  Theorem 26 of the Eight Levels paper, which is the Lucas–Lehmer test.

The recurrences are evaluated exactly with a rolling column of Python integers:
layer ``k`` needs ``r = 0 … K − k`` only, so memory is ``O(K)`` and time ``O(K²)`` where
``K = ⌊n/2⌋``.  For the B-sequence ``K = 2^{p−2}``, so the direct QPS primality check is
exponential in ``p`` and is only offered for ``p ≤ 13`` as a verification of the theory.
"""
from __future__ import annotations

import math
from fractions import Fraction

from core_math.psi_sequence import delta

QPS_PRIMALITY_MAX_P = 13


def falling_denominator(n: int, k: int) -> int:
    """``(n − 1)(n − 2) ⋯ (n − k)``; equals 1 for ``k = 0``."""
    out = 1
    for j in range(1, k + 1):
        out *= n - j
    return out


def omega_layer(zeta: int, xi: int, n: int, k: int, r_max: int) -> list[int]:
    """The list ``[Ω_r(k | ζ, ξ | n) for r in 0..r_max]`` by rolling over ``k``."""
    c = 2 * zeta - xi
    shift = delta(n - 1)
    layer = [1] * (r_max + k + 1)           # Ω_r(0) = 1 for every r we will ever need
    for kk in range(1, k + 1):
        width = r_max + k - kk + 1
        new = [0] * width
        for r in range(width):
            new[r] = c * (n - r - kk) * layer[r] - 2 * zeta * (n - 2 * r - shift) * layer[r + 1]
        layer = new
    return layer[: r_max + 1]


def omega(r: int, k: int, zeta: int, xi: int, n: int) -> int:
    """``Ω_r(k | ζ, ξ | n)``."""
    return omega_layer(zeta, xi, n, k, r)[r]


def omega_ratio(zeta: int, xi: int, n: int) -> Fraction:
    """``Ω_0(⌊n/2⌋ | ζ, ξ | n) / ((n−1)⋯(n−⌊n/2⌋))`` as an exact fraction."""
    K = n // 2
    return Fraction(omega_layer(zeta, xi, n, K, 0)[0], falling_denominator(n, K))


def psi_via_qps(zeta: int, xi: int, n: int) -> int:
    """Theorem 25: the QPS ratio equals ``Ψ(ζ, ξ, n)`` (``n ≥ 1``; raises if not integral)."""
    if n < 1:
        raise ValueError("Theorem 25 is stated for n >= 1")
    ratio = omega_ratio(zeta, xi, n)
    if ratio.denominator != 1:
        raise ArithmeticError(f"QPS ratio is not an integer for (ζ, ξ, n) = {(zeta, xi, n)}")
    return int(ratio)


# --------------------------------------------------------------------------- A and B sequences
def a_sequence_value(r: int, k: int, p: int) -> int:
    """``A_r(k)`` for exponent ``p`` — ``Ω_r(k | −2, −5 | p)``."""
    return omega(r, k, -2, -5, p)


def b_sequence_value(r: int, k: int, p: int) -> int:
    """``B_r(k)`` for exponent ``p`` — ``Ω_r(k | 1, 4 | 2^{p−1})``."""
    return omega(r, k, 1, 4, 1 << (p - 1))


def a_ratio(p: int) -> Fraction:
    """Theorem 11 numerator/denominator: ``A_0(⌊p/2⌋) / ((p−1)⋯(p−⌊p/2⌋))``."""
    return omega_ratio(-2, -5, p)


def b_ratio(p: int) -> Fraction:
    """Theorem 9 right-hand side: ``B_0(⌊n/2⌋) / ((n−1)⋯(n−⌊n/2⌋))`` with ``n = 2^{p−1}``."""
    if p > QPS_PRIMALITY_MAX_P:
        raise ValueError(f"B-ratio has 2^(p-2) layers; refusing p={p} > {QPS_PRIMALITY_MAX_P}")
    return omega_ratio(1, 4, 1 << (p - 1))


def mersenne_via_qps(p: int) -> int:
    """Theorem 11: ``2^p − 1`` from the A-sequence (odd prime ``p``)."""
    ratio = a_ratio(p)
    if ratio.denominator != 1:
        raise ArithmeticError("A-ratio is not an integer")
    return int(ratio)


def qps_primality(p: int) -> bool:
    """Theorem 9: ``2^p − 1`` is prime iff the A-ratio divides the B-ratio.

    Exponential cost — verification only (``p ≤ 13``).  Equivalent to Lucas–Lehmer.
    """
    if p < 5:
        raise ValueError("Theorem 9 is stated for primes p >= 5")
    a = a_ratio(p)
    b = b_ratio(p)
    if a.denominator != 1 or b.denominator != 1:
        raise ArithmeticError("QPS ratios must be integers")
    return int(b) % int(a) == 0


# --------------------------------------------------------------------------- closed forms for the whole table
# The following identities were found in this repository (2026-09-02) and are not stated in the
# QPS paper, which gives explicit Ω formulas only at the three points (1, −2), (1, 2), (0, −1).
# They are elementary (binomial sums / a terminating ₂F₁ / Gegenbauer polynomials) and are
# proved by induction on k; see tests/test_qps.py for the exact verification ranges.
# Notation: x^{m↓} = x (x − 1) ⋯ (x − m + 1) is the falling factorial.

def falling(x: int, length: int) -> int:
    """``x (x − 1) ⋯ (x − length + 1)``; empty product = 1."""
    out = 1
    for i in range(length):
        out *= x - i
    return out


def double_falling(u: int, j: int) -> int:
    """``u (u − 2) (u − 4) ⋯ (u − 2j + 2)``; empty product = 1."""
    out = 1
    for i in range(j):
        out *= u - 2 * i
    return out


def omega_closed_form(r: int, k: int, zeta: int, xi: int, n: int) -> int:
    """Closed form for the whole QPS table (valid for all ``n ≥ 1``, ``r, k ≥ 0``)::

        Ω_r(k | ζ, ξ | n) = Σ_{j=0}^{k} C(k, j) (2ζ − ξ)^{k−j} (−2ζ)^j · (N−j−1)^{^{k−j↓}} · u(u−2)⋯(u−2j+2)

    with ``N = n − r`` and ``u = n − 2r − δ(n−1)``.  In particular Ω depends on ``(n, r)`` only
    through ``(N, u)``, which yields the shift identity :func:`omega_shift_holds`.
    """
    N = n - r
    u = n - 2 * r - delta(n - 1)
    c = 2 * zeta - xi
    return sum(math.comb(k, j) * c ** (k - j) * (-2 * zeta) ** j * falling(N - j - 1, k - j) * double_falling(u, j)
               for j in range(k + 1))


def _pochhammer(x: Fraction, j: int) -> Fraction:
    out = Fraction(1)
    for i in range(j):
        out *= x + i
    return out


def omega_hypergeometric(r: int, k: int, zeta: int, xi: int, n: int) -> Fraction:
    """Terminating ``₂F₁`` form (needs ``2ζ ≠ ξ`` and ``k ≤ n − r − 1``)::

        Ω_r(k) = (2ζ − ξ)^k (N−1)^{k↓} · ₂F₁(−k, −u/2; 1 − N; 4ζ/(2ζ − ξ)).
    """
    N = n - r
    u = n - 2 * r - delta(n - 1)
    c = 2 * zeta - xi
    if c == 0 or k > N - 1:
        raise ValueError("hypergeometric form needs 2ζ ≠ ξ and k ≤ n − r − 1")
    z = Fraction(4 * zeta, c)
    total = Fraction(0)
    for j in range(k + 1):
        total += _pochhammer(Fraction(-k), j) * _pochhammer(Fraction(-u, 2), j) / (_pochhammer(Fraction(1 - N), j) * math.factorial(j)) * z ** j
    return c ** k * falling(N - 1, k) * total


def omega_column_delta_explicit(k: int, zeta: int, xi: int, n: int) -> Fraction:
    """The column ``r = δ(n)`` as a polynomial in ``ζ²`` and ``ξ`` (``K = ⌊n/2⌋``, ``0 ≤ k ≤ K``)::

        Ω_{δ(n)}(k) = (−1)^k (2K−1)^{k↓} Σ_{i=0}^{⌊k/2⌋} C(k, 2i) (2i)! / (i! (K−1)^{i↓}) (−ζ²)^i ξ^{k−2i}.

    Consequence (parity law): ``Ω_{δ(n)}(k | ζ, −ξ | n) = (−1)^k Ω_{δ(n)}(k | ζ, ξ | n)``.
    """
    K = n // 2
    total = Fraction(0)
    for i in range(k // 2 + 1):
        total += Fraction(math.comb(k, 2 * i) * math.factorial(2 * i), math.factorial(i) * falling(K - 1, i)) * (-zeta * zeta) ** i * xi ** (k - 2 * i)
    return (-1) ** k * falling(2 * K - 1, k) * total


def omega_gegenbauer(k: int, zeta: int, xi: int, n: int):
    """Gegenbauer form of the ``r = δ(n)`` column for ``1 ≤ k ≤ K − 1`` (sympy)::

        Ω_{δ(n)}(k) = (−ζ)^k k! (2K−1)^{k↓} / (K−1)^{k↓} · C_k^{(K−k)}(ξ / 2ζ).
    """
    import sympy as sp

    K = n // 2
    if not 1 <= k <= K - 1 or zeta == 0:
        raise ValueError("Gegenbauer form is stated for 1 ≤ k ≤ K − 1 and ζ ≠ 0")
    value = (-zeta) ** k * sp.factorial(k) * sp.Rational(falling(2 * K - 1, k), falling(K - 1, k)) * sp.gegenbauer(k, K - k, sp.Rational(xi, 2 * zeta))
    return sp.nsimplify(sp.expand(value))


def omega_shift_holds(n: int, zeta: int, xi: int) -> bool:
    """Shift identity: for odd ``n``, ``Ω_{r+1}(k | n) = Ω_r(k | n − 1)`` for all ``r, k``."""
    if n % 2 == 0:
        raise ValueError("the shift identity is stated for odd n")
    K = n // 2
    return all(omega(r + 1, k, zeta, xi, n) == omega(r, k, zeta, xi, n - 1)
               for k in range(K + 1) for r in range(K - k + 2))


def star_even_symmetry_holds(n: int) -> bool:
    """Lemma 7.4 of the Mersenne Star paper, ``Ω_0(⌊n/2⌋|−1,4|n) = Ω_0(⌊n/2⌋|1,4|n) = Ω_0(⌊n/2⌋|1,−4|n)``,
    is stated for ``8 | n`` but holds exactly for all ``4 | n`` (and ``n = 1``)."""
    K = n // 2
    return omega(0, K, -1, 4, n) == omega(0, K, 1, 4, n) == omega(0, K, 1, -4, n)
