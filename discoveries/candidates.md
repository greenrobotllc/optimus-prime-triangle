# Discoveries ledger

Working label: **Triboletti–Fable**.  A label here is a working name.  Mathematical names
stick only through publication and citation; novelty is *not* asserted by this repository —
each entry's `novelty` field must be checked by a human against OEIS and the literature.

Status ladder: `numeric-verified → sympy-proved / proved (elementary) → novelty: unchecked | classical | corollary_of_known | checked`.

## Periodicity classification of the Ψ rings

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (closed form; rotation form sympy-checked for n ≤ 8) · novelty: **classical**

> Ψ(1, −2cos 2θ, n) is periodic in n iff θ/2π = k/m is rational; the minimal period is m for even m and 2m for odd m.  Golden rings: b=φ (72°, 10), b=1−φ (36°, 10), b=−φ (18°, 20), b=φ−1 (54°, 20).

Evidence: exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30

Notes: Ibrahim's own Chebyshev identity at x = cos θ plus the folklore criterion 'a linear recurrence is periodic iff its roots are roots of unity'. Lewin (1991) states the period formula for V_n(2cos θ, 1) explicitly; OEIS A087204 is the period-6 ring.

Novelty check: Checked 2026-09-02 against Lucas 1878, Lewin 1991, Somer 1980, MacHenry–Wong 2007, Wikipedia (Lehmer sequence, Chebyshev polynomials) and OEIS: the statement is classical; only its application to Ibrahim's six examples is new bookkeeping.

References:
- M. Lewin, Periodic Fibonacci and Lucas sequences, Fibonacci Quart. 29.4 (1991) 310–315, Thms 1–2 — https://www.fq.math.ca/Scanned/29-4/lewin.pdf
- E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308
- L. Somer, Fibonacci Quart. 18.4 (1980), Thm 4 — https://www.fq.math.ca/Scanned/18-4/somer.pdf
- T. MacHenry, K. Wong, arXiv:0712.2403, Thm 2.1 — https://arxiv.org/abs/0712.2403
- OEIS A087204 — https://oeis.org/A087204

## Three golden rings not listed in the source paper

**Triboletti–Fable candidate** · kind: ring · numeric-verified: True · proof: proved (corollary of the classification) · novelty: **corollary_of_known**

> Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.

Evidence: exact sequences in Z[φ] over three periods

Novelty check: 2cos(π/5) = φ and 2cos(2π/5) = φ − 1 are classical (Euclid XIII.10, OEIS A001622); the three rings are one line from the classification. Not in Ibrahim's papers, but not a result either.

References:
- Wikipedia, Golden ratio — pentagon and pentagram — https://en.wikipedia.org/wiki/Golden_ratio
- OEIS A001622 — https://oeis.org/A001622
- M. Lewin, Periodic Fibonacci and Lucas sequences, Fibonacci Quart. 29.4 (1991) 310–315, Thms 1–2 — https://www.fq.math.ca/Scanned/29-4/lewin.pdf
- M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 §16.1.6

## Ψ is Lehmer's companion sequence

**Triboletti–Fable candidate** · kind: identity · numeric-verified: True · proof: proved (both sides satisfy the same recurrence with the same initial values; sympy for n ≤ 12) · novelty: **corollary_of_known**

> Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences; equivalently Ψ(a, b, n) = (2a − b)^{⌊n/2⌋}·V_n(1, a/(2a − b)).

Evidence: exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16

Notes: This is the sharpest classical identification and it settles the novelty of every Ψ-ring statement. Ibrahim's eq. (36) prints the Binet form; no source states the Lehmer identification, which is a one-line substitution R = 2a − b, Q = a.

Novelty check: Checked 2026-09-02: Lehmer 1930, MathWorld 'Lehmer Number', Wikipedia 'Lehmer sequence', Roettger–Williams 2025 §2 give the definition; the identification with Ψ is not published but is immediate. Worth a remark, not a theorem.

References:
- D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235
- MathWorld, Lehmer Number — https://mathworld.wolfram.com/LehmerNumber.html
- Wikipedia, Lehmer sequence — https://en.wikipedia.org/wiki/Lehmer_sequence
- E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf
- M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 eq. (36)

## Ψ is a rescaled Lucas V-sequence

**Triboletti–Fable candidate** · kind: identity · numeric-verified: True · proof: sympy-proved (n ≤ 12); general proof via Binet · novelty: **classical**

> Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b)).

Evidence: exact rational-function identity for each n ≤ 12; integer check for |a| ≤ 4, |b| ≤ 6, n < 14

Notes: Superseded by the Lehmer identification.

Novelty check: Checked 2026-09-02: Lucas 1878 / Lehmer 1930; Wikipedia 'Lucas sequence' (relations between sequences with different parameters).

References:
- E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308
- D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235
- Wikipedia, Lucas sequence — https://en.wikipedia.org/wiki/Lucas_sequence

## Ring coordinates of the Lucas–Lehmer index are constant

**Triboletti–Fable candidate** · kind: proposition · numeric-verified: True · proof: proved (elementary) · novelty: **classical**

> For every odd prime p ≥ 5, 2^{p−1} ≡ 4 (mod 6), 0 (mod 8), 4 (mod 12), 0 (mod 16), 4 or 16 (mod 20), 16 (mod 24); hence Ψ(1,1,2^{p−1}) = −1, Ψ(1,0,·) = 2, Ψ(1,−1,·) = −1, Ψ(1,√2,·) = 2, Ψ(1,φ−1,·) = −φ, Ψ(1,√3,·) = −1 independently of p. All periodic neighbours of the Mersenne Star carry no information about p, so the Star paper's proposal to use the periodic strips to accelerate Mersenne testing cannot work as stated.

Evidence: all primes 5 ≤ p < 400 and all 52 known Mersenne exponents

Novelty check: Checked 2026-09-02: Ibrahim's own Theorem 7 (arXiv:2404.05772, eqs. 20, 24, 26, 31) states Ψ(1,φ−1,2^l) = −φ for even l ≥ 4 and the analogues for the other rings; the consequence for the Star paper's proposals is not drawn there.

References:
- M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 Theorem 7
- M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 §§1.4, 1.5, 12.1

## The golden Lucas–Lehmer seed and its exact domain

**Triboletti–Fable candidate** · kind: proposition · numeric-verified: True · proof: proved (classical; (5 | M_p) = +1 iff p ≡ 1 mod 4) · novelty: **classical**

> Seed s₀ = 3 = L₂ gives s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}, and the test is valid iff p ≡ 3 (mod 4); no seed built in Q(√5) can be universal.

Evidence: all primes p ≤ 500; p = 5 is the smallest failure

Novelty check: Checked 2026-09-02: Lucas 1876/1878 (M_127), Robinson 1954, Jansen 2012, Roettger–Williams 2025, OEIS A001566, Wikipedia (alternative starting values).

References:
- E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf
- R. M. Robinson, Mersenne and Fermat numbers, Proc. AMS 5 (1954) 842–846
- OEIS A001566 — https://oeis.org/A001566
- Wikipedia, Lucas–Lehmer primality test — https://en.wikipedia.org/wiki/Lucas%E2%80%93Lehmer_primality_test

## Ibrahim's primality theorems and all 32 Mersenne Star conditions are the Lucas–Lehmer test

**Triboletti–Fable candidate** · kind: source_correction · numeric-verified: True · proof: proved (closed form Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n; anchor ratios computed exactly) · novelty: **corollary_of_known**

> Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; Theorem 26 of arXiv:2404.05772, Theorem 9 of arXiv:2502.06796 (B-ratio = Ψ(1, 4, 2^{p−1})) and all 32 conditions of Theorem 7.6 of the Mersenne Star paper reduce literally to 2^p − 1 | Ψ(1, 4, 2^{p−1}); they add no primality information beyond Lucas–Lehmer.

Evidence: p ≤ 61 (Theorem 26 vs LL); p = 5, 7, 11, 13 for Theorem 9 and for all 32 Star conditions

Novelty check: Checked 2026-09-02: Theorem 26 is itself titled 'a new version for Lucas–Lehmer' and proved via LL in the source; the QPS paper proves Theorem 9 from that theorem; a 2024 mersenneforum thread already notes the equivalence. That the Star's 32 conditions carry nothing new is not stated in the Star paper.

References:
- M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 Theorem 26
- M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1 Theorems 9, 47, 51
- M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 Theorem 7.6
- mersenneforum thread 'Eight levels theorem' (2024) — http://web.archive.org/web/20250116091733/https://www.mersenneforum.org/node/22736
- OEIS A003010 — https://oeis.org/A003010

## Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (Lucas's law of apparition + Lehmer's half-index criterion) · novelty: **corollary_of_known**

> If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}); verified for every such known Mersenne prime up to p = 4423 and for p = 86243. For p ≡ 1 (mod 4) the rank divides M_p − 1 with odd cofactor 1, 1, 1, 9, 3, 1, 1, 1, 3 for p = 5, 13, 17, 61, 89, 521, 2281, 3217, 4253 (a power of 3 each time; consistent with chance).

Evidence: every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 4423 (plus 86243); cofactors from factordb factorizations of 2^{p−1} − 1

Novelty check: Checked 2026-09-02: not found verbatim in OEIS (A001602, A000057, A001177), Wikipedia, MathWorld or the Prime Pages, but one step from Lucas 1878 and equivalent statements appear in Roettger–Williams 2025, Jaroma 2004, Guo–Koch 2009 (Thm 3.4) and Baker arXiv:2608.05319 (Prop. 1); OEIS A000057 (primes with entry point p+1) already lists 7, 127, 524287.

References:
- E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308 pp. 289–305
- E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf
- J. H. Jaroma, Note on the Lucas–Lehmer test, Irish Math. Soc. Bull. 54 (2004) — https://www.maths.tcd.ie/pub/ims/bull54/M5402.pdf
- C. Guo, A. Koch, Bounds for Fibonacci period growth, Involve 2 (2009) — https://msp.org/involve/2009/2-2/involve-v2-n2-p04-p.pdf
- OEIS A000057 — https://oeis.org/A000057

## Closed form for the whole Quanta Prime Sequence table

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (induction on k: the recurrence step is a symbolic identity in N, u, k, j; exact check for n ≤ 30, all r ≤ ⌊n/2⌋+3, all k ≤ ⌊n/2⌋) · novelty: **unchecked**

> For all n ≥ 1, r, k ≥ 0, with N = n − r and u = n − 2r − δ(n−1): Ω_r(k | ζ, ξ | n) = Σ_{j=0}^{k} C(k, j) (2ζ − ξ)^{k−j} (−2ζ)^j · (N−j−1)^{(k−j)↓} · u(u−2)⋯(u−2j+2). In particular Ω depends on (n, r) only through (N, u). The three explicit formulas of the source (points (0,−1), (1,2), (1,−2), Theorems 42, 41, 19) are the special cases.

Evidence: 0 mismatches in 21 000 entries (workflow) and 8 000 entries (independent re-check), random (ζ, ξ) ∈ [−9, 9]²

Notes: Standard technique (binomial sum solving a two-term recurrence); the value is that the QPS paper (2025) has no general formula.

Novelty check: Not in arXiv:2502.06796 (read in full); the arXiv API lists no follow-up papers. No wider literature search was possible for this 2025 object; as far as we know new, but routine.

References:
- M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1 Definition 6.1, Theorems 19, 41, 42

## Hypergeometric form and exponential generating function of the QPS table

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (rewrite of the closed form with Pochhammer symbols; exact check n ≤ 18, EGF coefficients n ≤ 14) · novelty: **unchecked**

> With N = n − r, u = n − 2r − δ(n−1), 2ζ ≠ ξ and k ≤ N − 1: Ω_r(k) = (2ζ − ξ)^k (N−1)^{k↓} · ₂F₁(−k, −u/2; 1 − N; 4ζ/(2ζ − ξ)) (terminating series), and Σ_k Ω_r(k) x^k/(k! (N−1)^{k↓}) = e^{(2ζ−ξ)x} · ₁F₁(−u/2; 1 − N; −4ζx). Note 1 − 4ζ/(2ζ−ξ) = −(2ζ+ξ)/(2ζ−ξ) is the quantity s of Ibrahim's closed form.

Evidence: 383/383 terminating ₂F₁ values and 447 EGF coefficients exact

Novelty check: Not in the source paper; routine rewriting. As far as we know new for this object.

References:
- M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1

## The r = δ(n) column of the QPS table is a Gegenbauer column, with a ξ-parity law

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved from the closed form (quadratic transformation of the terminating ₂F₁); sympy check n ≤ 30 · novelty: **unchecked**

> Let K = ⌊n/2⌋. For 1 ≤ k ≤ K − 1: Ω_{δ(n)}(k | ζ, ξ | n) = (−ζ)^k k! (2K−1)^{k↓}/(K−1)^{k↓} · C_k^{(K−k)}(ξ/2ζ); for 0 ≤ k ≤ K it equals (−1)^k (2K−1)^{k↓} Σ_i C(k,2i) (2i)!/(i! (K−1)^{i↓}) (−ζ²)^i ξ^{k−2i}. Hence Ω_{δ(n)}(k | ζ, −ξ | n) = (−1)^k Ω_{δ(n)}(k | ζ, ξ | n) — a parity law that fails for every other column. At k = K the λ → 0 limit is the classical corner Ψ(ζ, ξ, 2K) = (−1)^K V_K(ξ, ζ²).

Evidence: 196 Gegenbauer values and 1016 parity checks exact; explicit counterexample for other columns (n = 7, r = 0, k = 1)

Novelty check: Not in the source paper (which mentions only Chebyshev/Dickson at the corner). Standard special-function identities. As far as we know new for this object.

References:
- M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1
- DLMF §18.5 (Gegenbauer polynomials as ₂F₁) — https://dlmf.nist.gov/18.5

## Odd-n QPS tables contain the even-n tables as their r ≥ 1 columns

**Triboletti–Fable candidate** · kind: theorem · numeric-verified: True · proof: proved (Ω depends on (n, r) only through (n − r, n − 2r − δ(n−1)), which coincide for (r+1, n) and (r, n−1) when n is odd) · novelty: **unchecked**

> For every odd n ≥ 3 and all r, k ≥ 0: Ω_{r+1}(k | ζ, ξ | n) = Ω_r(k | ζ, ξ | n − 1). Consequently Ψ(ζ, ξ, 2m) and Ψ(ζ, ξ, 2m+1) sit in adjacent columns r = 1, 0 of the same layer k = m of the table n = 2m + 1. The analogous shift from even n fails (n = 8, r = 0, k = 1: −2(3ξ − ζ) ≠ −2(3ξ + ζ)).

Evidence: 3192 exact checks for odd n ≤ 29 (workflow), 1320 independent re-checks

Novelty check: Not in the source paper; elementary. As far as we know new for this object.

References:
- M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1

## Errata for the Mersenne Star paper (HAL v2 preprint)

**Triboletti–Fable candidate** · kind: source_correction · numeric-verified: True · proof: proved (exact computation n ≤ 40; Figure 1 vector content decoded) · novelty: **unchecked**

> (1) Section 10 prints Ω_0(n/2|1,−2|n) = Ω_0(n/2|0,1|n)·2^{δ(n+1)} and Ω_0(n/2|1,−3|n) = Ω_0(n/2|0,1|n)·{F(n), L(n)}; both are false as written (wrong by (−1)^{⌊n/2⌋} for n ≡ 2, 3 mod 4) and true with the anchor (0,−1) — as the paper's own p. 16 uses. (2) Lemma 7.4 (Ω_0(⌊n/2⌋|−1,4|n) = Ω_0(⌊n/2⌋|1,4|n) = Ω_0(⌊n/2⌋|1,−4|n)) is stated for 8 | n but holds exactly for all 4 | n (and n = 1) and for no other n ≤ 40. (3) The bullet on p. 11 listing (1, √5) among periodic points is wrong: Ψ(1, √5, n) is unbounded (|b| > 2). (4) The twelve edges of the Star are never listed; Figure 1 draws K_{2,6} (A and J joined to the six other points). (5) Cross-references cite 'Theorem 6.1' and 'Lemmas 6.3, 6.4' for results numbered 7.1, 7.3, 7.4.

Evidence: research workflow 2026-09-02; Lemma 7.4 range re-verified independently (tests/test_qps.py)

Novelty check: Errata; not previously published as far as we know.

References:
- M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 §10, Lemma 7.4, p. 11, Figure 1

## Conjecture: infinitely many primes in the Lehmer companions V̄_n(√5, 2) and V̄_n(√3, 2)

**Triboletti–Fable candidate** · kind: conjecture · numeric-verified: True · proof: unproved (heuristic of Wagstaff type; Hone–Jeffery–Selcoe prove the analogous Q = 1 statements only conditionally) · novelty: **unchecked**

> For (a, b) ∈ {(2,−1), (2,1), (2,3), (2,−3)} — the Lehmer companion pairs (R, Q) = (5,2), (3,2), (1,2), (7,2) — |Ψ(a, b, n)| is prime for infinitely many n; primes occur only at n = 2^k·m with m = 1, m prime, or m a product of 'unit' indices (d with |Ψ(a,b,d)| = 1) with a prime; and the number of prime indices ≤ N is asymptotic to Σ_{admissible n ≤ N} e^γ ln(2n)/ln|Ψ(a,b,n)| ≈ (4e^γ/ln 2) ln N ≈ 10.3 ln N for (2, ±1). Evidence: 57 and 58 primes for n ≤ 1000 against heuristic 56.6 and 55.7.

Evidence: prime counts for n ≤ 1000 (BPSW probable primes above 3.3·10^24); primitive-divisor theorem of Bilu–Hanrot–Voutier verified for n ≤ 120

Novelty check: The Q = 1 analogue is Conjecture 6.1–6.3 of Hone–Jeffery–Selcoe (arXiv:1802.01793); no statement for Q = 2 Lehmer companions found in OEIS or the accessible literature.

References:
- A. Hone, L. Jeffery, R. Selcoe, On a family of sequences related to Chebyshev polynomials, arXiv:1802.01793 — https://arxiv.org/abs/1802.01793
- S. S. Wagstaff Jr., Divisors of Mersenne numbers, Math. Comp. 40 (1983) 385–397
- Y. Bilu, G. Hanrot, P. Voutier, J. reine angew. Math. 539 (2001) 75–122

## Ψ-family sequences absent from OEIS (candidate submissions)

**Triboletti–Fable candidate** · kind: oeis_gap · numeric-verified: True · proof: proved (closed forms are Lehmer 1930) · novelty: **checked**

> As of 2026-09-02 OEIS has no entry (offsets 0, 1, 2 queried) for: Ψ(1,4,n) = V̄_n(√(−2),1) = 2,1,−4,−5,14,19,−52,−71,194,265,−724,−989,2702,3691,… (the paper's own Lucas–Lehmer Ψ-sequence; even part (−1)^m·A003500, odd part A001834; |Ψ(1,4,n)| prime for n ≤ 401 exactly at n = 0,3,5,7,13,19,29,37,293); Ψ(2,−1,n) = V̄_n(√5,2) = 2,1,1,−1,−7,−5,−11,−1,17,19,61,23,−7,−53,…; Ψ(2,1,n) = V̄_n(√3,2) = 2,1,−1,−3,−7,−1,11,13,17,−9,−61,−43,−7,79,…; their odd bisections and their prime-index sets. Recurrences: a(n) = −4a(n−2) − a(n−4); a(n) = a(n−2) − 4a(n−4); a(n) = −a(n−2) − 4a(n−4).

Evidence: OEIS JSON searches with leading term(s) dropped (2026-09-02); three earlier apparent gaps were refuted by the same method: Ψ(2,−5,n) = A076737(n+2), Ψ(−1,−6,n) = A159582 (n ≥ 1), Ψ(1,−6,n) = A079496 with even terms doubled

Novelty check: An OEIS submission is the legitimate way to attach a name to these; the mathematics is classical.

References:
- OEIS A003500, A001834, A299100, A272931 (bisections / prime indices) — https://oeis.org
- D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235

## No golden or residue structure in the 52 known exponents

**Triboletti–Fable candidate** · kind: negative_result · numeric-verified: True · proof: n/a (statistics) · novelty: **unchecked**

> Against a size-matched Monte-Carlo null (each exponent replaced by a random prime within a factor 1.5; 2000–20000 replications) none of the φ-zone, Fibonacci-zone, Beatty or golden-angle metrics of the known exponents differs from chance (p = 0.19–0.82), p mod 20 is consistent with equidistribution (p = 0.5), and no residue class mod 4, 8, 12, 20, 24 is significant after Bonferroni/Holm correction. The mod-12 nominal p ≈ 0.015 is a mod-3 × mod-4 interaction (21 of 50 exponents are 5 mod 12; Fisher p = 0.018) that does not survive correction and is not claimed.

Evidence: research/exponent_statistics.py (2000 reps) and an independent 20000-rep re-implementation in the workflow; both agree

Novelty check: A negative result; no prior test of these particular hypotheses was found, none was expected.

References:
- S. S. Wagstaff Jr., Math. Comp. 40 (1983) (mod-4 weighting)

```json
[
  {
    "slug": "periodicity-classification",
    "title": "Periodicity classification of the Ψ rings",
    "statement": "Ψ(1, −2cos 2θ, n) is periodic in n iff θ/2π = k/m is rational; the minimal period is m for even m and 2m for odd m.  Golden rings: b=φ (72°, 10), b=1−φ (36°, 10), b=−φ (18°, 20), b=φ−1 (54°, 20).",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (closed form; rotation form sympy-checked for n ≤ 8)",
    "novelty": "classical",
    "evidence": "exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30",
    "label": "Triboletti–Fable",
    "notes": "Ibrahim's own Chebyshev identity at x = cos θ plus the folklore criterion 'a linear recurrence is periodic iff its roots are roots of unity'. Lewin (1991) states the period formula for V_n(2cos θ, 1) explicitly; OEIS A087204 is the period-6 ring.",
    "details": {},
    "references": [
      "M. Lewin, Periodic Fibonacci and Lucas sequences, Fibonacci Quart. 29.4 (1991) 310–315, Thms 1–2 — https://www.fq.math.ca/Scanned/29-4/lewin.pdf",
      "E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308",
      "L. Somer, Fibonacci Quart. 18.4 (1980), Thm 4 — https://www.fq.math.ca/Scanned/18-4/somer.pdf",
      "T. MacHenry, K. Wong, arXiv:0712.2403, Thm 2.1 — https://arxiv.org/abs/0712.2403",
      "OEIS A087204 — https://oeis.org/A087204"
    ],
    "novelty_note": "Checked 2026-09-02 against Lucas 1878, Lewin 1991, Somer 1980, MacHenry–Wong 2007, Wikipedia (Lehmer sequence, Chebyshev polynomials) and OEIS: the statement is classical; only its application to Ibrahim's six examples is new bookkeeping."
  },
  {
    "slug": "golden-rings",
    "title": "Three golden rings not listed in the source paper",
    "statement": "Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.",
    "kind": "ring",
    "numeric_verified": true,
    "proof_status": "proved (corollary of the classification)",
    "novelty": "corollary_of_known",
    "evidence": "exact sequences in Z[φ] over three periods",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "Wikipedia, Golden ratio — pentagon and pentagram — https://en.wikipedia.org/wiki/Golden_ratio",
      "OEIS A001622 — https://oeis.org/A001622",
      "M. Lewin, Periodic Fibonacci and Lucas sequences, Fibonacci Quart. 29.4 (1991) 310–315, Thms 1–2 — https://www.fq.math.ca/Scanned/29-4/lewin.pdf",
      "M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 §16.1.6"
    ],
    "novelty_note": "2cos(π/5) = φ and 2cos(2π/5) = φ − 1 are classical (Euclid XIII.10, OEIS A001622); the three rings are one line from the classification. Not in Ibrahim's papers, but not a result either."
  },
  {
    "slug": "lehmer-identification",
    "title": "Ψ is Lehmer's companion sequence",
    "statement": "Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences; equivalently Ψ(a, b, n) = (2a − b)^{⌊n/2⌋}·V_n(1, a/(2a − b)).",
    "kind": "identity",
    "numeric_verified": true,
    "proof_status": "proved (both sides satisfy the same recurrence with the same initial values; sympy for n ≤ 12)",
    "novelty": "corollary_of_known",
    "evidence": "exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16",
    "label": "Triboletti–Fable",
    "notes": "This is the sharpest classical identification and it settles the novelty of every Ψ-ring statement. Ibrahim's eq. (36) prints the Binet form; no source states the Lehmer identification, which is a one-line substitution R = 2a − b, Q = a.",
    "details": {},
    "references": [
      "D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235",
      "MathWorld, Lehmer Number — https://mathworld.wolfram.com/LehmerNumber.html",
      "Wikipedia, Lehmer sequence — https://en.wikipedia.org/wiki/Lehmer_sequence",
      "E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf",
      "M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 eq. (36)"
    ],
    "novelty_note": "Checked 2026-09-02: Lehmer 1930, MathWorld 'Lehmer Number', Wikipedia 'Lehmer sequence', Roettger–Williams 2025 §2 give the definition; the identification with Ψ is not published but is immediate. Worth a remark, not a theorem."
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
    "notes": "Superseded by the Lehmer identification.",
    "details": {},
    "references": [
      "E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308",
      "D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235",
      "Wikipedia, Lucas sequence — https://en.wikipedia.org/wiki/Lucas_sequence"
    ],
    "novelty_note": "Checked 2026-09-02: Lucas 1878 / Lehmer 1930; Wikipedia 'Lucas sequence' (relations between sequences with different parameters)."
  },
  {
    "slug": "ll-index-constancy",
    "title": "Ring coordinates of the Lucas–Lehmer index are constant",
    "statement": "For every odd prime p ≥ 5, 2^{p−1} ≡ 4 (mod 6), 0 (mod 8), 4 (mod 12), 0 (mod 16), 4 or 16 (mod 20), 16 (mod 24); hence Ψ(1,1,2^{p−1}) = −1, Ψ(1,0,·) = 2, Ψ(1,−1,·) = −1, Ψ(1,√2,·) = 2, Ψ(1,φ−1,·) = −φ, Ψ(1,√3,·) = −1 independently of p. All periodic neighbours of the Mersenne Star carry no information about p, so the Star paper's proposal to use the periodic strips to accelerate Mersenne testing cannot work as stated.",
    "kind": "proposition",
    "numeric_verified": true,
    "proof_status": "proved (elementary)",
    "novelty": "classical",
    "evidence": "all primes 5 ≤ p < 400 and all 52 known Mersenne exponents",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 Theorem 7",
      "M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 §§1.4, 1.5, 12.1"
    ],
    "novelty_note": "Checked 2026-09-02: Ibrahim's own Theorem 7 (arXiv:2404.05772, eqs. 20, 24, 26, 31) states Ψ(1,φ−1,2^l) = −φ for even l ≥ 4 and the analogues for the other rings; the consequence for the Star paper's proposals is not drawn there."
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
    "references": [
      "E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf",
      "R. M. Robinson, Mersenne and Fermat numbers, Proc. AMS 5 (1954) 842–846",
      "OEIS A001566 — https://oeis.org/A001566",
      "Wikipedia, Lucas–Lehmer primality test — https://en.wikipedia.org/wiki/Lucas%E2%80%93Lehmer_primality_test"
    ],
    "novelty_note": "Checked 2026-09-02: Lucas 1876/1878 (M_127), Robinson 1954, Jansen 2012, Roettger–Williams 2025, OEIS A001566, Wikipedia (alternative starting values)."
  },
  {
    "slug": "qps-is-lucas-lehmer",
    "title": "Ibrahim's primality theorems and all 32 Mersenne Star conditions are the Lucas–Lehmer test",
    "statement": "Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; Theorem 26 of arXiv:2404.05772, Theorem 9 of arXiv:2502.06796 (B-ratio = Ψ(1, 4, 2^{p−1})) and all 32 conditions of Theorem 7.6 of the Mersenne Star paper reduce literally to 2^p − 1 | Ψ(1, 4, 2^{p−1}); they add no primality information beyond Lucas–Lehmer.",
    "kind": "source_correction",
    "numeric_verified": true,
    "proof_status": "proved (closed form Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n; anchor ratios computed exactly)",
    "novelty": "corollary_of_known",
    "evidence": "p ≤ 61 (Theorem 26 vs LL); p = 5, 7, 11, 13 for Theorem 9 and for all 32 Star conditions",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, Generalizing the Eight Levels Theorem, arXiv:2404.05772 — https://arxiv.org/abs/2404.05772 Theorem 26",
      "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1 Theorems 9, 47, 51",
      "M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 Theorem 7.6",
      "mersenneforum thread 'Eight levels theorem' (2024) — http://web.archive.org/web/20250116091733/https://www.mersenneforum.org/node/22736",
      "OEIS A003010 — https://oeis.org/A003010"
    ],
    "novelty_note": "Checked 2026-09-02: Theorem 26 is itself titled 'a new version for Lucas–Lehmer' and proved via LL in the source; the QPS paper proves Theorem 9 from that theorem; a 2024 mersenneforum thread already notes the equivalence. That the Star's 32 conditions carry nothing new is not stated in the Star paper."
  },
  {
    "slug": "mersenne-fibonacci-rank",
    "title": "Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)",
    "statement": "If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}); verified for every such known Mersenne prime up to p = 4423 and for p = 86243. For p ≡ 1 (mod 4) the rank divides M_p − 1 with odd cofactor 1, 1, 1, 9, 3, 1, 1, 1, 3 for p = 5, 13, 17, 61, 89, 521, 2281, 3217, 4253 (a power of 3 each time; consistent with chance).",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (Lucas's law of apparition + Lehmer's half-index criterion)",
    "novelty": "corollary_of_known",
    "evidence": "every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 4423 (plus 86243); cofactors from factordb factorizations of 2^{p−1} − 1",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "E. Lucas, Théorie des fonctions numériques simplement périodiques, Amer. J. Math. 1 (1878) — https://archive.org/details/jstor-2369308 pp. 289–305",
      "E. L. Roettger, H. C. Williams, Some remarks concerning the Lucas–Lehmer primality test, J. Integer Seq. 28 (2025) — https://cs.uwaterloo.ca/journals/JIS/VOL28/Roettger/roettger15.pdf",
      "J. H. Jaroma, Note on the Lucas–Lehmer test, Irish Math. Soc. Bull. 54 (2004) — https://www.maths.tcd.ie/pub/ims/bull54/M5402.pdf",
      "C. Guo, A. Koch, Bounds for Fibonacci period growth, Involve 2 (2009) — https://msp.org/involve/2009/2-2/involve-v2-n2-p04-p.pdf",
      "OEIS A000057 — https://oeis.org/A000057"
    ],
    "novelty_note": "Checked 2026-09-02: not found verbatim in OEIS (A001602, A000057, A001177), Wikipedia, MathWorld or the Prime Pages, but one step from Lucas 1878 and equivalent statements appear in Roettger–Williams 2025, Jaroma 2004, Guo–Koch 2009 (Thm 3.4) and Baker arXiv:2608.05319 (Prop. 1); OEIS A000057 (primes with entry point p+1) already lists 7, 127, 524287."
  },
  {
    "slug": "qps-closed-form",
    "title": "Closed form for the whole Quanta Prime Sequence table",
    "statement": "For all n ≥ 1, r, k ≥ 0, with N = n − r and u = n − 2r − δ(n−1): Ω_r(k | ζ, ξ | n) = Σ_{j=0}^{k} C(k, j) (2ζ − ξ)^{k−j} (−2ζ)^j · (N−j−1)^{(k−j)↓} · u(u−2)⋯(u−2j+2). In particular Ω depends on (n, r) only through (N, u). The three explicit formulas of the source (points (0,−1), (1,2), (1,−2), Theorems 42, 41, 19) are the special cases.",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (induction on k: the recurrence step is a symbolic identity in N, u, k, j; exact check for n ≤ 30, all r ≤ ⌊n/2⌋+3, all k ≤ ⌊n/2⌋)",
    "novelty": "unchecked",
    "evidence": "0 mismatches in 21 000 entries (workflow) and 8 000 entries (independent re-check), random (ζ, ξ) ∈ [−9, 9]²",
    "label": "Triboletti–Fable",
    "notes": "Standard technique (binomial sum solving a two-term recurrence); the value is that the QPS paper (2025) has no general formula.",
    "details": {},
    "references": [
      "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1 Definition 6.1, Theorems 19, 41, 42"
    ],
    "novelty_note": "Not in arXiv:2502.06796 (read in full); the arXiv API lists no follow-up papers. No wider literature search was possible for this 2025 object; as far as we know new, but routine."
  },
  {
    "slug": "qps-hypergeometric",
    "title": "Hypergeometric form and exponential generating function of the QPS table",
    "statement": "With N = n − r, u = n − 2r − δ(n−1), 2ζ ≠ ξ and k ≤ N − 1: Ω_r(k) = (2ζ − ξ)^k (N−1)^{k↓} · ₂F₁(−k, −u/2; 1 − N; 4ζ/(2ζ − ξ)) (terminating series), and Σ_k Ω_r(k) x^k/(k! (N−1)^{k↓}) = e^{(2ζ−ξ)x} · ₁F₁(−u/2; 1 − N; −4ζx). Note 1 − 4ζ/(2ζ−ξ) = −(2ζ+ξ)/(2ζ−ξ) is the quantity s of Ibrahim's closed form.",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (rewrite of the closed form with Pochhammer symbols; exact check n ≤ 18, EGF coefficients n ≤ 14)",
    "novelty": "unchecked",
    "evidence": "383/383 terminating ₂F₁ values and 447 EGF coefficients exact",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1"
    ],
    "novelty_note": "Not in the source paper; routine rewriting. As far as we know new for this object."
  },
  {
    "slug": "qps-gegenbauer-column",
    "title": "The r = δ(n) column of the QPS table is a Gegenbauer column, with a ξ-parity law",
    "statement": "Let K = ⌊n/2⌋. For 1 ≤ k ≤ K − 1: Ω_{δ(n)}(k | ζ, ξ | n) = (−ζ)^k k! (2K−1)^{k↓}/(K−1)^{k↓} · C_k^{(K−k)}(ξ/2ζ); for 0 ≤ k ≤ K it equals (−1)^k (2K−1)^{k↓} Σ_i C(k,2i) (2i)!/(i! (K−1)^{i↓}) (−ζ²)^i ξ^{k−2i}. Hence Ω_{δ(n)}(k | ζ, −ξ | n) = (−1)^k Ω_{δ(n)}(k | ζ, ξ | n) — a parity law that fails for every other column. At k = K the λ → 0 limit is the classical corner Ψ(ζ, ξ, 2K) = (−1)^K V_K(ξ, ζ²).",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved from the closed form (quadratic transformation of the terminating ₂F₁); sympy check n ≤ 30",
    "novelty": "unchecked",
    "evidence": "196 Gegenbauer values and 1016 parity checks exact; explicit counterexample for other columns (n = 7, r = 0, k = 1)",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1",
      "DLMF §18.5 (Gegenbauer polynomials as ₂F₁) — https://dlmf.nist.gov/18.5"
    ],
    "novelty_note": "Not in the source paper (which mentions only Chebyshev/Dickson at the corner). Standard special-function identities. As far as we know new for this object."
  },
  {
    "slug": "qps-shift-identity",
    "title": "Odd-n QPS tables contain the even-n tables as their r ≥ 1 columns",
    "statement": "For every odd n ≥ 3 and all r, k ≥ 0: Ω_{r+1}(k | ζ, ξ | n) = Ω_r(k | ζ, ξ | n − 1). Consequently Ψ(ζ, ξ, 2m) and Ψ(ζ, ξ, 2m+1) sit in adjacent columns r = 1, 0 of the same layer k = m of the table n = 2m + 1. The analogous shift from even n fails (n = 8, r = 0, k = 1: −2(3ξ − ζ) ≠ −2(3ξ + ζ)).",
    "kind": "theorem",
    "numeric_verified": true,
    "proof_status": "proved (Ω depends on (n, r) only through (n − r, n − 2r − δ(n−1)), which coincide for (r+1, n) and (r, n−1) when n is odd)",
    "novelty": "unchecked",
    "evidence": "3192 exact checks for odd n ≤ 29 (workflow), 1320 independent re-checks",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, On the emergence of the Quanta Prime Sequence, arXiv:2502.06796 — https://arxiv.org/html/2502.06796v1"
    ],
    "novelty_note": "Not in the source paper; elementary. As far as we know new for this object."
  },
  {
    "slug": "mersenne-star-errata",
    "title": "Errata for the Mersenne Star paper (HAL v2 preprint)",
    "statement": "(1) Section 10 prints Ω_0(n/2|1,−2|n) = Ω_0(n/2|0,1|n)·2^{δ(n+1)} and Ω_0(n/2|1,−3|n) = Ω_0(n/2|0,1|n)·{F(n), L(n)}; both are false as written (wrong by (−1)^{⌊n/2⌋} for n ≡ 2, 3 mod 4) and true with the anchor (0,−1) — as the paper's own p. 16 uses. (2) Lemma 7.4 (Ω_0(⌊n/2⌋|−1,4|n) = Ω_0(⌊n/2⌋|1,4|n) = Ω_0(⌊n/2⌋|1,−4|n)) is stated for 8 | n but holds exactly for all 4 | n (and n = 1) and for no other n ≤ 40. (3) The bullet on p. 11 listing (1, √5) among periodic points is wrong: Ψ(1, √5, n) is unbounded (|b| > 2). (4) The twelve edges of the Star are never listed; Figure 1 draws K_{2,6} (A and J joined to the six other points). (5) Cross-references cite 'Theorem 6.1' and 'Lemmas 6.3, 6.4' for results numbered 7.1, 7.3, 7.4.",
    "kind": "source_correction",
    "numeric_verified": true,
    "proof_status": "proved (exact computation n ≤ 40; Figure 1 vector content decoded)",
    "novelty": "unchecked",
    "evidence": "research workflow 2026-09-02; Lemma 7.4 range re-verified independently (tests/test_qps.py)",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "M. Ibrahim, The emergence of the Mersenne Star, HAL hal-05035758v2 (preprint of doi:10.1080/25765299.2025.2569155) — https://hal.science/hal-05035758v2 §10, Lemma 7.4, p. 11, Figure 1"
    ],
    "novelty_note": "Errata; not previously published as far as we know."
  },
  {
    "slug": "lehmer-q2-prime-conjecture",
    "title": "Conjecture: infinitely many primes in the Lehmer companions V̄_n(√5, 2) and V̄_n(√3, 2)",
    "statement": "For (a, b) ∈ {(2,−1), (2,1), (2,3), (2,−3)} — the Lehmer companion pairs (R, Q) = (5,2), (3,2), (1,2), (7,2) — |Ψ(a, b, n)| is prime for infinitely many n; primes occur only at n = 2^k·m with m = 1, m prime, or m a product of 'unit' indices (d with |Ψ(a,b,d)| = 1) with a prime; and the number of prime indices ≤ N is asymptotic to Σ_{admissible n ≤ N} e^γ ln(2n)/ln|Ψ(a,b,n)| ≈ (4e^γ/ln 2) ln N ≈ 10.3 ln N for (2, ±1). Evidence: 57 and 58 primes for n ≤ 1000 against heuristic 56.6 and 55.7.",
    "kind": "conjecture",
    "numeric_verified": true,
    "proof_status": "unproved (heuristic of Wagstaff type; Hone–Jeffery–Selcoe prove the analogous Q = 1 statements only conditionally)",
    "novelty": "unchecked",
    "evidence": "prime counts for n ≤ 1000 (BPSW probable primes above 3.3·10^24); primitive-divisor theorem of Bilu–Hanrot–Voutier verified for n ≤ 120",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "A. Hone, L. Jeffery, R. Selcoe, On a family of sequences related to Chebyshev polynomials, arXiv:1802.01793 — https://arxiv.org/abs/1802.01793",
      "S. S. Wagstaff Jr., Divisors of Mersenne numbers, Math. Comp. 40 (1983) 385–397",
      "Y. Bilu, G. Hanrot, P. Voutier, J. reine angew. Math. 539 (2001) 75–122"
    ],
    "novelty_note": "The Q = 1 analogue is Conjecture 6.1–6.3 of Hone–Jeffery–Selcoe (arXiv:1802.01793); no statement for Q = 2 Lehmer companions found in OEIS or the accessible literature."
  },
  {
    "slug": "oeis-gaps",
    "title": "Ψ-family sequences absent from OEIS (candidate submissions)",
    "statement": "As of 2026-09-02 OEIS has no entry (offsets 0, 1, 2 queried) for: Ψ(1,4,n) = V̄_n(√(−2),1) = 2,1,−4,−5,14,19,−52,−71,194,265,−724,−989,2702,3691,… (the paper's own Lucas–Lehmer Ψ-sequence; even part (−1)^m·A003500, odd part A001834; |Ψ(1,4,n)| prime for n ≤ 401 exactly at n = 0,3,5,7,13,19,29,37,293); Ψ(2,−1,n) = V̄_n(√5,2) = 2,1,1,−1,−7,−5,−11,−1,17,19,61,23,−7,−53,…; Ψ(2,1,n) = V̄_n(√3,2) = 2,1,−1,−3,−7,−1,11,13,17,−9,−61,−43,−7,79,…; their odd bisections and their prime-index sets. Recurrences: a(n) = −4a(n−2) − a(n−4); a(n) = a(n−2) − 4a(n−4); a(n) = −a(n−2) − 4a(n−4).",
    "kind": "oeis_gap",
    "numeric_verified": true,
    "proof_status": "proved (closed forms are Lehmer 1930)",
    "novelty": "checked",
    "evidence": "OEIS JSON searches with leading term(s) dropped (2026-09-02); three earlier apparent gaps were refuted by the same method: Ψ(2,−5,n) = A076737(n+2), Ψ(−1,−6,n) = A159582 (n ≥ 1), Ψ(1,−6,n) = A079496 with even terms doubled",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "OEIS A003500, A001834, A299100, A272931 (bisections / prime indices) — https://oeis.org",
      "D. H. Lehmer, An extended theory of Lucas' functions, Ann. of Math. 31 (1930) 419–448 — https://www.jstor.org/stable/1968235"
    ],
    "novelty_note": "An OEIS submission is the legitimate way to attach a name to these; the mathematics is classical."
  },
  {
    "slug": "exponent-statistics",
    "title": "No golden or residue structure in the 52 known exponents",
    "statement": "Against a size-matched Monte-Carlo null (each exponent replaced by a random prime within a factor 1.5; 2000–20000 replications) none of the φ-zone, Fibonacci-zone, Beatty or golden-angle metrics of the known exponents differs from chance (p = 0.19–0.82), p mod 20 is consistent with equidistribution (p = 0.5), and no residue class mod 4, 8, 12, 20, 24 is significant after Bonferroni/Holm correction. The mod-12 nominal p ≈ 0.015 is a mod-3 × mod-4 interaction (21 of 50 exponents are 5 mod 12; Fisher p = 0.018) that does not survive correction and is not claimed.",
    "kind": "negative_result",
    "numeric_verified": true,
    "proof_status": "n/a (statistics)",
    "novelty": "unchecked",
    "evidence": "research/exponent_statistics.py (2000 reps) and an independent 20000-rep re-implementation in the workflow; both agree",
    "label": "Triboletti–Fable",
    "notes": "",
    "details": {},
    "references": [
      "S. S. Wagstaff Jr., Math. Comp. 40 (1983) (mod-4 weighting)"
    ],
    "novelty_note": "A negative result; no prior test of these particular hypotheses was found, none was expected."
  }
]
```
