"""Text-only export of ledger candidates as Lean 4 theorem skeletons (stretch goal).

No Lean toolchain is required or invoked.  The output is a starting point for a human
formalisation: a definition of the Ψ recurrence over ``ℤ`` (and over ``ℝ`` for golden
parameters, using Mathlib's ``goldenRatio``), one ``theorem … := by sorry`` per candidate,
and a pointer to Mathlib's existing Lucas–Lehmer development
(``Mathlib.NumberTheory.LucasLehmer``, ``LucasLehmer.lucas_lehmer_sufficiency``).
"""
from __future__ import annotations

import re

from research.discovery import Candidate

PREAMBLE = """import Mathlib

open Real

/-!  Ψ-sequence of Ibrahim (Definition 4.1):  Ψ 0 = 2, Ψ 1 = 1,
     Ψ (n+2) = (2a − b)^{δ(n+1)} · Ψ (n+1) − a · Ψ n,  δ(m) = m mod 2.  -/
def psiZ (a b : ℤ) : ℕ → ℤ
  | 0 => 2
  | 1 => 1
  | (n + 2) => (if n % 2 = 0 then (2 * a - b) else 1) * psiZ a b (n + 1) - a * psiZ a b n

noncomputable def psiR (a b : ℝ) : ℕ → ℝ
  | 0 => 2
  | 1 => 1
  | (n + 2) => (if n % 2 = 0 then (2 * a - b) else 1) * psiR a b (n + 1) - a * psiR a b n

/-- Mathlib already formalises the Lucas–Lehmer test: see
    `LucasLehmer.lucas_lehmer_sufficiency` in `Mathlib.NumberTheory.LucasLehmer`. -/
example : True := trivial
"""

_PROPS: dict[str, str] = {
    "golden-rings": (
        "(∀ n : ℕ, psiR 1 goldenRatio (n + 10) = psiR 1 goldenRatio n) ∧\n"
        "    (∀ n : ℕ, psiR 1 (1 - goldenRatio) (n + 10) = psiR 1 (1 - goldenRatio) n) ∧\n"
        "    (∀ n : ℕ, psiR 1 (-goldenRatio) (n + 20) = psiR 1 (-goldenRatio) n) ∧\n"
        "    (∀ n : ℕ, psiR 1 (goldenRatio - 1) (n + 20) = psiR 1 (goldenRatio - 1) n)"
    ),
    "periodicity-classification": (
        "∀ θ : ℝ, ∀ n : ℕ, psiR 1 (-2 * Real.cos (2 * θ)) (2 * n) = 2 * Real.cos (2 * n * θ)"
    ),
    "ll-index-constancy": (
        "∀ p : ℕ, p.Prime → 5 ≤ p → psiR 1 (goldenRatio - 1) (2 ^ (p - 1)) = -goldenRatio"
    ),
    "mersenne-fibonacci-rank": (
        "∀ p : ℕ, p.Prime → p % 4 = 3 → (2 ^ p - 1).Prime →\n"
        "    (2 ^ p - 1) ∣ Nat.fib (2 ^ p) ∧ ¬ (2 ^ p - 1) ∣ Nat.fib (2 ^ (p - 1))"
    ),
    "lehmer-identification": (
        "∀ a b : ℤ, ∀ n : ℕ, 0 < 2 * a - b →\n"
        "    (psiZ a b n : ℝ) = LehmerVbar (Real.sqrt (2 * a - b)) a n"
    ),
    "normalisation-identity": (
        "∀ a b : ℤ, ∀ n : ℕ, 2 * a ≠ b →\n"
        "    (psiZ a b n : ℚ) = ((2 * a - b : ℚ) ^ (n / 2)) * (LucasV (1 : ℚ) ((a : ℚ) / (2 * a - b)) n)"
    ),
}


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", s.lower()).strip("_")


def to_lean_statement(cand: Candidate) -> str:
    """A Lean 4 ``theorem`` skeleton (with ``sorry``) for one candidate."""
    name = f"{slugify(cand.label)}_{slugify(cand.slug)}"
    prop = _PROPS.get(cand.slug)
    doc = cand.statement.replace("-/", "- /")
    if prop is None:
        prop = "True"
        doc += "  TODO: transcribe this statement into a Lean proposition (placeholder `True`)."
    return f"/-- {doc} -/\ntheorem {name} :\n    {prop} := by\n  sorry\n"


def export(candidates: list[Candidate]) -> str:
    """Preamble plus one skeleton per candidate."""
    body = "\n".join(to_lean_statement(c) for c in candidates)
    helper = ("\n/-- Lucas V-sequence, needed by the normalisation identity. -/\n"
              "def LucasV (P Q : ℚ) : ℕ → ℚ\n  | 0 => 2\n  | 1 => P\n  | (n + 2) => P * LucasV P Q (n + 1) - Q * LucasV P Q n\n"
              "\n/-- Lehmer's companion sequence V̄_n(√R, Q): V_n for even n, V_n/√R for odd n. -/\n"
              "noncomputable def LehmerV (s Q : ℝ) : ℕ → ℝ\n  | 0 => 2\n  | 1 => s\n  | (n + 2) => s * LehmerV s Q (n + 1) - Q * LehmerV s Q n\n"
              "noncomputable def LehmerVbar (s Q : ℝ) (n : ℕ) : ℝ := if n % 2 = 0 then LehmerV s Q n else LehmerV s Q n / s\n")
    return PREAMBLE + helper + "\n" + body
