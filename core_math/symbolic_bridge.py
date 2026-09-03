"""Symbolic proof assistance: sympy bridges between the discrete Ψ / Mersenne world and
polynomial dynamics (the "Eight Levels" framework), with machine-checkable identities.

What is proved here
-------------------
* ``psi_poly(n)`` builds ``Ψ(a, b, n)`` as an exact bivariate polynomial; it is homogeneous
  of degree ``⌊n/2⌋`` (:func:`verify_homogeneity`).
* **Differential-operator identities** (Ibrahim, Theorems 33–35).  For a homogeneous
  polynomial ``P`` of degree ``m`` in ``(a, b)``, Euler's theorem gives
  ``(∂_a + c·∂_b)^m P = m!·P(1, c)``.  Hence
  ``(1/m!)(∂_a + 4∂_b)^m Ψ(a, b, n) = Ψ(1, 4, n)`` (the Lucas–Lehmer numbers),
  ``(1/m!)(∂_a + 3∂_b)^m Ψ(a, b, n) = Ψ(1, 3, n) = (−1)^m L_n`` (Lucas numbers), and
  ``(1/m!)(∂_a + (φ−1)∂_b)^m Ψ(a, b, n) = Ψ(1, φ−1, n)``, which equals ``−φ`` for
  ``n = 2^l`` with ``l`` even (and, as shown in :mod:`core_math.psi_sequence`, for
  ``n = 2^{p−1}`` with every odd prime ``p``).
* **Normalisation identity** ``Ψ(a, b, n) = (2a − b)^{⌊n/2⌋}·V_n(1, a/(2a − b))`` as an
  exact rational-function identity for each ``n`` (:func:`normalisation_identity`), with
  the general Binet proof in :func:`normalisation_proof_sketch`.
* **Chebyshev / Dickson** links as exact polynomial identities.
* **Ring parameters are roots of the small Ψ-polynomials**: ``Ψ(1, b, 5) = b² + b − 1``
  has roots ``φ − 1`` and ``−φ`` — the period-20 golden rings; ``Ψ(1, b, 4) = b² − 2`` gives
  ``±√2`` (period 16); ``Ψ(1, b, 6) = 3b − b³`` gives ``0, ±√3`` (periods 8 and 24);
  ``Ψ(1, b, 3) = −1 − b`` gives ``−1`` (period 12); ``Ψ(1, b, 2) = −b`` gives ``0``.
* **No universal golden seed** for Lucas–Lehmer: ``(5 | M_p) = +1`` exactly when
  ``p ≡ 1 (mod 4)``, so a seed built in ``Q(√5)`` (such as ``3 = φ² + ψ²``) cannot work for
  every ``p`` — unlike ``Q(√3)`` where ``(3 | M_p) = −1`` always.

Equality of expressions involving ``√5``/``φ`` is decided by exact simplification after
rewriting ``GoldenRatio`` as ``(1 + √5)/2``; a 60-digit numeric evaluation is used as a
fallback only when sympy cannot reduce the difference symbolically.
"""
from __future__ import annotations

import math
from typing import Any

import sympy as sp

from core_math.psi_sequence import delta, lucas, psi

a, b, x, alpha, theta = sp.symbols("a b x alpha theta")
PHI_S = sp.GoldenRatio


# --------------------------------------------------------------------------- helpers
def is_zero(expr: Any) -> bool:
    """Decide ``expr == 0`` symbolically (rewriting ``φ → (1+√5)/2``), numeric fallback."""
    e = sp.expand(sp.sympify(expr).rewrite(sp.sqrt))
    if e == 0:
        return True
    e2 = sp.simplify(sp.radsimp(e))
    if e2 == 0:
        return True
    if e2.free_symbols:          # a genuinely non-zero expression in free symbols
        return False
    return bool(abs(sp.N(e2, 60)) < sp.Float(10) ** -40)


# --------------------------------------------------------------------------- Ψ as polynomials
def psi_expr(n: int) -> sp.Expr:
    """``Ψ(a, b, n)`` as an expanded sympy expression in ``a, b``."""
    return sp.expand(psi(a, b, n))


def psi_poly(n: int) -> sp.Poly:
    """``Ψ(a, b, n)`` as a ``sympy.Poly`` in ``(a, b)``."""
    return sp.Poly(psi_expr(n), a, b)


def psi_b_poly(n: int) -> sp.Poly:
    """``Ψ(1, b, n)`` as a univariate polynomial in ``b``."""
    return sp.Poly(sp.expand(psi(1, b, n)), b)


def psi_b_roots(n: int) -> list[sp.Expr]:
    """Real roots of ``Ψ(1, b, n)`` in closed form, sorted numerically."""
    roots = [sp.radsimp(r) for r in sp.roots(psi_b_poly(n), multiple=True)]
    real = [r for r in roots if r.is_real]
    return sorted(real, key=lambda r: float(r))


def ring_parameter_roots() -> dict[int, list[sp.Expr]]:
    """Roots of ``Ψ(1, b, n)`` for ``n = 2 … 6``: exactly the periodic ring parameters."""
    return {n: psi_b_roots(n) for n in range(2, 7)}


def verify_homogeneity(n: int) -> bool:
    """Euler: ``a·∂_a Ψ + b·∂_b Ψ = ⌊n/2⌋·Ψ``."""
    P = psi_expr(n)
    return sp.expand(a * sp.diff(P, a) + b * sp.diff(P, b) - (n // 2) * P) == 0


def verify_explicit(n: int) -> bool:
    """Theorem 9 explicit sum equals the recurrence, as polynomials."""
    m = n // 2
    total = sum(
        sp.Rational(n, n - i) * sp.binomial(n - i, i) * (-a) ** i * (2 * a - b) ** (m - i)
        for i in range(m + 1)
    ) if n > 0 else sp.Integer(2)
    return sp.expand(total - psi_expr(n)) == 0


def verify_closed_form(n: int, points: tuple[tuple[int, int], ...] = ((1, 4), (2, 5), (-1, -3), (3, 1))) -> bool:
    """Equation 36 at exact rational points (radicals handled symbolically)."""
    for aa, bb in points:
        if bb == 2 * aa:
            continue
        s = sp.Rational(bb + 2 * aa, bb - 2 * aa)
        r = sp.sqrt(s)
        closed = sp.Rational(2 * aa - bb) ** (n // 2) / sp.Integer(2) ** n * ((1 + r) ** n + (1 - r) ** n)
        if not is_zero(closed - psi(aa, bb, n)):
            return False
    return True


# --------------------------------------------------------------------------- Lucas normalisation
def lucas_v_expr(P: Any, Q: Any, n: int) -> sp.Expr:
    if n == 0:
        return sp.Integer(2)
    prev, cur = sp.Integer(2), sp.sympify(P)
    for _ in range(n - 1):
        prev, cur = cur, sp.expand(P * cur - Q * prev)
    return cur


def normalisation_identity(n: int) -> bool:
    """``Ψ(a, b, n) = (2a − b)^{⌊n/2⌋}·V_n(1, a/(2a − b))`` as an exact identity in ``a, b``."""
    Q = a / (2 * a - b)
    rhs = (2 * a - b) ** (n // 2) * lucas_v_expr(1, Q, n)
    return sp.cancel(sp.together(rhs - psi_expr(n))) == 0


def normalisation_proof_sketch() -> str:
    """Binet-style proof of the normalisation identity for all ``n``."""
    return (
        "Let t = 2a − b ≠ 0 and s = (b + 2a)/(b − 2a).  Put x0, y0 = (1 ± √s)/2.  Then x0 + y0 = 1 and "
        "x0·y0 = (1 − s)/4 = a/t.  Equation 36 reads Ψ(a,b,n) = t^{⌊n/2⌋} (x0^n + y0^n), and x0^n + y0^n "
        "is the Lucas V-sequence V_n(P, Q) with P = x0 + y0 = 1, Q = x0·y0 = a/t.  Both sides satisfy the "
        "same two-step recurrence with the same initial values, which gives the identity for every n."
    )


# --------------------------------------------------------------------------- differential operators
def directional_operator(n: int, c: Any) -> sp.Expr:
    """``(1/m!)·(∂_a + c·∂_b)^m Ψ(a, b, n)`` with ``m = ⌊n/2⌋`` (a constant by homogeneity)."""
    m = n // 2
    expr = psi_expr(n)
    for _ in range(m):
        expr = sp.expand(sp.diff(expr, a) + c * sp.diff(expr, b))
    return sp.expand(expr / sp.factorial(m))


def verify_directional_identity(n: int, c: Any) -> bool:
    """``(1/m!)(∂_a + c∂_b)^m Ψ(a, b, n) = Ψ(1, c, n)`` (Theorems 33–34 via Euler)."""
    return is_zero(directional_operator(n, c) - psi(1, sp.sympify(c), n))


def verify_operator_gives_lucas_lehmer(n: int) -> bool:
    return is_zero(directional_operator(n, 4) - psi(1, 4, n))


def verify_operator_gives_lucas_numbers(n: int) -> bool:
    """``c = 3``: the operator yields ``(−1)^{⌊n/2⌋}·L_n`` — plain ``L_n`` when ``n = 2^l, l ≥ 2``."""
    return is_zero(directional_operator(n, 3) - (-1) ** (n // 2) * lucas(n))


def verify_operator_golden(n: int) -> bool:
    """``c = φ − 1`` and ``n = 2^l`` with ``l`` even: the operator yields ``−φ``."""
    lg = int(round(math.log2(n)))
    if 2 ** lg != n or lg % 2:
        raise ValueError("stated for n = 2^l with l even")
    return is_zero(directional_operator(n, PHI_S - 1) + PHI_S)


# --------------------------------------------------------------------------- classical polynomials
def verify_chebyshev(n: int) -> bool:
    """``T_n(x) = x^{δ(n)} / 2^{δ(n+1)} · Ψ(1, 2 − 4x², n)``."""
    rhs = x ** delta(n) / sp.Integer(2) ** delta(n + 1) * psi(1, 2 - 4 * x**2, n)
    return sp.expand(sp.chebyshevt(n, x) - rhs) == 0


def dickson_expr(n: int) -> sp.Expr:
    """Dickson polynomial of the first kind ``D_n(x, α)``."""
    if n == 0:
        return sp.Integer(2)
    prev, cur = sp.Integer(2), x
    for _ in range(n - 1):
        prev, cur = cur, sp.expand(x * cur - alpha * prev)
    return cur


def verify_dickson(n: int) -> bool:
    """``D_n(x, α) = x^{δ(n)} · Ψ(α, 2α − x², n)``."""
    return sp.expand(dickson_expr(n) - x ** delta(n) * psi(alpha, 2 * alpha - x**2, n)) == 0


# --------------------------------------------------------------------------- rotation form
def verify_trig_form(n: int) -> bool:
    """``Ψ(1, −2cos 2θ, n) = 2cos nθ`` (n even) or ``cos nθ / cos θ`` (n odd), symbolically in ``θ``."""
    expr = sp.expand(sp.sympify(psi(1, -2 * sp.cos(2 * theta), n)))
    target = 2 * sp.cos(n * theta) if n % 2 == 0 else sp.cos(n * theta) / sp.cos(theta)
    diff = sp.simplify(sp.expand_trig(expr - target))
    if diff == 0:
        return True
    # fall back to exact evaluation at a few rational multiples of π
    return all(sp.simplify(diff.subs(theta, sp.pi * sp.Rational(k, 7))) == 0 for k in (1, 2, 3))


# --------------------------------------------------------------------------- golden ratio
def golden_period_table_symbolic() -> list[sp.Expr]:
    """``Ψ(1, φ − 1, n)`` for ``n = 0 … 19`` in terms of ``GoldenRatio``, simplified."""
    out = []
    for n in range(20):
        e = sp.expand(sp.sympify(psi(1, PHI_S - 1, n)).rewrite(sp.sqrt))
        e = sp.nsimplify(sp.simplify(e), [sp.GoldenRatio])
        out.append(e)
    return out


def no_universal_golden_seed(p_max: int = 500) -> bool:
    """``(5 | M_p) = +1 ⟺ p ≡ 1 (mod 4)`` for odd primes ``p ≤ p_max``.

    ``2^p mod 5`` cycles ``2, 4, 3, 1`` with ``p mod 4``, so ``M_p ≡ 1 (mod 5)`` for
    ``p ≡ 1 (mod 4)`` (5 is a residue: the golden seed fails) and ``M_p ≡ 2 (mod 5)`` for
    ``p ≡ 3 (mod 4)`` (5 is a non-residue: the golden seed ``3 = L_2`` works).
    """
    for p in sp.primerange(3, p_max + 1):
        residue = (2**p - 1) % 5
        legendre = sp.legendre_symbol(residue, 5)
        if (legendre == 1) != (p % 4 == 1):
            return False
    return True


# --------------------------------------------------------------------------- report
def bridge_report(n_max: int = 12) -> dict[str, bool]:
    """Run every symbolic verification; all values should be ``True``."""
    ns = range(1, n_max + 1)
    report: dict[str, bool] = {
        "homogeneity": all(verify_homogeneity(n) for n in ns),
        "explicit_formula": all(verify_explicit(n) for n in ns),
        "closed_form": all(verify_closed_form(n) for n in ns),
        "normalisation_identity": all(normalisation_identity(n) for n in ns),
        "operator_lucas_lehmer": all(verify_operator_gives_lucas_lehmer(n) for n in ns),
        "operator_lucas_numbers": all(verify_operator_gives_lucas_numbers(n) for n in ns),
        "operator_golden_n4_n16": verify_operator_golden(4) and verify_operator_golden(16),
        "chebyshev": all(verify_chebyshev(n) for n in ns),
        "dickson": all(verify_dickson(n) for n in ns),
        "no_universal_golden_seed": no_universal_golden_seed(),
        "rotation_form": all(verify_trig_form(n) for n in range(1, min(n_max, 8) + 1)),
    }
    roots = ring_parameter_roots()
    expected: dict[int, list[sp.Expr]] = {
        2: [sp.Integer(0)],
        3: [sp.Integer(-1)],
        4: [-sp.sqrt(2), sp.sqrt(2)],
        5: [-PHI_S, PHI_S - 1],
        6: [-sp.sqrt(3), sp.Integer(0), sp.sqrt(3)],
    }
    report["ring_roots"] = all(
        len(roots[n]) == len(exp) and all(is_zero(r - e) for r, e in zip(roots[n], exp, strict=True))
        for n, exp in expected.items()
    )
    return report
