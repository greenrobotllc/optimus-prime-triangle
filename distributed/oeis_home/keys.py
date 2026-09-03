"""Ed25519 identities and signed envelopes (``cryptography`` library)."""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canon import CanonError, KINDS, signing_message

DEFAULT_KEY_PATH = Path.home() / ".oeis-home" / "key.ed25519"
ROTATION_PREFIX = b"oeis-home/v1/rotation\n"


class SignatureError(ValueError):
    """The envelope's signature, key or structure is not acceptable."""


def generate(path: Path = DEFAULT_KEY_PATH) -> Ed25519PrivateKey:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists; refusing to overwrite a key")
    sk = Ed25519PrivateKey.generate()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(sk.private_bytes_raw())
    return sk


def load(path: Path = DEFAULT_KEY_PATH) -> Ed25519PrivateKey:
    raw = Path(path).read_bytes()
    if len(raw) != 32:
        raise SignatureError("private key file must hold exactly 32 raw bytes")
    return Ed25519PrivateKey.from_private_bytes(raw)


def public_raw(sk: Ed25519PrivateKey) -> bytes:
    return sk.public_key().public_bytes_raw()


def fingerprint(pub_raw: bytes) -> str:
    return "k1:" + hashlib.sha256(pub_raw).hexdigest()


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


_B64U_RE = __import__("re").compile(r"^[A-Za-z0-9_-]+$")


def _unb64u(text: str) -> bytes:
    """Strict base64url: alphabet-checked and round-trip canonical (rejects trailing-bit variants)."""
    if not isinstance(text, str) or not _B64U_RE.match(text):
        raise SignatureError("signature is not base64url")
    pad = "=" * (-len(text) % 4)
    raw = base64.urlsafe_b64decode(text + pad)
    if _b64u(raw) != text:
        raise SignatureError("signature encoding is not canonical")
    return raw


def sign_envelope(kind: str, payload: dict, sk: Ed25519PrivateKey) -> dict:
    pub = public_raw(sk)
    sig = sk.sign(signing_message(kind, payload))
    return {"kind": kind, "payload": payload,
            "signature": {"alg": "ed25519", "key": fingerprint(pub), "pubkey": pub.hex(), "sig": _b64u(sig)}}


def verify_envelope(env: dict, expected_kind: str | None = None) -> str:
    """Verify structure, key binding and signature; return the signer's fingerprint."""
    if not isinstance(env, dict) or set(env) != {"kind", "payload", "signature"}:
        raise SignatureError("envelope must have exactly kind, payload, signature")
    kind, payload, sig = env["kind"], env["payload"], env["signature"]
    if kind not in KINDS or (expected_kind and kind != expected_kind):
        raise SignatureError(f"unexpected kind {kind!r}")
    if not isinstance(payload, dict) or not isinstance(sig, dict) or set(sig) != {"alg", "key", "pubkey", "sig"}:
        raise SignatureError("malformed payload or signature block")
    if sig["alg"] != "ed25519":
        raise SignatureError("unsupported algorithm")
    try:
        pub_raw = bytes.fromhex(sig["pubkey"])
    except ValueError as exc:
        raise SignatureError("pubkey is not hex") from exc
    if len(pub_raw) != 32 or fingerprint(pub_raw) != sig["key"]:
        raise SignatureError("pubkey does not match the fingerprint")
    if not isinstance(sig["sig"], str) or len(sig["sig"]) != 86:
        raise SignatureError("signature must be 86 base64url characters")
    try:
        Ed25519PublicKey.from_public_bytes(pub_raw).verify(_unb64u(sig["sig"]), signing_message(kind, payload))
    except (InvalidSignature, ValueError, CanonError, SignatureError) as exc:
        raise SignatureError(f"signature does not verify: {exc}") from exc
    return sig["key"]


def rotation_signature(old_sk: Ed25519PrivateKey, new_pub_raw: bytes) -> str:
    return _b64u(old_sk.sign(ROTATION_PREFIX + new_pub_raw))


def verify_rotation(old_pub_raw: bytes, new_pub_raw: bytes, rotation_sig: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(old_pub_raw).verify(_unb64u(rotation_sig), ROTATION_PREFIX + new_pub_raw)
        return True
    except (InvalidSignature, ValueError, SignatureError):
        return False
