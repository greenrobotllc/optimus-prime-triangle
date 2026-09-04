import copy
import os
import stat

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from oeis_home import keys


def test_keygen_and_load(tmp_path):
    path = tmp_path / "k"
    sk = keys.generate(path)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600 and len(path.read_bytes()) == 32
    assert keys.public_raw(keys.load(path)) == keys.public_raw(sk)
    with pytest.raises(FileExistsError):
        keys.generate(path)


def test_sign_verify_and_rejections():
    sk = Ed25519PrivateKey.generate()
    env = keys.sign_envelope("result", {"a": 1, "b": "x"}, sk)
    assert keys.verify_envelope(env, "result") == keys.fingerprint(keys.public_raw(sk))
    tampered = copy.deepcopy(env)
    tampered["payload"]["a"] = 2
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(tampered)
    wrong_kind = copy.deepcopy(env)
    wrong_kind["kind"] = "claim"
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(wrong_kind)
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(env, "claim")
    other = Ed25519PrivateKey.generate()
    swapped = copy.deepcopy(env)
    swapped["signature"]["pubkey"] = keys.public_raw(other).hex()
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(swapped)
    swapped["signature"]["key"] = keys.fingerprint(keys.public_raw(other))
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(swapped)
    extra = copy.deepcopy(env)
    extra["extra"] = 1
    with pytest.raises(keys.SignatureError):
        keys.verify_envelope(extra)


def test_rotation_signature_only_from_old_key():
    old, new, imp = (Ed25519PrivateKey.generate() for _ in range(3))
    sig = keys.rotation_signature(old, keys.public_raw(new))
    assert keys.verify_rotation(keys.public_raw(old), keys.public_raw(new), sig)
    assert not keys.verify_rotation(keys.public_raw(imp), keys.public_raw(new), sig)
    assert not keys.verify_rotation(keys.public_raw(old), keys.public_raw(imp), sig)
