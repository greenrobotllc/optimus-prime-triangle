"""The Ψ-sequence of Ibrahim's Eight Levels theorem, exact quadratic-ring arithmetic,
and the periodic "ring" tables that drive the Mersenne Star geometry.

Definitions (Ibrahim, arXiv:2404.05772)
---------------------------------------
Definition 4.1::

    Ψ(a, b, 0) = 2,  Ψ(a, b, 1) = 1,
    Ψ(a, b, n + 1) = (2a − b)^{δ(n)} · Ψ(a, b, n) − a · Ψ(a, b, n − 1),   δ(n) = n mod 2.

Theorem 9 (explicit form)::

    Ψ(a, b, n) = Σ_{i=0}^{⌊n/2⌋} n/(n−i) · C(n−i, i) · (−a)^i · (2a − b)^{⌊n/2⌋ − i}.

Equation 36 (closed form)::

    Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} / 2^n · [ (1 + √s)^n + (1 − √s)^n ],   s = (b + 2a)/(b − 2a).

Lehmer identification (verified here; the definitive classical reference)
--------------------------------------------------------------------------
``Ψ(a, b, n)`` is exactly D. H. Lehmer's companion sequence ``V̄_n(√R, Q)`` with ``R = 2a − b``
and ``Q = a`` (An extended theory of Lucas' functions, Annals of Math. 31, 1930): ``V̄_n = V_n``
for even ``n`` and ``V_n/√R`` for odd ``n`` where ``V_n = α^n + β^n``, ``α + β = √R``, ``αβ = Q``.
See :func:`lehmer_companion_bar` / :func:`psi_via_lehmer`.  Every property of the Ψ family is a
property of Lehmer sequences.

Normalisation identity (verified here, classical in substance)
--------------------------------------------------------------
Let ``V_n(P, Q)`` be the Lucas V-sequence ``V_0 = 2, V_1 = P, V_{n+1} = P·V_n − Q·V_{n−1}``.
Then::

    Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a / (2a − b)).

Proof sketch: the closed form's two roots ``x_0, y_0 = ½(1 ± √s)`` satisfy ``x_0 + y_0 = 1``
and ``x_0·y_0 = a/(2a − b)`` (eq. 88 of the paper), so ``x_0^n + y_0^n = V_n(1, a/(2a−b))``.
Every identity in the paper is therefore a statement about the 1878 Lucas sequences
with ``P = 1``; ``Ψ(−1, −3, n) = V_n(1, −1) = L_n`` and ``Ψ(−2, −5, n) = V_n(1, −2) = 2^n + (−1)^n``.

Periodicity classification (derived here; only the period-20 case is in the paper)
-----------------------------------------------------------------------------------
Put ``b = −2·cos(2θ)`` and ``a = 1``.  The closed form gives::

    Ψ(1, b, n) = 2·cos(nθ)           (n even),
    Ψ(1, b, n) = cos(nθ) / cos(θ)    (n odd),

so ``Ψ(1, b, ·)`` is periodic iff ``θ = 2π·k/m`` (reduced), with period ``m`` for even ``m``
and ``2m`` for odd ``m`` (the parity alternation between the two branches doubles odd
orders).  This reproduces the paper's six rings — ``b = 1, 0, −1, √2, φ−1, √3`` with
``θ = 60°, 45°, 30°, 67.5°, 54°, 75°`` and periods ``6, 8, 12, 16, 20, 24`` — and predicts the
three further golden rings ``b = φ`` (θ = 72°, period 10), ``b = 1 − φ`` (36°, 10) and
``b = −φ`` (18°, 20).  ``|b| > 2`` — e.g. the Mersenne case ``b = 4`` — is the unbounded
hyperbolic continuation ``2·cosh``.

Consequence for the "period-20 golden nodes": ``2^{p−1} mod 20 ∈ {4, 16}`` for every odd
prime ``p``, hence ``Ψ(1, φ−1, 2^{p−1}) = −φ`` for *all* ``p ≥ 5``.  The golden ring is a
coordinate system for exponents, not a primality discriminator.

Primality (Theorem 26) and its true identity
--------------------------------------------
For prime ``p ≥ 5`` and ``n = 2^{p−1}``: ``2^p − 1`` is prime iff ``(2n − 1) | Ψ(1, 4, n)``.
Since ``Ψ(1, 4, 2^k)`` is the Lucas–Lehmer term ``s_{k−1}`` (``14, 194, 37634, …``),
this *is* the Lucas–Lehmer test, and :func:`theorem26_is_prime` must never be used as a
machine-learning feature.
"""
from __future__ import annotations

import cmath
import math
from fractions import Fraction
from typing import Any, Iterable

Number = Any  # int | Fraction | float | complex | sympy.Expr | QuadInt


# --------------------------------------------------------------------------- quadratic rings
_RINGS: dict[str, tuple[int, int, str, float]] = {
    # name: (c0, c1, symbol, float value of the generator ω) with ω² = c0 + c1·ω
    "phi": (1, 1, "φ", (1.0 + math.sqrt(5.0)) / 2.0),
    "sqrt2": (2, 0, "√2", math.sqrt(2.0)),
    "sqrt3": (3, 0, "√3", math.sqrt(3.0)),
    "sqrt5": (5, 0, "√5", math.sqrt(5.0)),
}


class QuadInt:
    """Exact element ``u + v·ω`` of a quadratic ring, ``ω² = c0 + c1·ω``.

    Rings: ``"phi"`` (``ω = φ``, ``φ² = φ + 1``), ``"sqrt2"``, ``"sqrt3"``, ``"sqrt5"``.
    Coefficients may be ``int`` or ``Fraction``.  Mixed arithmetic with plain integers
    and fractions is supported so that :func:`psi` can run unchanged over these rings.
    """

    __slots__ = ("u", "v", "ring")

    def __init__(self, u: int | Fraction = 0, v: int | Fraction = 0, ring: str = "phi") -> None:
        if ring not in _RINGS:
            raise ValueError(f"unknown ring {ring!r}; choose from {sorted(_RINGS)}")
        self.u, self.v, self.ring = u, v, ring

    # -- coercion -----------------------------------------------------------------
    def _coerce(self, other: Any) -> "QuadInt":
        if isinstance(other, QuadInt):
            if other.ring != self.ring:
                raise TypeError(f"cannot mix rings {self.ring!r} and {other.ring!r}")
            return other
        if isinstance(other, (int, Fraction)):
            return QuadInt(other, 0, self.ring)
        return NotImplemented  # type: ignore[return-value]

    # -- arithmetic ---------------------------------------------------------------
    def __add__(self, other: Any) -> "QuadInt":
        o = self._coerce(other)
        if o is NotImplemented:
            return o
        return QuadInt(self.u + o.u, self.v + o.v, self.ring)

    __radd__ = __add__

    def __neg__(self) -> "QuadInt":
        return QuadInt(-self.u, -self.v, self.ring)

    def __sub__(self, other: Any) -> "QuadInt":
        o = self._coerce(other)
        if o is NotImplemented:
            return o
        return QuadInt(self.u - o.u, self.v - o.v, self.ring)

    def __rsub__(self, other: Any) -> "QuadInt":
        o = self._coerce(other)
        if o is NotImplemented:
            return o
        return QuadInt(o.u - self.u, o.v - self.v, self.ring)

    def __mul__(self, other: Any) -> "QuadInt":
        o = self._coerce(other)
        if o is NotImplemented:
            return o
        c0, c1, _, _ = _RINGS[self.ring]
        vv = self.v * o.v
        return QuadInt(self.u * o.u + c0 * vv, self.u * o.v + self.v * o.u + c1 * vv, self.ring)

    __rmul__ = __mul__

    def __pow__(self, n: int) -> "QuadInt":
        if n < 0:
            raise ValueError("negative powers are not supported")
        result = QuadInt(1, 0, self.ring)
        base = self
        while n:
            if n & 1:
                result = result * base
            base = base * base
            n >>= 1
        return result

    # -- comparison / hashing -----------------------------------------------------
    def __eq__(self, other: Any) -> bool:
        o = self._coerce(other)
        if o is NotImplemented:
            return False
        return self.u == o.u and self.v == o.v

    def __hash__(self) -> int:
        return hash((self.u, self.v, self.ring))

    # -- conversions --------------------------------------------------------------
    def __float__(self) -> float:
        return float(self.u) + float(self.v) * _RINGS[self.ring][3]

    def conjugate(self) -> "QuadInt":
        """Galois conjugate: ``√d ↦ −√d``; ``φ ↦ 1 − φ``."""
        _, c1, _, _ = _RINGS[self.ring]
        if c1 == 0:
            return QuadInt(self.u, -self.v, self.ring)
        return QuadInt(self.u + c1 * self.v, -self.v, self.ring)

    def norm(self) -> int | Fraction:
        prod = self * self.conjugate()
        assert prod.v == 0
        return prod.u

    def to_sympy(self) -> Any:
        import sympy

        c0, _, _, _ = _RINGS[self.ring]
        omega = sympy.GoldenRatio if self.ring == "phi" else sympy.sqrt(c0)
        return sympy.Rational(self.u) + sympy.Rational(self.v) * omega

    def __repr__(self) -> str:
        sym = _RINGS[self.ring][2]
        if self.v == 0:
            return f"{self.u}"
        if self.u == 0:
            return f"{self.v}{sym}" if self.v not in (1, -1) else ("" if self.v == 1 else "-") + sym
        sign = "+" if self.v > 0 else "-"
        mag = abs(self.v)
        return f"{self.u}{sign}{'' if mag == 1 else mag}{sym}"


PHI_EXACT = QuadInt(0, 1, "phi")
SQRT2_EXACT = QuadInt(0, 1, "sqrt2")
SQRT3_EXACT = QuadInt(0, 1, "sqrt3")


# --------------------------------------------------------------------------- the Ψ-sequence
def delta(n: int) -> int:
    """``δ(n) = n mod 2``."""
    return n & 1


def psi(a: Number, b: Number, n: int) -> Number:
    """``Ψ(a, b, n)`` by the recurrence of Definition 4.1 (``O(n)`` ring operations).

    Works for any ``a, b`` supporting ``+``, ``−``, ``*`` with each other and with small
    integers: ``int``, ``Fraction``, ``float``, ``sympy`` expressions, :class:`QuadInt`.
    Negative indices use the paper's convention ``Ψ(a, b, −l) := Ψ(a, b, l)``.
    """
    if n < 0:
        n = -n
    if n == 0:
        return 2
    if n == 1:
        return 1
    t = 2 * a - b
    prev, cur = 2, 1
    for k in range(1, n):
        step = t * cur if (k & 1) else cur
        prev, cur = cur, step - a * prev
    return cur


def psi_explicit(a: Number, b: Number, n: int) -> Number:
    """``Ψ(a, b, n)`` by the explicit sum of Theorem 9 (exact via ``Fraction``).

    Returns an ``int`` when ``a, b`` are integers.
    """
    if n < 0:
        n = -n
    if n == 0:
        return 2
    t = 2 * a - b
    total: Number = 0
    for i in range(n // 2 + 1):
        coeff = Fraction(n, n - i) * math.comb(n - i, i)
        total = total + coeff * (-a) ** i * t ** (n // 2 - i)
    if isinstance(total, Fraction) and total.denominator == 1:
        return int(total)
    return total


def psi_closed_form(a: float, b: float, n: int) -> float | complex:
    """``Ψ(a, b, n)`` by equation 36 in floating point (complex square roots allowed).

    Requires ``b ≠ 2a``.  The result is real for real inputs; a real ``float`` is
    returned when the imaginary part is numerically zero.
    """
    if b == 2 * a:
        raise ValueError("closed form needs b != 2a (degenerate root)")
    s = (b + 2 * a) / (b - 2 * a)
    r = cmath.sqrt(s)
    value = ((2 * a - b) ** (n // 2) / 2 ** n) * ((1 + r) ** n + (1 - r) ** n)
    if abs(value.imag) <= 1e-9 * max(1.0, abs(value.real)):
        return value.real
    return value


def rotation_angle_rad(b: float) -> float:
    """``θ`` with ``b = −2·cos(2θ)``, for ``|b| ≤ 2`` (``a = 1``)."""
    if abs(b) > 2:
        raise ValueError("rotation angle is only defined for |b| <= 2 (elliptic case)")
    return 0.5 * math.acos(-b / 2.0)


def psi_trig(b: float, n: int) -> float:
    """``Ψ(1, b, n)`` from the rotation form ``2·cos(nθ)`` / ``cos(nθ)/cos θ`` (``|b| < 2``)."""
    theta = rotation_angle_rad(b)
    if n % 2 == 0:
        return 2.0 * math.cos(n * theta)
    return math.cos(n * theta) / math.cos(theta)


# --------------------------------------------------------------------------- Lucas sequences
def lucas_v(P: Number, Q: Number, n: int) -> Number:
    """Lucas V-sequence ``V_0 = 2, V_1 = P, V_{n+1} = P·V_n − Q·V_{n−1}``."""
    if n == 0:
        return 2
    prev, cur = 2, P
    for _ in range(n - 1):
        prev, cur = cur, P * cur - Q * prev
    return cur


def lucas_u(P: Number, Q: Number, n: int) -> Number:
    """Lucas U-sequence ``U_0 = 0, U_1 = 1, U_{n+1} = P·U_n − Q·U_{n−1}``."""
    if n == 0:
        return 0
    prev, cur = 0, 1
    for _ in range(n - 1):
        prev, cur = cur, P * cur - Q * prev
    return cur


def psi_via_lucas_v(a: Number, b: Number, n: int) -> Number:
    """``Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b))`` — the normalisation identity."""
    if n < 0:
        n = -n
    t = 2 * a - b
    if t == 0:
        raise ValueError("normalisation identity needs 2a != b")
    Q = Fraction(a, t) if isinstance(a, int) and isinstance(t, int) else a / t
    value = t ** (n // 2) * lucas_v(1, Q, n)
    if isinstance(value, Fraction) and value.denominator == 1:
        return int(value)
    return value


def lehmer_companion_bar(R: Number, Q: Number, n: int) -> Number:
    """D. H. Lehmer's companion sequence ``V̄_n(√R, Q)`` (1930), exactly.

    With ``α + β = √R`` and ``αβ = Q``: ``V_n = α^n + β^n`` and ``V̄_n = V_n`` for even ``n``,
    ``V_n/√R`` for odd ``n``.  Computed in ``Z[√R]`` as pairs ``x + y√R``.
    **Ψ(a, b, n) = V̄_n(√(2a − b), a)** — see :func:`psi_via_lehmer`.
    """
    if n < 0:
        n = -n
    prev = (2, 0)          # V_0 = 2
    cur = (0, 1)           # V_1 = √R
    if n == 0:
        return 2
    for _ in range(n - 1):
        x, y = cur
        sqrtR_cur = (R * y, x)                       # √R · (x + y√R) = R·y + x·√R
        prev, cur = cur, (sqrtR_cur[0] - Q * prev[0], sqrtR_cur[1] - Q * prev[1])
    x, y = cur
    return x if n % 2 == 0 else y


def lehmer_bar(R: Number, Q: Number, n: int) -> Number:
    """Lehmer numbers ``Ū_n(√R, Q)``: ``U_n = (α^n − β^n)/(α − β)``, ``Ū_n = U_n`` (n odd),
    ``U_n/√R`` (n even).  Computed in ``Z[√R]``."""
    if n == 0:
        return 0
    prev = (0, 0)
    cur = (1, 0)           # U_1 = 1
    for _ in range(n - 1):
        x, y = cur
        sqrtR_cur = (R * y, x)
        prev, cur = cur, (sqrtR_cur[0] - Q * prev[0], sqrtR_cur[1] - Q * prev[1])
    x, y = cur
    return x if n % 2 == 1 else y


def psi_via_lehmer(a: Number, b: Number, n: int) -> Number:
    """``Ψ(a, b, n) = V̄_n(√(2a − b), a)``: Ibrahim's Ψ-sequence is Lehmer's companion sequence."""
    return lehmer_companion_bar(2 * a - b, a, n)


def lucas(n: int) -> int:
    """Lucas number ``L_n`` (``2, 1, 3, 4, 7, …``)."""
    a, b = 2, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fibonacci(n: int) -> int:
    """Fibonacci number ``F_n`` (``0, 1, 1, 2, 3, …``)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fibonacci_mod(n: int, m: int) -> int:
    """``F_n mod m`` by iterative fast doubling (``O(log n)``, no recursion)."""
    if m == 1:
        return 0
    f, g = 0, 1                      # (F_k, F_{k+1}) for the prefix of bits processed so far
    for bit in bin(n)[2:]:
        c = (f * ((2 * g - f) % m)) % m          # F_{2k}
        d = (f * f + g * g) % m                  # F_{2k+1}
        f, g = (d, (c + d) % m) if bit == "1" else (c, d)
    return f % m


def lucas_number_mod(n: int, m: int) -> int:
    """``L_n mod m`` via ``L_n = 2F_{n+1} − F_n``."""
    return (2 * fibonacci_mod(n + 1, m) - fibonacci_mod(n, m)) % m


# --------------------------------------------------------------------------- fast modular Ψ
def psi_double(a: Number, b: Number, psi_n: Number, n: int) -> Number:
    """``Ψ(a, b, 2n)`` from ``Ψ(a, b, n)``: ``(2a − b)^{δ(n)}·Ψ(n)² − 2·a^n``
    (from ``V_{2n} = V_n² − 2Q^n``)."""
    return (2 * a - b) ** delta(n) * psi_n * psi_n - 2 * a ** n


def _mat_mul_mod(x: tuple[int, int, int, int], y: tuple[int, int, int, int], m: int) -> tuple[int, int, int, int]:
    return (
        (x[0] * y[0] + x[1] * y[2]) % m,
        (x[0] * y[1] + x[1] * y[3]) % m,
        (x[2] * y[0] + x[3] * y[2]) % m,
        (x[2] * y[1] + x[3] * y[3]) % m,
    )


def psi_mod(a: int, b: int, n: int, m: int) -> int:
    """``Ψ(a, b, n) mod m`` in ``O(log n)`` multiplications via the two-step matrix.

    From an even index ``k``: ``Ψ(k+1) = Ψ(k) − a·Ψ(k−1)`` and
    ``Ψ(k+2) = (2a − b)·Ψ(k+1) − a·Ψ(k)``, so ``(Ψ(k+2), Ψ(k+1)) = M·(Ψ(k), Ψ(k−1))`` with
    ``M = [[a − b, −a(2a − b)], [1, −a]]``.  Starting from ``(Ψ(2), Ψ(1)) = (−b, 1)``.
    """
    if n < 0:
        n = -n
    if m == 1:
        return 0
    if n == 0:
        return 2 % m
    if n == 1:
        return 1 % m
    t = (2 * a - b) % m
    M = ((a - b) % m, (-a * t) % m, 1 % m, (-a) % m)
    j = (n - 2) // 2 if n % 2 == 0 else (n - 1) // 2
    R = (1 % m, 0, 0, 1 % m)
    while j:
        if j & 1:
            R = _mat_mul_mod(R, M, m)
        M = _mat_mul_mod(M, M, m)
        j >>= 1
    x2, x1 = (-b) % m, 1 % m
    top = (R[0] * x2 + R[1] * x1) % m
    bottom = (R[2] * x2 + R[3] * x1) % m
    return top if n % 2 == 0 else bottom


def psi_pow2_mod(a: int, b: int, k: int, m: int) -> int:
    """``Ψ(a, b, 2^k) mod m`` by repeated doubling.  For ``(a, b) = (1, 4)`` the loop is
    ``x ↦ x² − 2`` from ``x = −4``, i.e. the Lucas–Lehmer iteration up to sign."""
    if k == 0:
        return 1 % m
    x = (-b) % m            # Ψ(2)
    apow = (a * a) % m      # a^{2^1}
    for _ in range(1, k):
        x = (x * x - 2 * apow) % m
        apow = (apow * apow) % m
    return x


def psi_fast(a: int, b: int, n: int):
    """Exact ``Ψ(a, b, n)`` in ``O(log n)`` big-integer multiplications (gmpy2 when available).

    Uses the two-step matrix of :func:`psi_mod` without a modulus:
    ``(Ψ(k+2), Ψ(k+1)) = M · (Ψ(k), Ψ(k−1))`` for even ``k`` with
    ``M = [[a − b, −a(2a − b)], [1, −a]]``, started from ``(Ψ(2), Ψ(1)) = (−b, 1)``.
    """
    try:
        from gmpy2 import mpz
    except ImportError:  # pragma: no cover
        mpz = int  # type: ignore[assignment]
    if n < 0:
        n = -n
    if n == 0:
        return 2
    if n == 1:
        return 1
    t = 2 * a - b
    m00, m01, m10, m11 = mpz(a - b), mpz(-a * t), mpz(1), mpz(-a)
    r00, r01, r10, r11 = mpz(1), mpz(0), mpz(0), mpz(1)
    j = (n - 2) // 2 if n % 2 == 0 else (n - 1) // 2
    while j:
        if j & 1:
            r00, r01, r10, r11 = r00 * m00 + r01 * m10, r00 * m01 + r01 * m11, r10 * m00 + r11 * m10, r10 * m01 + r11 * m11
        m00, m01, m10, m11 = m00 * m00 + m01 * m10, m00 * m01 + m01 * m11, m10 * m00 + m11 * m10, m10 * m01 + m11 * m11
        j >>= 1
    x2, x1 = mpz(-b), mpz(1)
    top, bottom = r00 * x2 + r01 * x1, r10 * x2 + r11 * x1
    return int(top if n % 2 == 0 else bottom)


# --------------------------------------------------------------------------- periodic rings
def _ring_table(a: Number, b: Number, period: int) -> tuple[Number, ...]:
    vals = []
    for n in range(period):
        v = psi(a, b, n)
        if isinstance(a, QuadInt) and isinstance(v, int):   # Ψ(0) = 2, Ψ(1) = 1 come back as ints
            v = QuadInt(v, 0, a.ring)
        vals.append(v)
    return tuple(vals)


#: Exact tables ``Ψ(1, b, n)`` for ``n = 0 … period−1`` (ints or :class:`QuadInt`).
PERIODIC_TABLES: dict[int, tuple[Number, ...]] = {
    6: _ring_table(1, 1, 6),
    8: _ring_table(1, 0, 8),
    12: _ring_table(1, -1, 12),
    16: _ring_table(QuadInt(1, 0, "sqrt2"), SQRT2_EXACT, 16),
    20: _ring_table(QuadInt(1, 0, "phi"), PHI_EXACT - 1, 20),
    24: _ring_table(QuadInt(1, 0, "sqrt3"), SQRT3_EXACT, 24),
}

#: The four golden rings: name -> (b exact, rotation angle in degrees, period, table).
GOLDEN_TABLES: dict[str, tuple[QuadInt, float, int, tuple[QuadInt, ...]]] = {
    "phi": (PHI_EXACT, 72.0, 10, _ring_table(QuadInt(1, 0, "phi"), PHI_EXACT, 10)),
    "1-phi": (1 - PHI_EXACT, 36.0, 10, _ring_table(QuadInt(1, 0, "phi"), 1 - PHI_EXACT, 10)),
    "-phi": (-PHI_EXACT, 18.0, 20, _ring_table(QuadInt(1, 0, "phi"), -PHI_EXACT, 20)),
    "phi-1": (PHI_EXACT - 1, 54.0, 20, _ring_table(QuadInt(1, 0, "phi"), PHI_EXACT - 1, 20)),
}

EIGHT_LEVELS: tuple[int, ...] = tuple(int(x) for x in PERIODIC_TABLES[8])  # (2, 1, 0, -1, -2, -1, 0, 1)


def psi_periodic_exact(period: int, n: int) -> Number:
    """Exact ``Ψ(1, b_period, n)`` from the stored table."""
    table = PERIODIC_TABLES[period]
    return table[n % period]


def psi_periodic(period: int, n: int) -> float:
    """``Ψ(1, b_period, n)`` as a float."""
    return float(psi_periodic_exact(period, n))


def eight_level(n: int) -> int:
    """``Ψ(1, 0, n) ∈ {2, 1, 0, −1, −2}``: the Eight Levels, indexed by ``n mod 8``."""
    return EIGHT_LEVELS[n % 8]


def golden_level_exact(n: int) -> QuadInt:
    """``Ψ(1, φ − 1, n)`` exactly in ``Z[φ]`` (period 20)."""
    return PERIODIC_TABLES[20][n % 20]


def golden_level(n: int) -> float:
    """``Ψ(1, φ − 1, n)`` as a float."""
    return float(golden_level_exact(n))


def golden_ring_level(name: str, n: int) -> float:
    """Float value on one of the four golden rings (``"phi"``, ``"1-phi"``, ``"-phi"``, ``"phi-1"``)."""
    _, _, period, table = GOLDEN_TABLES[name]
    return float(table[n % period])


# --------------------------------------------------------------------------- theorems 26/27/30
def theorem26_is_prime(p: int) -> bool:
    """Theorem 26: ``2^p − 1`` prime iff ``(2n − 1) | Ψ(1, 4, n)`` with ``n = 2^{p−1}``.

    This is the Lucas–Lehmer test: ``Ψ(1, 4, 2^k) = s_{k−1}``.  Provided for
    verification only — never as a feature.
    """
    if p < 3:
        raise ValueError("Theorem 26 is stated for primes p >= 5; p = 3 also works")
    M = (1 << p) - 1
    return psi_pow2_mod(1, 4, p - 1, M) == 0


def theorem27_residue(p: int, mu: int) -> int:
    """Signed residue of ``Ψ(1, 4, n·μ) mod (2n − 1)``, ``n = 2^{p−1}``.

    Theorem 27: when ``2^p − 1`` is prime the pattern is ``+2, 0, −2, 0`` for
    ``μ ≡ 0, 1, 2, 3 (mod 4)``.
    """
    M = (1 << p) - 1
    r = psi_mod(1, 4, (1 << (p - 1)) * mu, M)
    return r - M if r > M // 2 else r


def theorem30_neighbour_divides(p: int) -> bool:
    """Theorem 30: if ``(2n − 1) | Ψ(1, 4, n ± 1)`` then ``2^p − 1`` is composite."""
    M = (1 << p) - 1
    n = 1 << (p - 1)
    return psi_mod(1, 4, n - 1, M) == 0 or psi_mod(1, 4, n + 1, M) == 0


def minimal_period(seq: Iterable[Number], max_period: int | None = None) -> int | None:
    """Smallest ``P`` with ``seq[n + P] == seq[n]`` for all available ``n``, or ``None``."""
    s = list(seq)
    limit = max_period or len(s) // 2
    for P in range(1, limit + 1):
        if all(s[i] == s[i + P] for i in range(len(s) - P)):
            return P
    return None
