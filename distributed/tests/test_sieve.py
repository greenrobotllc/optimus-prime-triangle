from oeis_home.families import abs_value
from oeis_home.sieve import structured_trial_division


def test_structured_sieve_finds_2017_for_m1_1009():
    N = abs_value("m1", 1009)
    assert structured_trial_division(N, 1009) == 2017 and N % 2017 == 0


def test_sieve_never_returns_the_number_itself_or_a_non_divisor():
    for v in ("m1", "p1"):
        for n in range(2, 48):
            N = abs_value(v, n)
            q = structured_trial_division(N, n, kmax=200)
            assert q is None or (1 < q < N and N % q == 0), (v, n, q)
