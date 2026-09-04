"""Canonical JSON (an RFC 8785 profile) and the signing message.

Profile: no floats; integers with |x| ≤ 2^53 − 1 (larger integers travel as decimal strings);
object keys ASCII; every string NFC-normalised.  Under these rules Python's ``json.dumps`` with
``sort_keys=True`` and compact separators is byte-identical to JCS.  Files on disk must equal
``canon(envelope) + b"\\n"`` exactly.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata

MAX_INT = 2**53 - 1
PREFIX = b"oeis-home/v1/"
KINDS = ("contributor", "claim", "result", "verified", "note")
MAX_FILE_BYTES = 8 * 1024 * 1024


class CanonError(ValueError):
    """The object violates the canonical profile or the bytes are not canonical."""


def check_profile(obj, path: str = "$") -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, float):
        raise CanonError(f"{path}: floats are not allowed")
    if isinstance(obj, int):
        if abs(obj) > MAX_INT:
            raise CanonError(f"{path}: integer exceeds 2^53-1; use a decimal string")
        return
    if isinstance(obj, str):
        if unicodedata.normalize("NFC", obj) != obj:
            raise CanonError(f"{path}: string is not NFC")
        if any("\ud800" <= ch <= "\udfff" for ch in obj):
            raise CanonError(f"{path}: lone surrogate in string")
        return
    if isinstance(obj, list):
        for i, v in enumerate(obj):
            check_profile(v, f"{path}[{i}]")
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str) or not k.isascii():
                raise CanonError(f"{path}: object keys must be ASCII strings")
            check_profile(v, f"{path}.{k}")
        return
    raise CanonError(f"{path}: unsupported type {type(obj).__name__}")


def canon(obj) -> bytes:
    check_profile(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def _no_duplicates(pairs):
    seen = set()
    out = {}
    for k, v in pairs:
        if k in seen:
            raise CanonError(f"duplicate key {k!r}")
        seen.add(k)
        out[k] = v
    return out


def loads_strict(data: bytes):
    if len(data) > MAX_FILE_BYTES:
        raise CanonError(f"file larger than {MAX_FILE_BYTES} bytes")
    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=_no_duplicates)
        check_profile(obj)
        return obj
    except RecursionError as exc:
        raise CanonError("nesting too deep") from exc
    except UnicodeDecodeError as exc:
        raise CanonError(f"not UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CanonError(f"invalid JSON: {exc}") from exc


def signing_message(kind: str, payload: dict) -> bytes:
    if kind not in KINDS:
        raise CanonError(f"unknown kind {kind!r}")
    return PREFIX + kind.encode("ascii") + b"\n" + canon(payload)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_bytes(envelope: dict) -> bytes:
    """The only accepted on-disk form of a signed file."""
    return canon(envelope) + b"\n"


def check_file_bytes(data: bytes) -> dict:
    """Parse strictly and require byte-canonical form; return the envelope."""
    env = loads_strict(data)
    if not isinstance(env, dict):
        raise CanonError("top level must be an object")
    if data != file_bytes(env):
        raise CanonError("file bytes are not canonical (pretty-printing, CRLF or key order)")
    return env
