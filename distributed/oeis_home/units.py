"""Work units: the band grid, unit ids, candidate lists, and the per-worker Fermat base."""
from __future__ import annotations

import hashlib

try:
    from gmpy2 import next_prime as _next_prime
except ImportError:  # pragma: no cover
    def _next_prime(x):  # type: ignore[no-redef]
        from .compute import small_prime_decision  # noqa: PLC0415

        x = int(x) + 1
        while small_prime_decision(x) != "prime":
            x += 1
        return x

from .families import Family, is_candidate, variants_for

BANDS: tuple[tuple[int, int, int], ...] = ((0, 20000, 5000), (20000, 60000, 1000), (60000, 120000, 400), (120000, 200000, 200))
FAMILY_ID = "lehmer-q2"


def unit_bounds(n_lo: int, bands=BANDS) -> tuple[int, int]:
    for lo, hi, width in bands:
        if lo <= n_lo < hi:
            if (n_lo - lo) % width:
                raise ValueError(f"n_lo={n_lo} is not on the band grid (width {width} from {lo})")
            return n_lo, min(n_lo + width, hi)
    raise ValueError(f"n_lo={n_lo} is outside every band")


def unit_id(n_lo: int, bands=BANDS) -> str:
    lo, hi = unit_bounds(n_lo, bands)
    return f"{FAMILY_ID}-{lo:08d}-{hi:08d}"


def parse_unit_id(uid: str, bands=BANDS) -> tuple[int, int]:
    parts = uid.rsplit("-", 2)
    if len(parts) != 3 or parts[0] != FAMILY_ID:
        raise ValueError(f"malformed unit id {uid!r}")
    lo, hi = int(parts[1]), int(parts[2])
    if unit_bounds(lo, bands) != (lo, hi) or f"{lo:08d}" != parts[1] or f"{hi:08d}" != parts[2]:
        raise ValueError(f"unit id {uid!r} is not on the band grid")
    return lo, hi


def all_units(n_max_open: int, bands=BANDS) -> list[str]:
    out = []
    for lo, hi, width in bands:
        n = lo
        while n < min(hi, n_max_open):
            out.append(unit_id(n, bands))
            n += width
    return out


def candidates(fam: Family, uid: str) -> list[tuple[int, str]]:
    """Sorted ``(n, variant)`` pairs a result must contain, in this exact order."""
    lo, hi = parse_unit_id(uid, fam.bands)
    out = []
    for n in range(lo, hi):
        for v in variants_for(n):
            if is_candidate(fam, v, n):
                out.append((n, v))
    return out


def worker_base(fp: str, uid: str) -> int:
    """Per-worker Fermat base: a prime in ``[7, 100003]`` derived from the key fingerprint and unit id."""
    h = hashlib.sha256(f"oeis-home-base/v1|{fp}|{uid}".encode("utf-8")).digest()
    return int(_next_prime(5 + int.from_bytes(h[:4], "big") % 100000))
