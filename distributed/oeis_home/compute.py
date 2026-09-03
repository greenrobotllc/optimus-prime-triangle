"""Verdicts and the worker loop.

Order of decision for a candidate ``(variant, n)`` with ``N = |Psi|``:

1. ``N == 1`` → ``unit``.  ``N < 2^64`` → ``prime`` / ``composite`` with ``method "small"``
   (deterministic Miller–Rabin over the first 13 prime bases, exact below 3.3·10^24).
2. structured trial division → ``composite``, ``method "factor"``, ``factor q``.
3. Fermat test to the per-worker base → ``composite``, ``method "fermat"`` (``res64`` kept).
4. BPSW (``gmpy2.is_prime``) plus strong-probable-prime tests to bases 2, 3 and the worker base →
   ``prp`` (``method "bpsw"``, ``sprp`` bases, ``res64``) or ``composite``.
``prime`` for ``N ≥ 2^64`` needs a certificate (optional tier, maintainer only).
"""
from __future__ import annotations

import hashlib
import os
import platform
import time
from pathlib import Path

try:
    import gmpy2
    from gmpy2 import mpz, powmod
    HAVE_GMPY2 = True
except ImportError:  # pragma: no cover
    HAVE_GMPY2 = False
    mpz = int  # type: ignore[assignment,misc]

    def powmod(a, e, m):  # type: ignore[no-redef]
        return pow(a, e, m)

from . import __version__
from .canon import canon
from .families import Family, abs_value
from .sieve import structured_trial_division
from .units import candidates, parse_unit_id, worker_base

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
TWO64 = 1 << 64
SOURCE_FILES = ("families.py", "units.py", "sieve.py", "compute.py")


def small_prime_decision(N: int) -> str:
    """Deterministic primality for ``N < 3.3·10^24`` (13 Miller–Rabin bases)."""
    N = int(N)
    if N < 2:
        return "composite"
    for q in _MR_BASES:
        if N % q == 0:
            return "prime" if N == q else "composite"
    d, s = N - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, N)
        if x in (1, N - 1):
            continue
        for _ in range(s - 1):
            x = x * x % N
            if x == N - 1:
                break
        else:
            return "composite"
    return "prime"


def _res64(r) -> str:
    return format(int(r) & (TWO64 - 1), "016x")


def _is_strong_prp(N, base: int) -> bool:
    if HAVE_GMPY2:
        return bool(gmpy2.is_strong_prp(N, base))
    N = int(N)
    d, s = N - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    x = pow(base, d, N)
    if x in (1, N - 1):
        return True
    for _ in range(s - 1):
        x = x * x % N
        if x == N - 1:
            return True
    return False


def verdict(fam: Family, variant: str, n: int, base: int) -> dict:
    """One verdict record; a pure function of ``(variant, n, base)``."""
    N = abs_value(variant, n)
    digits = len(str(N))
    rec = {"n": n, "variant": variant, "digits": digits}
    if N == 1:
        rec.update(v="unit", method="small")
        return rec
    if N < TWO64:
        rec.update(v=small_prime_decision(int(N)), method="small")
        return rec
    q = structured_trial_division(N, n, fam.sieve_kmax)
    if q is not None:
        rec.update(v="composite", method="factor", factor=str(q))
        return rec
    r = powmod(mpz(base), N - 1, N)
    res64 = _res64(r)
    if r != 1:
        rec.update(v="composite", method="fermat", res64=res64)
        return rec
    bpsw = bool(gmpy2.is_prime(N, fam.mr_rounds)) if HAVE_GMPY2 else small_prime_decision(int(N)) == "prime"
    bases = [*fam.sprp_bases, base]
    if bpsw and all(_is_strong_prp(N, b) for b in bases):
        rec.update(v="prp", method="bpsw", res64=res64, sprp=bases)
    else:
        rec.update(v="composite", method="bpsw", res64=res64)
    return rec


def worker_sha256() -> str:
    """SHA-256 over the concatenated canonical source of the worker modules, in a fixed order."""
    here = Path(__file__).resolve().parent
    blob = b"".join((here / f).read_bytes().replace(b"\r\n", b"\n") for f in SOURCE_FILES)
    return hashlib.sha256(blob).hexdigest()


def software_info() -> dict:
    info = {"name": "oeis_home", "version": __version__, "worker_sha256": worker_sha256(), "python": platform.python_version()}
    if HAVE_GMPY2:
        info["gmpy2"] = gmpy2.version()
        info["gmp"] = gmpy2.mp_version().replace("GMP ", "")
    else:
        info["gmpy2"] = "none"
        info["gmp"] = "none"
    return info


def summarize(verdicts: list[dict]) -> dict:
    out = {"prime": 0, "prp": 0, "composite": 0, "unit": 0, "digits_hi": 0}
    for r in verdicts:
        out[r["v"]] += 1
        out["digits_hi"] = max(out["digits_hi"], r["digits"])
    return out


def run_unit(fam: Family, uid: str, fp: str, login: str, progress=print, partial_path: Path | None = None,
             checkpoint_s: float = 60.0) -> dict:
    """Compute the full (unsigned) result payload for ``uid``; resumable through ``partial_path``."""
    lo, hi = parse_unit_id(uid, fam.bands)
    cands = candidates(fam, uid)
    base = worker_base(fp, uid)
    done: list[dict] = []
    if partial_path and Path(partial_path).exists():
        import json  # noqa: PLC0415

        saved = json.loads(Path(partial_path).read_text())
        if saved.get("unit_id") == uid and saved.get("base") == base and saved.get("worker") == fp:
            done = saved["verdicts"]
    t0 = time.perf_counter()
    last = t0
    for i, (n, v) in enumerate(cands):
        if i < len(done):
            continue
        rec = verdict(fam, v, n, base)
        done.append(rec)
        if progress:
            progress(f"{uid} {i + 1}/{len(cands)} n={n} {v}: {rec['v']} ({rec['method']}, {rec['digits']} digits)")
        if partial_path and time.perf_counter() - last > checkpoint_s:
            _write_partial(Path(partial_path), uid, base, fp, done)
            last = time.perf_counter()
    payload = {
        "schema": "oeis-home/v1/result", "family": fam.id, "family_hash": fam.hash,
        "unit_id": uid, "n_lo": lo, "n_hi": hi, "login": login, "worker": fp,
        "software": software_info(), "base": base, "verdicts": done, "summary": summarize(done),
        "wall_ms": int((time.perf_counter() - t0) * 1000), "nonce": os.urandom(32).hex(),
    }
    canon(payload)  # profile check
    if partial_path and Path(partial_path).exists():
        Path(partial_path).unlink()
    return payload


def _write_partial(path: Path, uid: str, base: int, fp: str, verdicts: list[dict]) -> None:
    import json  # noqa: PLC0415

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"unit_id": uid, "base": base, "worker": fp, "verdicts": verdicts}))
    os.replace(tmp, path)
