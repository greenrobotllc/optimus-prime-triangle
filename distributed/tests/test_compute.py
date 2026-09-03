from oeis_home import compute as C
from oeis_home.families import variants_for
from oeis_home.units import worker_base


def test_prime_index_lists_reproduced(fam):
    base = worker_base("k1:" + "0" * 64, "lehmer-q2-00000000-00005000")
    for v in ("m1", "p1"):
        got = [n for n in range(0, 121) for vv in variants_for(n) if (vv == v or vv == "even")
               and C.verdict(fam, vv, n, base)["v"] in ("prime", "prp")]
        assert got == fam.test_vectors["prime_indices_le_120"][v]


def test_units_and_small_and_prp(fam):
    for n in (1, 2, 3, 7):
        assert C.verdict(fam, "m1", n, 7)["v"] == "unit"
    for n in (1, 2, 5):
        assert C.verdict(fam, "p1", n, 7)["v"] == "unit"
    assert C.verdict(fam, "even", 0, 7) == {"n": 0, "variant": "even", "digits": 1, "v": "prime", "method": "small"}
    r = C.verdict(fam, "m1", 1019, 8419)
    assert r["v"] == "prp" and r["method"] == "bpsw" and r["sprp"] == [2, 3, 8419] and r["res64"] == "0000000000000001"
    r = C.verdict(fam, "m1", 20000, 3)
    assert r["v"] == "composite" and r["method"] == "fermat" and r["res64"] == "e45cdea32da2b4f7"


def test_small_prime_decision_matches_sympy():
    import random
    import sympy

    rng = random.Random(4)
    for _ in range(300):
        N = rng.randrange(2, 2**64)
        assert C.small_prime_decision(N) == ("prime" if sympy.isprime(N) else "composite")
    assert C.small_prime_decision(318665857834031151167461) == "composite"


def test_worker_sha256_is_stable_and_declared():
    import json
    from pathlib import Path

    sha = C.worker_sha256()
    rel = json.loads((Path(C.__file__).resolve().parents[1] / "RELEASES.json").read_text())
    assert sha == rel["accepted"][0]["worker_sha256"] and sha == C.worker_sha256()
