# optimus-prime-triangle
Research into the intersection of golden triangles and mersenne primes.
# PROJECT INITIALIZATION PROMPT: AI-Driven Geometric Prime Explorer

## 1. Project Context & Objectives
You are building an advanced mathematical discovery and simulation framework exploring the intersection of **Golden Triangles (the Golden Ratio $\phi$)**, **Mersenne Primes ($2^p - 1$)**, and **Geometric/Neuro-Symbolic AI**. Recent research indicates that the distribution of Mersenne primes aligns with specific periodic points (period 20) on a geometric coordinate map called the **Mersenne Star**, heavily influenced by Fibonacci/Lucas number harmonics.

The core goal of this repository is threefold:
1. **Geometric Modeling:** Implement visual and algebraic models of the Mersenne Triangle, Mersenne Star, and Golden Triangles.
2. **AI Heuristic Sieving:** Build a machine learning heuristic filter (using PyTorch or scikit-learn) that evaluates candidate prime exponents based on their proximity to Golden Ratio harmonic coordinate nodes, acting as a "smart pruning filter" before running a heavy Lucas-Lehmer test.
3. **Symbolic Proof Assistance:** Create an interface or pipeline designed to bridge discrete Mersenne values with continuous polynomial dynamics (referencing the "Eight Levels Theorem" framework).

## 2. Technical Stack Requirements
- **Language:** Python 3.11+
- **Math & ML Foundations:** `numpy`, `scipy`, `sympy` (for symbolic execution), `torch` or `scikit-learn` (for structural pattern recognition models)
- **Visualization:** `matplotlib`, `plotly` (for interactive 3D Mersenne Star maps)
- **Architecture:** Clean, modular structure separated into `/core_math`, `/ml_models`, `/visualization`, and `/tests`.

## 3. Initial Scaffolding Tasks (Step-by-Step)
Please generate the initial repository structure and write the following core modules:

### Task 1: Scaffolding and Environment
- Create a `requirements.txt` file including `numpy`, `scipy`, `sympy`, `plotly`, and `torch`.
- Write a modular `config.py` handling default parameters for candidate exponents ($p$) and $\phi$-based period cycles (e.g., period-20 nodes).

### Task 2: Core Mathematics Module (`/core_math`)
- **`mersenne.py`:** Implement a standard Lucas-Lehmer test for validation alongside a generator for Mersenne numbers.
- **`geometry.py`:** Implement coordinate generation logic for the Mersenne Triangle and the Mersenne Star projection system, calculating proximity metrics to Golden Ratio ($\phi$) convergence zones.

### Task 3: Machine Learning Framework (`/ml_models`)
- **`siever.py`:** Build a lightweight neural network or regression baseline model. It should take a candidate exponent $p$, convert it to its projected spatial features on the geometric Mersenne Star matrix, and output a "primality plausibility index" based on harmonic convergence.

### Task 4: Visualization Dashboard (`/visualization`)
- **`plotter.py`:** Create an interactive Plotly visualization that plots the Mersenne Star coordinate map, highlighting Golden Triangle intersections and marking known Mersenne primes dynamically.

## 4. Operational Instructions
- Write clean, type-hinted Python code.
- Provide descriptive inline docstrings explaining the underlying mathematical logic (QPS, Mersenne Star periodic points).
- Ensure an entry-point script `main.py` is created to run a quick test pipeline: calculating a small candidate pool, filtering them with the geometric AI heuristic, and rendering the 3D visualization map.

The Mersenne Triangle is a geometric and visual representation used to map prime-related relationships and Quanta Prime Sequence (QPS) dynamics. 
Archive ouverte HAL
Overview and Significance
Visualizing Primes: Instead of treating prime numbers and formulas as isolated text, the Mersenne Triangle acts as a bridge between abstract algebra and visual structures in space. 
Archive ouverte HAL
Quanta Prime Sequence (QPS): It organizes mathematical truths so they can be drawn rather than just calculated, revealing hidden organizational patterns in prime numbers. 
Archive ouverte HAL
Connection to the Mersenne Star: Research into these geometric representations expands into structures like the Mersenne Star, pointing toward a broader study of the geometry of prime numbers. 
Taylor & Francis Online +1
If you'd like, I can provide more details on how Mersenne numbers relate to triangular numbers or explain the Quanta Prime Sequence further.




Yes, there are active and emerging research opportunities at the intersection of Golden Triangles (and the Golden Ratio 
), Mersenne primes, and Artificial Intelligence.
Historically, Mersenne primes (numbers of the form ) and the Golden Ratio belonged to separate realms of math. However, recent breakthroughs in the "Geometry of Prime Numbers" and AI-driven mathematical discovery have revealed a hidden structural harmony connecting them. 
MathOverflow +3
Open problems and research frameworks where AI can be applied to this intersection include the following:
1. Pruning and Accelerating Large Mersenne Prime Searches
The Open Problem: Finding Mersenne primes is computationally grueling. The Great Internet Mersenne Prime Search (GIMPS) uses the Lucas-Lehmer test, which can take weeks for a single massive candidate number. 
Taylor & Francis Online +1
The Intersection: Recent research into the Mersenne Star—a geometric coordinate map of Mersenne distributions driven by the Quanta Prime Sequence (QPS)—has revealed that its structural periodic points tightly align with the Golden Ratio (
, period 20), Fibonacci numbers, and Lucas numbers. 
Archive ouverte HAL +1
The AI Opportunity: You can train Deep Learning or Geometric Neural Networks to look at candidate exponents. Instead of blindly running the Lucas-Lehmer test, an AI can evaluate how closely a candidate's mathematical properties map near these "Golden Ratio" harmonic points on the Mersenne Star geometry. This heuristic filter could predict which numbers are likely prime, potentially reducing prime-detection computation time from weeks to seconds. 
Quora +3
2. Generalizing the "Eight Levels Theorem" and Polynomial Dynamics
The Open Problem: Proving a formal, closed-form algebraic link between the transcendental geometry of 
 (inherent to Golden Triangles) and the discrete primality of Mersenne numbers. 
The Intersection: A paper titled "Generalizing the Eight Levels Theorem" mathematically linked Mersenne numbers to the derivatives of unique polynomial sequences. It explicitly mapped how the Golden Ratio constant influences the coefficients of these expansions, providing a bridge between number theory and differential equations. 
The AI Opportunity: AI systems like DeepMind’s AlphaGeometry or large language models trained on formal proof languages (like Lean or Coq) can be deployed here. AI can be used to search for, generate, and verify complex algebraic identities or boundary conditions within these newly discovered polynomial bridges that humans cannot compute by hand. 
Google DeepMind +1
3. Discovering Fractals in "Artificial Prime Intelligence"
The Open Problem: Mapping the discrete distribution of prime numbers into continuous geometric space. Golden Triangles can form logarithmic "Golden Spirals" (fractals), while Mersenne numbers form discrete nodes.
The Intersection: Emerging publications propose building an Artificial Prime Intelligence (API). This concept treats the distribution of primes as a continuous, symmetric holographic canvas where pure arithmetic collapses toward the Golden Section.
The AI Opportunity: This is prime territory for unsupervised Machine Learning (like Autoencoders or GANs). By feeding massive datasets of Mersenne sequences and Golden Triangle geometric matrices into an AI, the model can look for multidimensional structural patterns, symmetries, and structural "collapses" that point to an underlying mathematical law. 
ResearchGate +2
Summary of How to Get Started
To dive into this specific niche of mathematical AI research, focus your literature review on:
The Quanta Prime Sequence (QPS) and the Mersenne Star
AI-driven heuristic sieving for GIMPS distributed data
Neuro-symbolic AI architectures (like AlphaGeometry) that combine neural pattern recognition with strict geometric deduction. 
---

# Implementation notes (added with the scaffold)

Everything below documents what the code in this repository actually does and, just as
importantly, what the mathematics actually says.  The narrative above is the original brief;
two of its headline claims turned out to be false, and the code says so.

## Setup

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
```

```bash
.venv/bin/python -m pytest -q
```

```bash
.venv/bin/python main.py
```

`python main.py` (p ≤ 2500, logistic siever) runs in about 3 s and writes `output/mersenne_star.html`
(interactive 3-D map), `output/period20_wheel.png` and `output/summary.csv`.
`python main.py --full --model both` uses p ≤ 5000 and adds the torch MLP.
`python main.py --research` adds the research dashboards (≈ 10 s), writes `output/research_report.md`,
`output/growth_law.png`, `output/lean_skeletons.lean` and updates the ledger `discoveries/candidates.md`.

## Layout

| path | contents |
|---|---|
| `config.py` | every default: candidate range, the Ψ rings and their rotation angles, star layout, siever and research parameters, the discovery label |
| `core_math/mersenne.py` | Mersenne numbers, Lucas–Lehmer (universal seed 4; golden seed 3 for p ≡ 3 mod 4), trial factoring, Sophie-Germain factors, Wagstaff prior, the table of 52 known exponents |
| `core_math/psi_sequence.py` | Ibrahim's Ψ-sequence (recurrence, explicit sum, closed form, `O(log n)` modular ladder), exact quadratic-ring arithmetic (`QuadInt`), the periodic ring tables, Theorems 26/27/30 |
| `core_math/qps.py` | the Quanta Prime Sequence Ω and its Theorems 25, 11, 9 |
| `core_math/symbolic_bridge.py` | sympy proofs: homogeneity, differential-operator identities, Chebyshev/Dickson links, the normalisation identity, ring roots, the rotation form |
| `core_math/geometry.py` | golden triangles, pentagram, the rotation rings, the (interpreted) Mersenne Star, exponent placement and proximity metrics |
| `ml_models/` | leak-free features, labelled dataset, baselines + logistic + torch MLP, repeated stratified CV with an explicit honesty line |
| `research/` | growth laws (G1), Monte-Carlo tests of the geometric claims (G1b), New Mersenne Conjecture / Wieferich / Wall–Sun–Sun dashboards (G2–G4), the Fibonacci rank-of-apparition theorem (G4b), the periodicity classification (G7), the discovery census and ledger (G8), text-only Lean export |
| `visualization/plotter.py` | Plotly `graph_objects` 3-D map with stable trace names; matplotlib period-20 wheel |
| `tests/` | 124 exact tests; every identity quoted from the papers is checked with integer arithmetic |

## What the math actually says

The brief's sources are three papers by Moustafa Ibrahim: *Generalizing the Eight Levels Theorem*
([arXiv:2404.05772](https://arxiv.org/abs/2404.05772)), *On the Emergence of the Quanta Prime Sequence*
([arXiv:2502.06796](https://arxiv.org/abs/2502.06796)) and *The emergence of the Mersenne Star*
([doi:10.1080/25765299.2025.2569155](https://www.tandfonline.com/doi/full/10.1080/25765299.2025.2569155),
full text not accessible to us — the star geometry here is a documented interpretation).

* **The Ψ-sequence is D. H. Lehmer's companion sequence (1930).**  Exactly:
  `Ψ(a, b, n) = V̄_n(√(2a − b), a)`, where `V̄_n = V_n` for even `n` and `V_n/√R` for odd `n`,
  `α + β = √R`, `αβ = Q` (equivalently `Ψ(a, b, n) = (2a − b)^⌊n/2⌋ · V_n(1, a/(2a − b))`).  Every
  identity in the papers is therefore a statement about Lucas/Lehmer sequences and is proved
  mechanically in `symbolic_bridge.py`; the Eight Levels, the rings and the "new" polynomial
  classes are properties of Lehmer sequences whose roots lie on the unit circle.
* **Theorem 26 (and QPS Theorem 9) is the Lucas–Lehmer test.**  `Ψ(1, 4, 2^k)` is the Lucas–Lehmer term
  `s_{k−1}`, so the divisibility criterion is LL in different notation.  It is the *label* of the siever,
  never a feature.
* **Every periodic ring is a rotation.**  With `b = −2cos 2θ`, `Ψ(1, b, n) = 2cos nθ` for even `n`.  The
  ring is periodic iff `θ/2π = k/m` is rational, with period `m` (even `m`) or `2m` (odd `m`).  This
  reproduces the paper's six periods 6, 8, 12, 16, 20, 24 and predicts three golden rings the paper does
  not list: `b = φ` (72°, period 10), `b = 1 − φ` (36°, 10), `b = −φ` (18°, 20), alongside its `b = φ − 1`
  (54°, 20).  The four angles are exactly the golden-triangle angles.
* **Claim 1 of the brief is false: the period-20 golden nodes cannot predict Mersenne primes.**
  `2^{p−1} mod 20 ∈ {4, 16}` for every odd prime, so `Ψ(1, φ−1, 2^{p−1}) = −φ` for all `p ≥ 5`; in fact the
  Lucas–Lehmer index has the *same* coordinate on every ring (12 features are constant and are dropped
  by `VarianceThreshold`).  The rings are a coordinate system, not a sieve.
* **Claim 2 is not supported: the golden ratio does not govern exponent growth.**  Over the 52 known
  exponents the geometric-mean successive ratio is 1.424 (95 % bootstrap interval 1.32–1.56).  The
  Lenstra–Pomerance–Wagstaff factor 1.476 is inside the interval, Eberhart's 1.5 is inside, and φ = 1.618
  is outside (z ≈ 2.9).
* **A clean theorem on the golden-ratio side.**  If `M_p` is prime and `p ≡ 3 (mod 4)`, the
  Fibonacci rank of apparition of `M_p` is exactly `2^p = M_p + 1`: Lucas's golden-seed test gives
  `M_p | L_{2^{p−1}}`, and `F_{2^p} = F_{2^{p−1}} L_{2^{p−1}}` with `gcd(F_n, L_n) | 2`.  Verified for
  every known Mersenne prime with `p ≡ 3 (mod 4)` up to 4423.  For `p ≡ 1 (mod 4)` the rank divides
  `M_p − 1` and is maximal for `p = 5, 13, 17` but not for `p = 61` (cofactor 9) or `p = 89` (cofactor 3).
* **The data show no golden structure either.**  With a size-matched Monte-Carlo null (each exponent
  replaced by a random prime within a factor 1.5) none of the φ-zone / Fibonacci-zone / Beatty / golden-angle
  metrics of the 52 exponents differs from chance, and no residue class mod 4, 8, 12, 20 or 24 is
  significant after multiple-testing correction (`research/exponent_statistics.py`).
* **The one genuine golden-ratio ↔ Mersenne bridge is classical.**  Lucas's seed `s₀ = 3 = L₂` gives
  `s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}` and is valid exactly for `p ≡ 3 (mod 4)`; no seed built
  in `Q(√5)` can be universal because 5 is a quadratic residue mod `M_p` when `p ≡ 1 (mod 4)`.

## What the siever finds

Repeated stratified cross-validation on p ≤ 2500 (365 prime exponents, 15 positives):

| model | ROC-AUC | average precision | LL tests to recover every known exponent (out-of-fold) |
|---|---|---|---|
| constant | 0.50 | 0.04 | 337 |
| Wagstaff prior | 0.79 | 0.47 | 347 |
| logistic on geometry + arithmetic | 0.83 ± 0.02 | 0.43 ± 0.03 | 238 ± 34 |

The program prints the corresponding line itself: *no evidence of a geometric signal beyond the
number-theoretic prior*.  The ranking metric improves a little; average precision does not.  With 15
positives that is the expected outcome, and the pipeline is built so that a real signal would show up
as a lift over the Wagstaff prior larger than one standard deviation.

## Research goals

| # | open problem | equation | deliverable |
|---|---|---|---|
| G1 | infinitude of Mersenne primes; **Lenstra–Pomerance–Wagstaff** `#{p ≤ x} ~ e^γ log₂ x`; **Eberhart** `q_n ~ (3/2)^n` | `M_p = 2^p − 1` | `research/growth_laws.py` |
| G2 | **New Mersenne Conjecture** (Bateman–Selfridge–Wagstaff 1989) | `Ψ(−2,−5,p) = M_p`, `Ψ(2,−5,p) = (2^p+1)/3` | `nmc_dashboard`: no counterexample for p ≤ 1000; all three hold for p ∈ {3, 5, 7, 13, 17, 19, 31, 61, 127} |
| G3 | are all Mersenne numbers squarefree? (**Wieferich primes** `q² | 2^{q−1} − 1`) | | `wieferich_search`: {1093, 3511} below 10⁵; no `q² | M_p` for p ≤ 200, q ≤ 10⁵ |
| G4 | **Wall–Sun–Sun primes** `p² | F_{p−(5/p)}` | | none below 2·10⁴; every Mersenne prime `M_p` divides `F_{M_p − (5|M_p)}` |
| G5 | primes in Lucas sequences (no sequence proven to contain infinitely many) | normalisation identity | prime-density census over the (a, b) family |
| G6 | odd perfect numbers; Catalan–Mersenne `M_{M_127}` | | context only — out of computational reach |
| G7 | periodicity classification | `Ψ(1, −2cos 2θ, n) = 2cos nθ` | `research/periodicity.py`, exact verification |
| G8 | automated identity discovery | | `research/discovery.py`, ledger, Lean skeletons |

## On naming discoveries

`discoveries/candidates.md` is a ledger with a status ladder
`numeric-verified → sympy-proved / proved (elementary) → novelty: unchecked | classical | checked`.
The working label (`config.DISCOVERY_LABEL`, default "Triboletti–Fable") is a *working name*.  Mathematical
names stick only through publication and citation, and this repository never asserts novelty: the
normalisation identity is classical in substance (Lucas 1878), and the periodicity classification with its
three unlisted golden rings is the strongest first candidate — its ingredients are classical, its unified
statement is what the ledger records, and a human must check OEIS and the literature before claiming more.
