#!/usr/bin/env python3
"""Doi chung cho SLA manifest ngoai sinh (amendment 23-57)."""
from __future__ import annotations

import json
import os

import pytest

from measurements import sla_manifest_exogenous as M
from measurements.sla_exogenous import SLA_SPECS


@pytest.fixture(scope="module")
def rep():
    return M.build()


def test_same_schema_as_legacy(rep):
    """`G23-190`. Cung schema thi builder KHONG phai doi mot dong nao."""
    old = json.load(open(M.LEGACY, encoding="utf-8"))
    dropped = set(M.FIXPOINT_TRACES) | set(M.DERIVED_FROM_SLA)
    assert set(rep["cells"][0]) >= (set(old["cells"][0]) - dropped)
    assert len(rep["cells"]) == len(old["cells"])


def test_only_three_fields_change(rep):
    """Mot thi nghiem doi DUNG MOT THU. Neu doi hon, khong quy trach nhiem duoc."""
    old = {(c["mode"], c["rho_bar"]): c
           for c in json.load(open(M.LEGACY, encoding="utf-8"))["cells"]}
    allowed = ({"t_delay_ms", "t_loss", "w_loss", "loss_exchange",
                "sla_source", "sla_citation"}
               | set(M.FIXPOINT_TRACES) | set(M.DERIVED_FROM_SLA))
    for c in rep["cells"]:
        o = old[(c["mode"], c["rho_bar"])]
        changed = {k for k in set(c) | set(o)
                   if c.get(k, "\0") != o.get(k, "\0")}
        assert changed <= allowed, (
            "%s@%s doi truong ngoai danh sach: %s"
            % (c["mode"], c["rho_bar"], sorted(changed - allowed)))


def test_fixpoint_traces_are_removed(rep):
    """Hoa thach cua vong tu hieu chuan phai bi XOA.

    De lai thi sau nay se bi doc nham la nguong VAN noi sinh -- dung cai
    "nap nghia moi vao truong cu" da cam o amendment 23-52 muc 8.
    """
    for c in rep["cells"]:
        for k in M.FIXPOINT_TRACES:
            assert k not in c, "%s con dau vet fixpoint: %s" % (c["mode"], k)


def test_w_loss_matches_equal_budget_and_k06(rep):
    spec = SLA_SPECS["S-B"]
    assert rep["config"]["w_loss"] == pytest.approx(
        spec["t_delay_ms"] / spec["t_loss"])
    assert rep["config"]["w_loss"] == M.W_LOSS
    for c in rep["cells"]:
        assert c["w_loss"] == pytest.approx(c["t_delay_ms"] / c["loss_exchange"])


def test_manifest_carries_validity(rep):
    """`L68`: artifact PHAI mang truong `validity` de test chan kiem duoc."""
    v = rep["validity"]
    assert v["endogenous"] is False
    assert v["sla_axis"]["label"] == "exogenous_g114_S-B"
    assert v["sla_axis"]["citation"]
    # Vai tro DO truc: manifest DINH NGHIA truc SLA, khong TIEU THU no,
    # va hoan toan doc lap voi truc tuoi (amendment 23-45a).
    assert v["axis_role"] == "measures_axis"
    assert v["instrument"]["source_sha256"]
    assert v["inputs_sha256"]
    assert v["aoi_axis"]["label"] is None


def test_registered_sha_matches_the_file_on_disk():
    """`G23-193`. Sha trong registry phai la sha cua FILE THAT.

    Go tay mot sha la cach chac chan nhat de tao ra mot cai chan KHONG BAO
    GIO bat duoc gi.
    """
    reg = json.load(open("docs/phase-23/axis_registry.json", encoding="utf-8"))
    path = M.OUT_TMPL % "S-B"
    if not os.path.exists(path):
        pytest.skip("chua sinh manifest")
    entry = reg["sla_axis"].get(path)
    assert entry, "manifest chua duoc dang ky vao axis_registry"
    assert entry["content_sha256"] == M.sha256_file(path)
    assert entry["label"] in reg["approved_for_live"]["sla_axis"]


# -- amendment 23-58: xoa theo NGHIA, khong theo TEN (NT 50) -----------------
def test_manifest_carries_no_endogenous_derived_field(rep):
    """`G23-196`. Mot truong phai sinh sot lai la mot con SO SAI nam im o LIVE.

    `opt_viol_rate` cua `poisson@0.925` la 0.15000 trong ban cu nhung 0.99131
    duoi `S-B` -- sai 6.6 lan, o dung dai luong ma `L61` noi ve.
    """
    banned = set(M.DERIVED_FROM_SLA) | set(M.FIXPOINT_TRACES)
    for c in rep["cells"]:
        leak = sorted(banned & set(c))
        assert not leak, (
            "cell %s@%.3f con truong phai sinh tu SLA CU: %s\n"
            "  -> chung tinh duoi `w_loss`/nguong CU. Xoa, dung tinh lai o day."
            % (c["mode"], c["rho_bar"], leak))


def test_manifest_config_has_no_fixpoint_machinery(rep):
    """`G23-197`. `endogenous: false` + `target_viol: 0.15` la file TU MAU THUAN."""
    leak = sorted(set(M.CONFIG_FIXPOINT_KEYS) & set(rep["config"]))
    assert not leak, (
        "`config` con bo may tu hieu chuan: %s. File khai `endogenous = false` "
        "nhung mang MUC TIEU cua vong fixpoint -- reviewer se hoi ngay." % leak)


def test_manifest_points_at_the_authoritative_statistics(rep):
    """Xoa roi thi phai chi cho nguoi doc biet so DUNG nam o dau."""
    ds = rep["derived_statistics"]
    assert ds["authoritative_source"].endswith("sla_exogenous_S-B.json")
    assert set(ds["removed_fields"]) == set(M.DERIVED_FROM_SLA)
