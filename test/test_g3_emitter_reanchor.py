"""G-A014 re-anchor ledger: the emitter gates must survive the tag change.

`tools/g3_emitter_dryrun.py` refuses to execute unless local HEAD, origin
main, and its `PREREG_TAG` resolve to one commit.  G-A014 adds commits above
`phase-G-g3-emitter-reduction-prereg`, so the tag is re-anchored rather than
moved.  A re-anchor is only legitimate if no gate moved with it, so every
value doc 41 pinned is asserted here against a literal.  This turns the
prose claim in doc 42 section 6 into a machine-checked invariant: a silent
threshold edit under a new tag now fails the suite.
"""
from __future__ import annotations

from tools import g3_emitter_dryrun as E


def test_prereg_tag_is_the_reanchored_run_tag():
    """The tag is repointed to a new name; the old tag is never moved."""
    assert E.PREREG_TAG == "phase-G-g3-emitter-run-prereg"


def test_emitter_gates_are_unchanged_across_the_reanchor():
    assert E.GATE_OVERRUN_FRACTION == 0.001
    assert E.GATE_QUANT_SIGN == -0.05
    assert E.GATE_QUANT_PREDICTION == 0.05
    assert E.GATE_TIMING_CORRELATION == 0.10
    assert E.GATE_SNAPSHOT_P99_S == 0.001


def test_emit3_null_calibration_inputs_are_unchanged():
    """The doc-41 null (median .032332, p95 .045294, p99 .051107) is a
    deterministic function of exactly these four inputs."""
    assert E.EMIT3_NULL_TRIALS == 3000
    assert E.EMIT3_NULL_SEED == 20260909
    assert E.REPLICATES == 16
    assert E.N_WINDOWS == 300


def test_run_design_is_unchanged_across_the_reanchor():
    assert E.SEED == 20260908
    assert E.DT_S == 0.2
    assert E.DURATION_S == 60.0
    assert E.PAYLOAD_BYTES == 1400
    assert E.CELLS == (
        {"name": "anchor", "sigma_ref": 0.030348837209302317, "tau_s": 3.0},
        {"name": "stress", "sigma_ref": 0.020232558139534878, "tau_s": 30.0},
    )


def test_ladder_cpu_mapping_is_unchanged_across_the_reanchor():
    maps = E.build_ladder_cpu_maps(tuple(range(8)))
    assert maps["L0"] == (0, 1, 2, 3, 4, 5, 0, 1, 6, 7)
    assert maps["L1"] == (0, 1, 2, 0, 1, 2, 0, 1, 6, 7)
    assert maps["L2"] == (0, 0, 0, 0, 0, 0, 0, 0, 6, 7)


class _FakeRun:
    def __init__(self, stdout: str, returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode


def _fake_remote(monkeypatch, head: str, main: str, tag: str, returncode: int = 0):
    """Answer ls-remote from a canned table; never touch the network."""
    monkeypatch.setattr(E, "git_hash", lambda: head)
    lines = "%s\trefs/heads/main\n%s\trefs/tags/%s^{}\n" % (
        main, tag, E.PREREG_TAG
    )
    monkeypatch.setattr(
        E.subprocess, "run", lambda *a, **k: _FakeRun(lines, returncode)
    )


def test_provenance_identity_still_requires_all_three_to_agree(monkeypatch):
    """The stop rule itself is not relaxed by the re-anchor."""
    _fake_remote(monkeypatch, "a" * 40, "a" * 40, "a" * 40)
    assert E.remote_provenance()["pass"] is True


def test_provenance_refuses_when_the_tag_lags_head(monkeypatch):
    """Exactly the G-A014 situation before the re-anchor: HEAD moved past the tag."""
    _fake_remote(monkeypatch, "a" * 40, "a" * 40, "b" * 40)
    assert E.remote_provenance()["pass"] is False


def test_provenance_refuses_when_head_is_unpushed(monkeypatch):
    _fake_remote(monkeypatch, "a" * 40, "b" * 40, "a" * 40)
    assert E.remote_provenance()["pass"] is False


def test_provenance_refuses_when_the_remote_query_fails(monkeypatch):
    _fake_remote(monkeypatch, "a" * 40, "a" * 40, "a" * 40, returncode=128)
    assert E.remote_provenance()["pass"] is False
