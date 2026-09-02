"""A small offline library of classical integer sequences for the discovery screen.

No network access: OEIS is not consulted.  A match here means "this is a well-known
sequence"; a non-match means only "not in this small library" and never "new".
"""
from __future__ import annotations

from core_math.mersenne import mersenne_number, wagstaff_number
from core_math.psi_sequence import fibonacci, lucas

N_TERMS = 30


def _linear(P: int, Q: int, x0: int, x1: int, n: int) -> list[int]:
    out = [x0, x1]
    while len(out) < n:
        out.append(P * out[-1] - Q * out[-2])
    return out[:n]


def library(n_terms: int = N_TERMS) -> dict[str, list[int]]:
    lib: dict[str, list[int]] = {
        "fibonacci": [fibonacci(n) for n in range(n_terms)],
        "lucas": [lucas(n) for n in range(n_terms)],
        "pell": _linear(2, -1, 0, 1, n_terms),
        "pell_lucas": _linear(2, -1, 2, 2, n_terms),
        "jacobsthal": _linear(1, -2, 0, 1, n_terms),
        "jacobsthal_lucas": _linear(1, -2, 2, 1, n_terms),
        "mersenne_numbers": [mersenne_number(n) if n >= 1 else 0 for n in range(n_terms)],
        "2^n+1": [2**n + 1 for n in range(n_terms)],
        "2^n+(-1)^n": [2**n + (-1) ** n for n in range(n_terms)],
        "powers_of_2": [2**n for n in range(n_terms)],
        "powers_of_3": [3**n for n in range(n_terms)],
        "wagstaff_odd_index": [wagstaff_number(n) if n % 2 and n >= 3 else (2**n + 1) // 3 if n % 2 else 0 for n in range(n_terms)],
        "chebyshev_T_at_2 (2·T_n(2))": _linear(4, 1, 2, 4, n_terms),
        "chebyshev_T_at_3 (2·T_n(3))": _linear(6, 1, 2, 6, n_terms),
        "lucas_lehmer_psi(1,4)": None,  # filled below
    }
    from core_math.psi_sequence import psi

    lib["lucas_lehmer_psi(1,4)"] = [psi(1, 4, n) for n in range(n_terms)]
    return lib


_LIB = library()


def match(seq: list[int], min_len: int = 8) -> list[str]:
    """Names of library sequences equal to ``seq`` on its first terms (also up to sign)."""
    if len(seq) < min_len:
        return []
    hits = []
    for name, ref in _LIB.items():
        k = min(len(seq), len(ref))
        if list(seq[:k]) == ref[:k]:
            hits.append(name)
        elif [-v for v in seq[:k]] == ref[:k]:
            hits.append(f"-({name})")
        elif [abs(v) for v in seq[:k]] == [abs(v) for v in ref[:k]] and any(v < 0 for v in seq[:k]):
            hits.append(f"±({name})")
    return hits
