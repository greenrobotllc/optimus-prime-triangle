"""Smoke tests for main.py."""
from __future__ import annotations

import main as entry


def test_pipeline_smoke_p_max_200_no_plot(tmp_path):
    res = entry.run(entry.parse_args(["--p-max", "200", "--no-plot", "--cv-repeats", "2", "--out", str(tmp_path)]))
    confirmed = sorted(p for p, r in res["ll"].items() if r)
    assert confirmed == [5, 7, 13, 17, 19, 31, 61, 89, 107, 127]
    assert (tmp_path / "summary.csv").exists()
    assert all(res["bridge"].values())


def test_pipeline_research_smoke(tmp_path, monkeypatch):
    import config as cfg

    monkeypatch.setattr(cfg, "NMC_P_MAX", 60)
    monkeypatch.setattr(cfg, "WIEFERICH_LIMIT", 4000)
    monkeypatch.setattr(cfg, "WSS_LIMIT", 1000)
    monkeypatch.setattr(cfg, "LEDGER_PATH", tmp_path / "ledger.md")
    monkeypatch.setattr(cfg, "STATS_N_REP", 20)
    monkeypatch.setattr(cfg, "RANK_P_MAX_FACTOR", 17)
    monkeypatch.setattr(cfg, "RANK_P_MAX_CHECK", 127)
    res = entry.run(entry.parse_args(["--p-max", "100", "--no-plot", "--research", "--cv-repeats", "2", "--out", str(tmp_path)]))
    assert (tmp_path / "research_report.md").exists() and (tmp_path / "lean_skeletons.lean").exists()
    assert (tmp_path / "ledger.md").exists()
    assert res["research"]["nmc"]["counterexamples"] == []


def test_cli_rejects_nonpositive_repeats_and_tiny_pools(tmp_path):
    import pytest

    with pytest.raises(SystemExit):
        entry.parse_args(["--cv-repeats", "0"])
    with pytest.raises(SystemExit):
        entry.run(entry.parse_args(["--p-max", "11", "--no-plot", "--out", str(tmp_path)]))
