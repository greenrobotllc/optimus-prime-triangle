import pytest

from oeis_home import canon


def test_profile_rejections():
    for bad in ({"a": 1.5}, {"a": 2**53}, {"é": 1}, {"a": "e\u0301"}):
        with pytest.raises(canon.CanonError):
            canon.canon(bad)
    with pytest.raises(canon.CanonError):
        canon.loads_strict(b'{"a":1,"a":2}')
    with pytest.raises(canon.CanonError):
        canon.signing_message("bogus", {})


def test_canonical_bytes_vectors():
    vectors = [
        ({"b": 1, "a": "x"}, b'{"a":"x","b":1}'),
        ({"s": "\u001f\u007f\u2028"}, '{"s":"\\u001f\u007f\u2028"}'.encode("utf-8")),
        ({"n": [1, {"z": None, "y": True}]}, b'{"n":[1,{"y":true,"z":null}]}'),
        ({"big": str(2**80)}, b'{"big":"1208925819614629174706176"}'),
        ({"q": 'a"b\\c/d'}, b'{"q":"a\\"b\\\\c/d"}'),
    ]
    for obj, expected in vectors:
        assert canon.canon(obj) == expected


def test_file_bytes_round_trip_and_strictness():
    env = {"kind": "claim", "payload": {"x": 1}, "signature": {"alg": "ed25519", "key": "k", "pubkey": "p", "sig": "s"}}
    data = canon.file_bytes(env)
    assert canon.check_file_bytes(data) == env
    with pytest.raises(canon.CanonError):
        canon.check_file_bytes(data.replace(b"\n", b"\r\n"))
    with pytest.raises(canon.CanonError):
        canon.check_file_bytes(b'{"kind": "claim", "payload": {"x": 1}, "signature": {}}\n')   # pretty-printed
