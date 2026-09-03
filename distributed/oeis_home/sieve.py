"""Structured trial division: every prime factor of a candidate term is ``≡ ±1 (mod 2n)``."""
from __future__ import annotations

try:
    from gmpy2 import is_prime as _is_prime
except ImportError:  # pragma: no cover
    def _is_prime(n, reps=25):  # type: ignore[no-redef]
        from .compute import small_prime_decision  # noqa: PLC0415

        return small_prime_decision(int(n)) == "prime"


def structured_trial_division(N, n: int, kmax: int = 20000) -> int | None:
    """Smallest prime ``q = 2kn ± 1`` with ``k ≤ kmax`` and ``1 < q < N`` dividing ``N``, else ``None``."""
    step = 2 * n
    q_minus, q_plus = step - 1, step + 1
    for _ in range(kmax):
        for q in (q_minus, q_plus):
            if 1 < q < N and N % q == 0 and _is_prime(q):
                return int(q)
        q_minus += step
        q_plus += step
    return None
