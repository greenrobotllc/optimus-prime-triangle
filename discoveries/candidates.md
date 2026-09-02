# Discoveries ledger

Working label: **Triboletti–Fable**.  A label here is a working name.  Mathematical names
stick only through publication and citation; novelty is *not* asserted by this repository —
each entry's `novelty` field must be checked by a human against OEIS and the literature.

Status ladder: `numeric-verified → sympy-proved / proved (elementary) → novelty: unchecked | classical | checked`.

## Periodicity classification of the Ψ rings

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (closed form; rotation form sympy-checked for n ≤ 8) · novelty: **unchecked**

> Ψ(1, −2cos 2θ, n) is periodic in n iff θ/2π = k/m is rational; the minimal period is m for even m and 2m for odd m.  Golden rings: b=φ (72°, 10), b=1−φ (36°, 10), b=−φ (18°, 20), b=φ−1 (54°, 20).

Evidence: exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30

Notes: Ingredients are classical (Chebyshev / Lucas-sequence normalisation); the unified statement and the three unlisted golden rings are what is recorded.

## Three golden rings not listed in the source paper

**Triboletti–Fable candidate** · kind: ring · numeric-verified: True · proof: proved (corollary of the classification) · novelty: **unchecked**

> Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.

Evidence: exact sequences in Z[φ] over three periods

## Ψ is a rescaled Lucas V-sequence

**Triboletti–Fable candidate** · kind: identity · numeric-verified: True · proof: sympy-proved (n ≤ 12); general proof via Binet · novelty: **classical**

> Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b)).

Evidence: exact rational-function identity for each n ≤ 12; integer check for |a| ≤ 4, |b| ≤ 6, n < 14

Notes: Classical in substance (Lucas 1878); recorded because it makes every identity in the source papers mechanically provable. Not a novelty claim.

## Ring coordinates of the Lucas–Lehmer index are constant

**Triboletti–Fable candidate** · kind: proposition · numeric-verified: True · proof: proved (elementary: 2^{p−1} is constant modulo each period for p ≥ 5) · novelty: **unchecked**

> For every ring period k ∈ {6, 8, 10, 12, 16, 20, 24} and every odd prime p ≥ 5, Ψ(1, b_k, 2^{p−1}) takes the same value; on the golden ring it is −φ.

Evidence: all odd primes p ≤ 2000

Notes: This is why the period-20 golden map cannot discriminate Mersenne primes.

## Ψ is Lehmer's companion sequence

**Triboletti–Fable candidate** · kind: identity · numeric-verified: True · proof: proved (elementary: both sides satisfy the same recurrence with the same initial values) · novelty: **unchecked**

> Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences.

Evidence: exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16

Notes: Sharper than the normalisation identity: it names the classical object exactly.

## Ibrahim's primality theorems are the Lucas–Lehmer test

**Triboletti–Fable candidate** · kind: source_correction · numeric-verified: True · proof: proved (closed form: Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n) · novelty: **unchecked**

> Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; hence Theorem 26 of arXiv:2404.05772 and Theorem 9 of arXiv:2502.06796 (whose B-ratio equals Ψ(1, 4, 2^{p−1})) are the Lucas–Lehmer test restated.

Evidence: p ≤ 61 (Theorem 26 vs LL), p = 5, 7, 11 (Theorem 9 vs LL)

## Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (via Lucas's golden-seed test and F_{2n} = F_n L_n, gcd(F_n, L_n) | 2) · novelty: **unchecked**

> If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}). For p ≡ 1 (mod 4) the rank is M_p − 1 for p = 5, 13, 17 but (M_p − 1)/9 for p = 61 and (M_p − 1)/3 for p = 89.

Evidence: every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 2203; cofactors for p ≡ 1 (mod 4), p ≤ 89

## The golden Lucas–Lehmer seed and its exact domain

**Triboletti–Fable candidate** · kind: proposition · numeric-verified: True · proof: proved (classical; (5 | M_p) = +1 iff p ≡ 1 mod 4) · novelty: **classical**

> Seed s₀ = 3 = L₂ gives s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}, and the test is valid iff p ≡ 3 (mod 4); no seed built in Q(√5) can be universal.

Evidence: all primes p ≤ 500; p = 5 is the smallest failure

```json
[
  {
    "slug": "periodicity-classification",
    "title": "Periodicity classification of the Ψ rings",
    "statement": "Ψ(1, −2cos 2θ, n) is periodic in n iff θ/2π = k/m is rational; the minimal period is m for even m and 2m for odd m.  Golden rings: b=φ (72°, 10), b=1−φ (36°, 10), b=−φ (18°, 20), b=φ−1 (54°, 20).",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (closed form; rotation form sympy-checked for n ≤ 8)",
    "novelty": "unchecked",
    "evidence": "exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30",
    "label": "Triboletti–Fable",
    "notes": "Ingredients are classical (Chebyshev / Lucas-sequence normalisation); the unified statement and the three unlisted golden rings are what is recorded.",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "golden-rings",
    "title": "Three golden rings not listed in the source paper",
    "statement": "Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.",
    "kind": "ring",
    "numeric_verified": true,
    "proof_status": "proved (corollary of the classification)",
    "novelty": "unchecked",
    "evidence": "exact sequences in Z[φ] over three periods",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "normalisation-identity",
    "title": "Ψ is a rescaled Lucas V-sequence",
    "statement": "Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b)).",
    "kind": "identity",
    "numeric_verified": true,
    "proof_status": "sympy-proved (n ≤ 12); general proof via Binet",
    "novelty": "classical",
    "evidence": "exact rational-function identity for each n ≤ 12; integer check for |a| ≤ 4, |b| ≤ 6, n < 14",
    "label": "Triboletti–Fable",
    "notes": "Classical in substance (Lucas 1878); recorded because it makes every identity in the source papers mechanically provable. Not a novelty claim.",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "ll-index-constancy",
    "title": "Ring coordinates of the Lucas–Lehmer index are constant",
    "statement": "For every ring period k ∈ {6, 8, 10, 12, 16, 20, 24} and every odd prime p ≥ 5, Ψ(1, b_k, 2^{p−1}) takes the same value; on the golden ring it is −φ.",
    "kind": "proposition",
    "numeric_verified": true,
    "proof_status": "proved (elementary: 2^{p−1} is constant modulo each period for p ≥ 5)",
    "novelty": "unchecked",
    "evidence": "all odd primes p ≤ 2000",
    "label": "Triboletti–Fable",
    "notes": "This is why the period-20 golden map cannot discriminate Mersenne primes.",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "lehmer-identification",
    "title": "Ψ is Lehmer's companion sequence",
    "statement": "Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences.",
    "kind": "identity",
    "numeric_verified": true,
    "proof_status": "proved (elementary: both sides satisfy the same recurrence with the same initial values)",
    "novelty": "unchecked",
    "evidence": "exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16",
    "label": "Triboletti–Fable",
    "notes": "Sharper than the normalisation identity: it names the classical object exactly.",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "qps-is-lucas-lehmer",
    "title": "Ibrahim's primality theorems are the Lucas–Lehmer test",
    "statement": "Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; hence Theorem 26 of arXiv:2404.05772 and Theorem 9 of arXiv:2502.06796 (whose B-ratio equals Ψ(1, 4, 2^{p−1})) are the Lucas–Lehmer test restated.",
    "kind": "source_correction",
    "numeric_verified": true,
    "proof_status": "proved (closed form: Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n)",
    "novelty": "unchecked",
    "evidence": "p ≤ 61 (Theorem 26 vs LL), p = 5, 7, 11 (Theorem 9 vs LL)",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "mersenne-fibonacci-rank",
    "title": "Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)",
    "statement": "If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}). For p ≡ 1 (mod 4) the rank is M_p − 1 for p = 5, 13, 17 but (M_p − 1)/9 for p = 61 and (M_p − 1)/3 for p = 89.",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (via Lucas's golden-seed test and F_{2n} = F_n L_n, gcd(F_n, L_n) | 2)",
    "novelty": "unchecked",
    "evidence": "every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 2203; cofactors for p ≡ 1 (mod 4), p ≤ 89",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [],
    "novelty_note": ""
  },
  {
    "slug": "golden-seed",
    "title": "The golden Lucas–Lehmer seed and its exact domain",
    "statement": "Seed s₀ = 3 = L₂ gives s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}, and the test is valid iff p ≡ 3 (mod 4); no seed built in Q(√5) can be universal.",
    "kind": "proposition",
    "numeric_verified": true,
    "proof_status": "proved (classical; (5 | M_p) = +1 iff p ≡ 1 mod 4)",
    "novelty": "classical",
    "evidence": "all primes p ≤ 500; p = 5 is the smallest failure",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [],
    "novelty_note": ""
  }
]
```
