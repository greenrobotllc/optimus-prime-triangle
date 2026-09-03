# OEIS@home pilot

A verification-first volunteer-computing pilot whose first work-unit family is the prime hunt in the
Lehmer companion sequences with Q = 2: |Ψ(2, −1, n)| = |V̄_n(√5, 2)| and |Ψ(2, 1, n)| = |V̄_n(√3, 2)|.
These sequences and their prime-index sets are not in OEIS; every verified term is a new one, credited
to the volunteer who found it and to the one who double-checked it.

How trust works: results are Ed25519-signed canonical JSON files contributed by pull request; CI runs
the *base* branch's code and recomputes every line with the volunteer's own test base; a rebuild job
on `main` re-verifies, writes `verified/`, `ledger/`, `exports/` and the results page, and opens a
discovery issue for each confirmed probable prime. Volunteer quorum (two accounts) is required for a
probable prime to enter the OEIS-ready export; the maintainer's `gp` check turns "prp" into "prime".

Everything OEIS-facing stays manual and human: `exports/lehmer-q2/oeis_draft.txt` is regenerated from
the ledger, and a named person submits it.

See CONTRIBUTING.md for the volunteer steps; `oeis-home --help` for the commands.
