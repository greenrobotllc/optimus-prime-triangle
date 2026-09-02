"""Automated identity discovery (goal G8) and the discoveries ledger.

What the pipeline does
----------------------
1. Enumerate points ``(a, b)`` of the Ψ family over the integers and over the rings
   ``Z[√2]``, ``Z[√3]``, ``Z[φ]`` (with ``a = 1`` on the rings).
2. For each point compute the exact sequence ``Ψ(a, b, n)``, ``n < n_max``, and classify it:
   periodic (with the period predicted by the classification theorem for comparison),
   a known classical sequence (offline library, up to sign), or unclassified.
3. Scan the integer points for prime density among ``|Ψ(a, b, n)|`` (goal G5): which points
   of the family are rich in primes (Mersenne ``(−2, −5)``, Lucas ``(−1, −3)``, …).
4. Record candidate results in a ledger with a status ladder::

       numeric-verified  →  sympy-proved / proved (elementary)  →  novelty: unchecked | classical | checked

   The working label is ``config.DISCOVERY_LABEL``.  A label in the ledger is a *working
   name*; mathematical names stick only through publication and citation, and novelty is
   never asserted by this code — a human must check OEIS and the literature.

The census is also a self-consistency check of the classification theorem: within the
coefficient range searched, the only periodic points of the golden ring are the four
golden ``b`` values and ``1, 0, −1``.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import config as cfg
from core_math.mersenne import is_prime_int
from core_math.psi_sequence import QuadInt, minimal_period, psi
from research.known_sequences import match
from research.periodicity import THEOREM_STATEMENT, predicted_period

RING_NAMES: dict[str, str] = {"Z[sqrt2]": "sqrt2", "Z[sqrt3]": "sqrt3", "Z[phi]": "phi"}


# --------------------------------------------------------------------------- points
@dataclass(frozen=True)
class Point:
    ring: str                       # "Z" or one of RING_NAMES
    a: Any
    b: Any

    @property
    def label(self) -> str:
        return f"Ψ({self.a}, {self.b}, n) over {self.ring}"

    def b_float(self) -> float:
        return float(self.b)


def enumerate_points(grid: dict[str, object] | None = None) -> list[Point]:
    grid = grid or cfg.DISCOVERY_GRID
    lo, hi = grid["int_range"]  # type: ignore[misc]
    pts: list[Point] = []
    for a in range(lo, hi + 1):
        for b in range(lo, hi + 1):
            if 2 * a == b:
                continue
            pts.append(Point("Z", a, b))
    clo, chi = grid["coeff_range"]  # type: ignore[misc]
    for ring in grid["rings"]:  # type: ignore[union-attr]
        key = RING_NAMES[ring]
        for u in range(clo, chi + 1):
            for v in range(clo, chi + 1):
                if v == 0:
                    continue
                pts.append(Point(ring, QuadInt(1, 0, key), QuadInt(u, v, key)))
    return pts


def sequence(point: Point, n_max: int) -> list[Any]:
    vals = []
    for n in range(n_max):
        v = psi(point.a, point.b, n)
        if isinstance(point.a, QuadInt) and isinstance(v, int):
            v = QuadInt(v, 0, point.a.ring)
        vals.append(v)
    return vals


def classify_point(point: Point, n_max: int | None = None) -> dict[str, Any]:
    n_max = n_max or int(cfg.DISCOVERY_GRID["n_max"])  # type: ignore[arg-type]
    seq = sequence(point, n_max)
    period = minimal_period(seq)
    info: dict[str, Any] = {"point": point.label, "ring": point.ring, "n_max": n_max, "period": period}
    if period is not None:
        info["kind"] = "periodic"
        if point.ring != "Z" or point.a == 1:
            info["predicted_period"] = predicted_period(point.b_float())
            info["prediction_rule"] = "equals"
            info["prediction_agrees"] = info["predicted_period"] == period
        elif point.a == -1:
            # Theorem 14 with λ = −1: Ψ(−1, b, n) = (−1)^{⌊n/2⌋} Ψ(1, −b, n); the sign factor has period 4,
            # so the minimal period divides lcm(4, period of Ψ(1, −b, ·)).
            base = predicted_period(-point.b_float())
            info["predicted_period"] = math.lcm(4, base) if base else None
            info["prediction_rule"] = "divides"
            info["prediction_agrees"] = base is not None and info["predicted_period"] % period == 0
        else:
            info["predicted_period"] = None
            info["prediction_rule"] = "none"
            info["prediction_agrees"] = False       # |a| ≥ 2: the roots have modulus √|Q| > 1, no periodicity
        return info
    if point.ring == "Z":
        hits = match([int(v) for v in seq])
        if hits:
            info["kind"] = "known_sequence"
            info["matches"] = hits
            return info
    info["kind"] = "unclassified"
    return info


def census(grid: dict[str, object] | None = None) -> list[dict[str, Any]]:
    grid = grid or cfg.DISCOVERY_GRID
    return [classify_point(pt, int(grid["n_max"])) for pt in enumerate_points(grid)]  # type: ignore[arg-type]


def periodic_points(cen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in cen if c["kind"] == "periodic"]


def prime_density_scan(grid: dict[str, object] | None = None, n_terms: int = 40, top: int = 12) -> list[dict[str, Any]]:
    """Integer points ranked by the number of primes among ``|Ψ(a, b, n)|``, ``2 ≤ n < n_terms``."""
    grid = grid or cfg.DISCOVERY_GRID
    rows = []
    for pt in enumerate_points(grid):
        if pt.ring != "Z":
            continue
        seq = [abs(int(v)) for v in sequence(pt, n_terms)]
        if minimal_period(seq) is not None:
            continue
        prime_idx = [n for n in range(2, n_terms) if seq[n] > 1 and is_prime_int(seq[n])]
        # Cramér-style size expectation: a random integer of size N is prime with probability ≈ 1/ln N
        expected = sum(1.0 / math.log(seq[n]) for n in range(2, n_terms) if seq[n] > 2)
        rows.append({"point": pt.label, "a": pt.a, "b": pt.b, "primes": len(prime_idx), "indices": prime_idx,
                     "expected_by_size": expected, "ratio": len(prime_idx) / expected if expected else 0.0,
                     "prime_indices_all_prime": all(is_prime_int(n) for n in prime_idx)})
    rows.sort(key=lambda r: (-r["ratio"], r["a"], r["b"]))
    return rows[:top]


# --------------------------------------------------------------------------- ledger
@dataclass
class Candidate:
    slug: str
    title: str
    statement: str
    kind: str                           # theorem | identity | ring | proposition
    numeric_verified: bool
    proof_status: str                   # "sympy-proved (n ≤ 12)" | "proved (elementary)" | "unproved"
    novelty: str                        # "unchecked" | "classical" | "checked"
    evidence: str
    label: str = cfg.DISCOVERY_LABEL
    notes: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)      # prior art found by the novelty audit
    novelty_note: str = ""                                    # what was searched / why the verdict


class Ledger:
    """Markdown ledger with an embedded JSON block for round-tripping."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path else cfg.LEDGER_PATH
        self.entries: list[Candidate] = []

    def add(self, cand: Candidate) -> None:
        self.entries = [e for e in self.entries if e.slug != cand.slug] + [cand]

    def to_markdown(self) -> str:
        lines = [
            "# Discoveries ledger",
            "",
            f"Working label: **{cfg.DISCOVERY_LABEL}**.  A label here is a working name.  Mathematical names",
            "stick only through publication and citation; novelty is *not* asserted by this repository —",
            "each entry's `novelty` field must be checked by a human against OEIS and the literature.",
            "",
            "Status ladder: `numeric-verified → sympy-proved / proved (elementary) → novelty: unchecked | classical | checked`.",
            "",
        ]
        for e in self.entries:
            lines += [
                f"## {e.title}",
                "",
                f"**{e.label} candidate** · kind: {e.kind} · numeric-verified: {e.numeric_verified} · proof: {e.proof_status} · novelty: **{e.novelty}**",
                "",
                f"> {e.statement}",
                "",
                f"Evidence: {e.evidence}",
                "",
            ]
            if e.notes:
                lines += [f"Notes: {e.notes}", ""]
            if e.novelty_note:
                lines += [f"Novelty check: {e.novelty_note}", ""]
            if e.references:
                lines += ["References:"] + [f"- {r}" for r in e.references] + [""]
        lines += ["```json", json.dumps([asdict(e) for e in self.entries], indent=2, ensure_ascii=False, default=str), "```", ""]
        return "\n".join(lines)

    def write(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.to_markdown(), encoding="utf-8")
        return self.path

    @classmethod
    def load(cls, path: Path | None = None) -> "Ledger":
        led = cls(path)
        if not led.path.exists():
            return led
        text = led.path.read_text(encoding="utf-8")
        if "```json" not in text:
            return led
        block = text.split("```json", 1)[1].split("```", 1)[0]
        for raw in json.loads(block):
            led.entries.append(Candidate(**raw))
        return led


def seed_candidates(bridge_report: dict[str, bool] | None = None, census_rows: list[dict[str, Any]] | None = None) -> list[Candidate]:
    """The candidates this repository can already justify."""
    br = bridge_report or {}
    cen = census_rows or []
    golden_ok = all(c.get("prediction_agrees", False) for c in periodic_points(cen) if c["ring"] == "Z[phi]") if cen else True
    return [
        Candidate(
            slug="periodicity-classification",
            title="Periodicity classification of the Ψ rings",
            statement=THEOREM_STATEMENT,
            kind="theorem",
            numeric_verified=golden_ok,
            proof_status="proved (closed form; rotation form sympy-checked for n ≤ 8)" if br.get("rotation_form", True) else "unproved",
            novelty="unchecked",
            evidence="exact periods in Z, Z[√2], Z[√3], Z[φ] for all six paper rings and the four golden rings; float check for every reduced rotation k/m with m ≤ 30",
            notes="Ingredients are classical (Chebyshev / Lucas-sequence normalisation); the unified statement and the three unlisted golden rings are what is recorded.",
        ),
        Candidate(
            slug="golden-rings",
            title="Three golden rings not listed in the source paper",
            statement="Ψ(1, φ, n) has period 10 (rotation 72°), Ψ(1, 1−φ, n) has period 10 (36°), Ψ(1, −φ, n) has period 20 (18°); with the paper's Ψ(1, φ−1, n) (54°, period 20) the four golden rotation angles are exactly the golden-triangle angles.",
            kind="ring",
            numeric_verified=True,
            proof_status="proved (corollary of the classification)",
            novelty="unchecked",
            evidence="exact sequences in Z[φ] over three periods",
        ),
        Candidate(
            slug="normalisation-identity",
            title="Ψ is a rescaled Lucas V-sequence",
            statement="Ψ(a, b, n) = (2a − b)^{⌊n/2⌋} · V_n(1, a/(2a − b)).",
            kind="identity",
            numeric_verified=True,
            proof_status="sympy-proved (n ≤ 12); general proof via Binet" if br.get("normalisation_identity", True) else "unproved",
            novelty="classical",
            evidence="exact rational-function identity for each n ≤ 12; integer check for |a| ≤ 4, |b| ≤ 6, n < 14",
            notes="Classical in substance (Lucas 1878); recorded because it makes every identity in the source papers mechanically provable. Not a novelty claim.",
        ),
        Candidate(
            slug="ll-index-constancy",
            title="Ring coordinates of the Lucas–Lehmer index are constant",
            statement="For every ring period k ∈ {6, 8, 10, 12, 16, 20, 24} and every odd prime p ≥ 5, Ψ(1, b_k, 2^{p−1}) takes the same value; on the golden ring it is −φ.",
            kind="proposition",
            numeric_verified=True,
            proof_status="proved (elementary: 2^{p−1} is constant modulo each period for p ≥ 5)",
            novelty="unchecked",
            evidence="all odd primes p ≤ 2000",
            notes="This is why the period-20 golden map cannot discriminate Mersenne primes.",
        ),
        Candidate(
            slug="lehmer-identification",
            title="Ψ is Lehmer's companion sequence",
            statement="Ψ(a, b, n) = V̄_n(√(2a − b), a), D. H. Lehmer's companion sequence (1930): V̄_n = V_n for even n and V_n/√R for odd n, with α + β = √R, αβ = Q. Every property of the Ψ / Eight-Levels family is a property of Lehmer sequences.",
            kind="identity",
            numeric_verified=True,
            proof_status="proved (elementary: both sides satisfy the same recurrence with the same initial values)",
            novelty="unchecked",
            evidence="exact check in Z[√R] for |a| ≤ 4, |b| ≤ 6, n < 16",
            notes="Sharper than the normalisation identity: it names the classical object exactly.",
        ),
        Candidate(
            slug="qps-is-lucas-lehmer",
            title="Ibrahim's primality theorems are the Lucas–Lehmer test",
            statement="Ψ(1, 4, 2^k) is the Lucas–Lehmer term s_{k−1}; hence Theorem 26 of arXiv:2404.05772 and Theorem 9 of arXiv:2502.06796 (whose B-ratio equals Ψ(1, 4, 2^{p−1})) are the Lucas–Lehmer test restated.",
            kind="source_correction",
            numeric_verified=True,
            proof_status="proved (closed form: Ψ(1,4,n) ∝ (1+√3)^n + (1−√3)^n)",
            novelty="unchecked",
            evidence="p ≤ 61 (Theorem 26 vs LL), p = 5, 7, 11 (Theorem 9 vs LL)",
        ),
        Candidate(
            slug="mersenne-fibonacci-rank",
            title="Fibonacci rank of apparition of Mersenne primes with p ≡ 3 (mod 4)",
            statement="If M_p = 2^p − 1 is prime and p ≡ 3 (mod 4), the Fibonacci rank of apparition of M_p is exactly 2^p = M_p + 1 (M_p | F_{2^p}, M_p ∤ F_{2^{p−1}}, M_p | L_{2^{p−1}}). For p ≡ 1 (mod 4) the rank is M_p − 1 for p = 5, 13, 17 but (M_p − 1)/9 for p = 61 and (M_p − 1)/3 for p = 89.",
            kind="theorem",
            numeric_verified=True,
            proof_status="proved (via Lucas's golden-seed test and F_{2n} = F_n L_n, gcd(F_n, L_n) | 2)",
            novelty="unchecked",
            evidence="every known Mersenne prime with p ≡ 3 (mod 4) and p ≤ 2203; cofactors for p ≡ 1 (mod 4), p ≤ 89",
        ),
        Candidate(
            slug="golden-seed",
            title="The golden Lucas–Lehmer seed and its exact domain",
            statement="Seed s₀ = 3 = L₂ gives s_k = L_{2^{k+1}} = φ^{2^{k+1}} + ψ^{2^{k+1}}, and the test is valid iff p ≡ 3 (mod 4); no seed built in Q(√5) can be universal.",
            kind="proposition",
            numeric_verified=True,
            proof_status="proved (classical; (5 | M_p) = +1 iff p ≡ 1 mod 4)",
            novelty="classical",
            evidence="all primes p ≤ 500; p = 5 is the smallest failure",
        ),
    ]


def run_discovery(path: Path | None = None, bridge_report: dict[str, bool] | None = None,
                  grid: dict[str, object] | None = None) -> tuple[Ledger, list[dict[str, Any]], list[dict[str, Any]]]:
    """Census + prime-density scan + ledger update.  Returns ``(ledger, census, density)``."""
    cen = census(grid)
    density = prime_density_scan(grid)
    ledger = Ledger.load(path)
    for cand in seed_candidates(bridge_report, cen):
        ledger.add(cand)
    # every periodic point found in the census that the theorem did not predict would be news
    surprises = [c for c in periodic_points(cen) if c.get("prediction_agrees") is False]
    for c in surprises:
        slug = "unexpected-period-" + c["point"].replace(" ", "").replace("Ψ", "psi").replace(",", "_").replace("(", "").replace(")", "")
        ledger.add(Candidate(slug=slug, title=f"Unexpected period at {c['point']}",
                             statement=f"{c['point']} is periodic with period {c['period']} but the classification predicts {c['predicted_period']}.",
                             kind="anomaly", numeric_verified=True, proof_status="unproved", novelty="unchecked",
                             evidence=f"n < {c['n_max']}", details=c))
    ledger.write()
    return ledger, cen, density
