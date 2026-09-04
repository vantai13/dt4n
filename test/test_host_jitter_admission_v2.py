"""G-A016 admission must be measured under benchmark-like CPU pressure."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

from tools import g3_emitter_dryrun as E
from tools import host_jitter_probe as P
from tools.g2_topology import LINKS


@pytest.fixture(autouse=True)
def _current_tool_is_committed(monkeypatch):
    """Keep unit fixtures independent of whether the worktree is committed."""
    tool_hash = E.sha256(Path("tools/host_jitter_probe.py"))
    monkeypatch.setattr(E, "git_blob_sha256", lambda _commit, _path: tool_hash)


def _valid_payload(tmp_path: Path, **overrides) -> Path:
    ladder = E.build_ladder_cpu_maps()["L0"]
    tool = Path("tools/host_jitter_probe.py")
    stalls = 5
    windows = 1500
    point = stalls / windows
    bound = P.wilson_upper_95(stalls, windows)
    roles = [
        {
            "role": f"emitter-{LINKS[index]}",
            "cpu": ladder[index],
            "windows": windows,
            "stall_windows": stalls,
            "p_stall_1ms": point,
            "p_stall_1ms_wilson_upper_95": bound,
            "window_max_p99_s": 4.5e-5,
        }
        for index in range(len(LINKS))
    ]
    roles.extend([
        {
            "role": "sampler", "cpu": ladder[8], "windows": windows,
            "stall_windows": stalls, "p_stall_1ms": point,
            "p_stall_1ms_wilson_upper_95": bound,
            "window_max_p99_s": 4.5e-5,
        },
        {
            "role": "sink", "cpu": ladder[9], "windows": windows,
            "stall_windows": stalls, "p_stall_1ms": point,
            "p_stall_1ms_wilson_upper_95": bound,
            "window_max_p99_s": 4.5e-5,
        },
    ])
    payload = {
        "schema": E.ADMISSION_SCHEMA,
        "status": "NO_SOCKET_HOST_MEASUREMENT",
        "scenario": "after_quiesce",
        "mode": "ladder",
        "git_hash": E.git_hash(),
        "tool_path": tool.as_posix(),
        "tool_sha256": E.sha256(tool),
        "measured_at_unix": time.time(),
        "boot_id": E.read_boot_id(),
        "loadavg_at_start": 0.07,
        "roles": roles,
        "binding_role": "sink",
        "binding_cpu": ladder[9],
        "p_stall_1ms": point,
        "p_stall_1ms_wilson_upper_95": bound,
        "stall_threshold_s": 1e-3,
        "windows": windows,
        "scheduled_duration_s": 300.0,
    }
    payload.update(overrides)
    path = tmp_path / "jitter.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_the_gate_itself_is_unchanged():
    assert E.GATE_P_STALL == 0.02
    assert E.ADMISSION_MODE == "ladder"


def test_minimum_duration_has_more_than_the_signed_margin_factor():
    assert E.ADMISSION_MIN_DURATION_S == 300.0
    windows = int(E.ADMISSION_MIN_DURATION_S / E.DT_S)
    bound = P.wilson_upper_95(round(0.0033333 * windows), windows)
    assert E.GATE_P_STALL / bound > 1.5


def test_a_valid_ladder_probe_is_admitted(tmp_path):
    verdict = E.host_jitter_admission(_valid_payload(tmp_path))
    assert verdict["pass"] is True
    assert verdict["decided_on"] == "p_stall_1ms_wilson_upper_95"


def test_floor_mode_is_refused(tmp_path):
    verdict = E.host_jitter_admission(
        _valid_payload(tmp_path, mode="floor")
    )
    assert verdict["pass"] is False
    assert verdict["checks"]["mode_is_ladder"] is False


def test_wrong_l0_role_mapping_is_refused(tmp_path):
    path = _valid_payload(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["roles"][8]["cpu"] = payload["roles"][0]["cpu"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    verdict = E.host_jitter_admission(path)
    assert verdict["pass"] is False
    assert verdict["checks"]["covers_every_ladder_cpu"] is False
    assert verdict["checks"]["role_population_matches_l0"] is False


def test_admission_decides_on_the_bound_not_the_point_estimate(tmp_path):
    path = _valid_payload(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    # Six events in 300 windows: point estimate is exactly at the gate, but
    # the conservative endpoint exceeds it.
    bound = P.wilson_upper_95(6, 300)
    for row in payload["roles"]:
        row.update({
            "windows": 300,
            "stall_windows": 6,
            "p_stall_1ms": 0.02,
            "p_stall_1ms_wilson_upper_95": bound,
        })
    payload.update({
        "windows": 300,
        "p_stall_1ms": 0.02,
        "p_stall_1ms_wilson_upper_95": bound,
    })
    path.write_text(json.dumps(payload), encoding="utf-8")
    verdict = E.host_jitter_admission(path)
    assert verdict["pass"] is False
    assert verdict["decided_on"] == "p_stall_1ms_wilson_upper_95"


def test_a_sixty_second_probe_is_refused(tmp_path):
    verdict = E.host_jitter_admission(
        _valid_payload(tmp_path, scheduled_duration_s=60.0)
    )
    assert verdict["pass"] is False
    assert verdict["checks"]["duration_at_least_signed_minimum"] is False


def test_a_stale_artifact_is_refused(tmp_path):
    stale = time.time() - E.ADMISSION_MAX_AGE_S - 1.0
    verdict = E.host_jitter_admission(
        _valid_payload(tmp_path, measured_at_unix=stale)
    )
    assert verdict["pass"] is False
    assert verdict["checks"]["artifact_is_fresh"] is False


def test_an_artifact_from_another_boot_is_refused(tmp_path):
    verdict = E.host_jitter_admission(_valid_payload(
        tmp_path,
        boot_id="00000000-0000-0000-0000-000000000000",
    ))
    assert verdict["pass"] is False
    assert verdict["checks"]["same_boot"] is False


def test_binding_summary_must_match_the_worst_role(tmp_path):
    verdict = E.host_jitter_admission(_valid_payload(
        tmp_path,
        p_stall_1ms=0.0,
        p_stall_1ms_wilson_upper_95=P.wilson_upper_95(0, 1500),
    ))
    assert verdict["pass"] is False
    assert verdict["checks"]["binding_summary_consistent"] is False


def test_load1_is_reported_and_never_gating(tmp_path):
    verdict = E.host_jitter_admission(
        _valid_payload(tmp_path, loadavg_at_start=5.0)
    )
    assert verdict["pass"] is True
    assert verdict["load1_diagnostic_reference"] == 0.10


def test_declared_tool_must_match_the_version_in_its_commit(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(E, "git_blob_sha256", lambda _commit, _path: "0" * 64)
    verdict = E.host_jitter_admission(_valid_payload(tmp_path))
    assert verdict["pass"] is False
    assert verdict["checks"]["commit_tool_sha256_matches"] is False


def test_wilson_upper_matches_hand_computed_values():
    assert P.wilson_upper_95(1, 300) == pytest.approx(0.018637, abs=1e-5)
    assert P.wilson_upper_95(2, 300) == pytest.approx(0.023980, abs=1e-5)
    assert P.wilson_upper_95(2, 300) > E.GATE_P_STALL


def test_a016_execute_requires_live_admission(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", [
        "g3_emitter_dryrun", "--a016", "--execute",
        "--out", str(tmp_path / "result.json"),
    ])
    with pytest.raises(SystemExit, match="requires --live-admission"):
        E.main()


def test_live_probe_runs_before_first_a016_replicate(monkeypatch, tmp_path):
    events = []
    output = tmp_path / "benchmark.json"
    external = tmp_path / "external.json"
    external.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "g3_emitter_dryrun", "--a016", "--execute", "--live-admission",
        "--host-jitter-artifact", str(external), "--out", str(output),
    ])
    monkeypatch.setattr(E, "remote_provenance", lambda _tag: {"pass": True})
    monkeypatch.setattr(
        E,
        "host_jitter_admission",
        lambda path: (
            events.append(f"admit:{Path(path).name}")
            or {"pass": True, "binding_role": "sink"}
        ),
    )
    monkeypatch.setattr(
        E, "cpu_preflight", lambda _cpu_map: {"pass": True}
    )
    monkeypatch.setattr(
        P,
        "measure_artifact",
        lambda mode, duration, scenario: (
            events.append(f"measure:{mode}:{duration}:{scenario}") or {}
        ),
    )
    monkeypatch.setattr(
        P,
        "write_artifact",
        lambda path, _payload: events.append(f"write:{Path(path).name}"),
    )

    class FirstReplicateReached(RuntimeError):
        pass

    def _stop_at_first_replicate(*_args, **_kwargs):
        events.append("replicate")
        raise FirstReplicateReached

    monkeypatch.setattr(E, "run_replicate", _stop_at_first_replicate)
    with pytest.raises(FirstReplicateReached):
        E.main()
    assert events == [
        "admit:external.json",
        "measure:ladder:300.0:live_admission",
        "write:host_jitter_live_admission.json",
        "admit:host_jitter_live_admission.json",
        "replicate",
    ]
