"""The family ``lehmer-q2``: exact values, the provable algebraic filter, and the family hash.

Mathematics (all verified in the test-suite against ``core_math.psi_sequence.psi``):

* With ``(U_m, V_m)`` the Lucas pair ``P = 1, Q = 4``::

      Psi(2,-1,2m) = V_m            Psi(2,1,2m) = (-1)^m V_m          (variant "even", N = |V_m|)
      Psi(2,-1,2m+1) = (V_m - 3U_m)/2                                  (variant "m1")
      Psi(2,1,2m+1)  = (-1)^m (V_m + 5U_m)/2                           (variant "p1")

* Lehmer (1930): ``Psi(d) | Psi(n)`` whenever ``d | n`` and ``n/d`` is odd.  Bilu–Hanrot–Voutier
  (2001): for ``n ≥ 16`` the companion term has a primitive prime divisor, so the quotient is
  non-trivial.  Hence for ``n ≥ 16`` a term can only be prime when ``n`` is prime, twice a prime,
  a power of two, or one of the listed extra survivors (indices whose only odd-quotient divisors
  are *unit* indices, where ``|Psi(d)| = 1``).  Below 16 everything is tested directly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

try:
    from gmpy2 import is_prime as _is_prime
    from gmpy2 import mpz
except ImportError:  # pragma: no cover - pure-Python fallback (≈ 20× slower)
    mpz = int  # type: ignore[assignment,misc]

    def _is_prime(n, reps=25):  # type: ignore[no-redef]
        from .compute import small_prime_decision  # noqa: PLC0415

        return small_prime_decision(int(n)) == "prime"

from .canon import canon, sha256_hex

VARIANTS = ("even", "m1", "p1")
HASH_KEYS = ("family", "version", "variants", "filter", "sieve", "prp")
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "families" / "lehmer-q2.json"


@dataclass(frozen=True)
class Family:
    id: str
    version: int
    hash: str
    units: dict[str, frozenset[int]]
    extra_survivors: dict[str, frozenset[int]]
    exhaustive_below: int
    sieve_kmax: int
    sprp_bases: tuple[int, ...]
    mr_rounds: int
    bands: tuple[tuple[int, int, int], ...]
    n_max_open: int
    test_vectors: dict
    raw: dict


def family_hash(payload: dict) -> str:
    core = {k: payload[k] for k in HASH_KEYS}
    return "sha256:" + sha256_hex(canon(core))


def load(path: Path | None = None) -> Family:
    import os  # noqa: PLC0415

    raw = json.loads(Path(path or os.environ.get("OEIS_HOME_FAMILY") or DEFAULT_PATH).read_text(encoding="utf-8"))
    flt = raw["filter"]
    return Family(
        id=raw["family"], version=int(raw["version"]), hash=family_hash(raw),
        units={v: frozenset(flt["units"][v]) for v in VARIANTS},
        extra_survivors={v: frozenset(flt["extra_survivors"][v]) for v in VARIANTS},
        exhaustive_below=int(flt["exhaustive_below"]),
        sieve_kmax=int(raw["sieve"]["kmax"]),
        sprp_bases=tuple(raw["prp"]["sprp_bases"]), mr_rounds=int(raw["prp"]["mr_rounds"]),
        bands=tuple(tuple(b) for b in raw["bands"]), n_max_open=int(raw["n_max_open"]),
        test_vectors=raw["test_vectors"], raw=raw,
    )


# --------------------------------------------------------------------------- exact values
def lucas_uv_14(m: int) -> tuple:
    """``(U_m, V_m)`` for the Lucas pair ``P = 1, Q = 4`` by fast doubling (exact halvings)."""
    U, V, k = mpz(0), mpz(2), 0
    for bit in bin(m)[2:]:
        U, V = U * V, V * V - (mpz(1) << (2 * k + 1))     # U_{2k} = U_k V_k ; V_{2k} = V_k² − 2·4^k
        k *= 2
        if bit == "1":
            U, V = (U + V) >> 1, (V - 15 * U) >> 1         # (U_{k+1}, V_{k+1}) from (U_k, V_k), P=1, Q=4
            k += 1
    return U, V


def value(variant: str, n: int):
    """Signed ``Psi`` value of the variant at ``n`` (``even`` requires even ``n``)."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}")
    if n < 0:
        raise ValueError("n must be non-negative")
    m, r = divmod(n, 2)
    U, V = lucas_uv_14(m)
    if variant == "even":
        if r:
            raise ValueError("variant 'even' needs an even index")
        return V
    if variant == "m1":
        return V if r == 0 else (V - 3 * U) // 2
    sign = -1 if m % 2 else 1
    return sign * V if r == 0 else sign * ((V + 5 * U) // 2)


def abs_value(variant: str, n: int):
    return abs(value(variant, n))


def variants_for(n: int) -> tuple[str, ...]:
    return ("even",) if n % 2 == 0 else ("m1", "p1")


def reference_value(variant: str, n: int) -> int:
    """Independent O(n) evaluator via the repository's ``core_math`` (tests / CI cross-check only)."""
    from core_math.psi_sequence import psi  # noqa: PLC0415 - optional dependency on the parent repo

    b = {"even": -1, "m1": -1, "p1": 1}[variant]
    return int(psi(2, b, n))


# --------------------------------------------------------------------------- the algebraic filter
def _is_power_of_two(n: int) -> bool:
    return n > 0 and n & (n - 1) == 0


def is_candidate(fam: Family, variant: str, n: int) -> bool:
    """Closed form of "no proper divisor ``d`` with ``n/d`` odd and ``d`` not a unit index"."""
    if variant == "even" and n % 2:
        return False
    if n < fam.exhaustive_below:
        return True
    if _is_prime(n):
        return True
    if n % 2 == 0 and _is_prime(n // 2):
        return True
    if _is_power_of_two(n):
        return True
    return n in fam.extra_survivors[variant]


def filter_witness(fam: Family, variant: str, n: int) -> int | None:
    """Smallest proper divisor ``d`` of ``n`` with ``n/d`` odd and ``d`` not a unit index (``None`` if candidate)."""
    if n < fam.exhaustive_below or is_candidate(fam, variant, n):
        return None
    units = fam.units[variant]
    for d in range(1, n):
        if n % d == 0 and (n // d) % 2 == 1 and d not in units:
            return d
    return None


def check_filter_witness(variant: str, n: int, d: int) -> bool:
    """Exact check: ``1 < |Psi(d)| < |Psi(n)|`` and ``Psi(d) | Psi(n)``."""
    if not (0 < d < n and n % d == 0 and (n // d) % 2 == 1):
        return False
    vd, vn = value(variant, d) if variant != "even" or d % 2 == 0 else value("m1", d), value(variant, n)
    return 1 < abs(vd) < abs(vn) and vn % vd == 0
