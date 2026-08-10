#!/usr/bin/env python3
"""Phase 20R.6-v2 -- propagate residual bands and scan breakdown thresholds."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import math
import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from measurements import decision_error_v2 as D
from measurements import residual_spec as RS
from measurements.decision_error import spearman_rho
from mininet.topology_tandem import TANDEM_LINKS
from twin import cost_v2 as C
from twin import topology_v7 as T7


N_LINKS_IN_PATH = 3
G1_LO, G1_HI = 0.05, 0.40
G2_FLOOR = 0.03
R_MAX_DEFAULT = {"loss": 0.05, "delay_ms": 5.0}
JOINT_LAMBDA_R_MAX_DEFAULT = 10.0
VARIANTS = ("common_mode", "differential", "full", "joint")
DEFAULT_VARIANTS = VARIANTS
BLOCK_LEN_G7 = int(round(float(D.BLOCK_S) / float(D.DT)))
N_BOOT_BAND = 2000
TANDEM_CLASS = {str(name): (float(bw), int(q)) for name, _t7_link, bw, q, _base in TANDEM_LINKS}
TANDEM_CLASS_TO_T7 = {
    name: tuple(
        link
        for link, (bw, _base, q) in T7.LINKS.items()
        if (float(bw), int(q)) == link_class
    )
    for name, link_class in TANDEM_CLASS.items()
}
if any(not links for links in TANDEM_CLASS_TO_T7.values()):
    raise AssertionError("tandem class khong anh xa duoc sang topology_v7: %s" % TANDEM_CLASS_TO_T7)


class BiasedTruthTable(D.TruthTable):
    """Truth table plus additive residual; loss is clipped to the physical domain."""

    def __init__(self, resid_loss: float, resid_delay_ms: float, mode: str, parquet_path: str = D.TRUTH_TABLE):
        super().__init__(parquet_path)
        self._resid_loss = float(resid_loss)
        self._resid_delay = float(resid_delay_ms)
        self._mode = str(mode)
        self.clip_events = 0
        self.eval_count = 0

    def delay_loss(self, mode, link, rho):
        delay, loss = super().delay_loss(mode, link, rho)
        if str(mode) != self._mode:
            return delay, loss
        self.eval_count += int(np.asarray(rho).size)
        biased = loss + self._resid_loss
        self.clip_events += int(np.sum(biased < 0.0))
        return delay + self._resid_delay, np.clip(biased, 0.0, 1.0)


class LinkShiftTruthTable(D.TruthTable):
    """Truth table plus per-link additive residuals on selected topology links."""

    def __init__(self, shifts: Mapping[str, float], channel: str, mode: str, parquet_path: str = D.TRUTH_TABLE):
        super().__init__(parquet_path)
        self._shifts = {str(key): float(val) for key, val in shifts.items()}
        self._channel = str(channel)
        self._mode = str(mode)
        self.clip_events = 0
        self.eval_count = 0

    def delay_loss(self, mode, link, rho):
        delay, loss = super().delay_loss(mode, link, rho)
        if str(mode) != self._mode:
            return delay, loss
        self.eval_count += int(np.asarray(rho).size)
        resid = float(self._shifts.get(str(link), 0.0))
        if self._channel == "loss":
            biased = loss + resid
            self.clip_events += int(np.sum(biased < 0.0))
            return delay, np.clip(biased, 0.0, 1.0)
        if self._channel == "delay_ms":
            return delay + resid, loss
        raise ValueError("channel khong hop le: %s" % self._channel)


class JointLinkShiftTruthTable(D.TruthTable):
    """Truth table plus per-mode residuals, for conclusions that compare modes."""

    def __init__(
        self,
        mode_shifts: Mapping[str, Mapping[str, float]],
        channel: str,
        parquet_path: str = D.TRUTH_TABLE,
    ):
        super().__init__(parquet_path)
        self._mode_shifts = {
            str(mode): {str(link): float(val) for link, val in shifts.items()}
            for mode, shifts in mode_shifts.items()
        }
        self._channel = str(channel)
        self.clip_events = 0
        self.eval_count = 0

    def delay_loss(self, mode, link, rho):
        delay, loss = super().delay_loss(mode, link, rho)
        shifts = self._mode_shifts.get(str(mode))
        if shifts is None:
            return delay, loss
        self.eval_count += int(np.asarray(rho).size)
        resid = float(shifts.get(str(link), 0.0))
        if self._channel == "loss":
            biased = loss + resid
            self.clip_events += int(np.sum(biased < 0.0))
            return delay, np.clip(biased, 0.0, 1.0)
        if self._channel == "delay_ms":
            return delay + resid, loss
        raise ValueError("channel khong hop le: %s" % self._channel)


def link_residuals(rec: RS.ResidualRecord) -> Optional[Dict[str, float]]:
    vals = {str(key): float(val) for key, val in rec.per_unit.items()}
    if all(link in vals for link in TANDEM_CLASS_TO_T7):
        return {link: vals[link] for link in TANDEM_CLASS_TO_T7}
    return None


def decompose_residual(per_link: Mapping[str, float]) -> Dict[str, Any]:
    vals = np.asarray(list(per_link.values()), dtype=float)
    common = float(vals.mean())
    diff = {str(key): float(val - common) for key, val in per_link.items()}
    diff_rms = float(np.sqrt(np.mean((vals - common) ** 2)))
    return {
        "common_mode": common,
        "differential": diff,
        "diff_rms": diff_rms,
        "diff_over_cm": float(diff_rms / abs(common)) if common else float("inf"),
    }


def expand_tandem_shifts(per_link: Mapping[str, float]) -> Dict[str, float]:
    """Expand measured TandemTopo residuals to every topology_v7 link in the same class."""
    out: Dict[str, float] = {}
    for tandem_link, value in per_link.items():
        links = TANDEM_CLASS_TO_T7.get(str(tandem_link))
        if not links:
            raise ValueError("khong biet lop link tandem %r" % tandem_link)
        for t7_link in links:
            out[str(t7_link)] = float(value)
    return out


def variant_vectors(
    per_link: Mapping[str, float],
    r_endpoint: float,
    point: float,
    level: str = "per_link",
) -> Dict[str, Dict[str, float]]:
    """Return common/differential/full vectors with one shared scaling rule."""
    if not per_link:
        raise ValueError(
            "Phan du muc DUONG khong tach duoc common/differential: "
            "khong co thong tin per-link. Chi bien the common_mode duoc ho tro. "
            "KHONG duoc bom differential = 0 -> BOM RONG IM LANG (RC8)."
        )
    if abs(float(point)) < 1e-15:
        raise ValueError(
            "point ~ 0 -> khong dinh nghia duoc ti so co gian; "
            "phai ky mot quy tac khac trong prereg TRUOC khi chay"
        )
    scale = float(r_endpoint) / float(point)
    vals = {str(key): float(val) for key, val in per_link.items()}
    common = float(sum(vals.values()) / len(vals))
    return {
        "common_mode": {key: scale * common for key in vals},
        "differential": {key: scale * (val - common) for key, val in vals.items()},
        "full": {key: scale * val for key, val in vals.items()},
    }


def variant_supported(
    rec: RS.ResidualRecord,
    variant: str,
    records: Optional[Sequence[RS.ResidualRecord]] = None,
) -> bool:
    if variant == "common_mode":
        return True
    if variant in ("differential", "full"):
        return link_residuals(rec) is not None and abs(float(rec.point)) >= 1e-15
    if variant == "joint":
        if records is None:
            return False
        peers = [other for other in records if str(other.channel) == str(rec.channel)]
        return (
            len(peers) >= 2
            and all(abs(float(other.point)) >= 1e-15 for other in peers)
            and all(link_residuals(other) is not None for other in peers)
        )
    return False


def truth_table_for(rec: RS.ResidualRecord, variant: str, magnitude: float, sign: float = 1.0) -> D.TruthTable:
    """Build the perturbed table.

    ``magnitude`` is a scalar in the channel's native unit. For ``common_mode`` it
    is the direct pooled residual. For per-link variants, it scales the observed
    per-link pattern; this keeps the direction visible instead of pooling it away.
    """
    endpoint = float(sign) * float(magnitude)
    if variant == "joint":
        raise ValueError("joint can chay qua truth_table_for_joint")

    per_link = link_residuals(rec)
    if per_link is not None:
        vecs = variant_vectors(per_link, endpoint, rec.point, level=rec.level)
        if variant not in vecs:
            raise ValueError("variant khong hop le: %s" % variant)
        return LinkShiftTruthTable(expand_tandem_shifts(vecs[variant]), rec.channel, rec.mode)

    if variant == "common_mode":
        rl, rd = residual_to_link_shift(rec, endpoint)
        return BiasedTruthTable(rl, rd, rec.mode)

    raise ValueError("variant %s can only run when per_unit has L1/L2/L3" % variant)


def truth_table_for_joint(
    records: Sequence[RS.ResidualRecord],
    anchor: RS.ResidualRecord,
    magnitude: float,
    sign: float = 1.0,
    scale_rule: str = "qt3",
) -> D.TruthTable:
    """Build a full-vector perturbation for all modes in one channel.

    QT-3 interprets ``magnitude`` as dimensionless lambda: lambda=1 means every
    same-channel mode is perturbed by its own worst CI90 endpoint.  QT-1 is kept
    only for band back-compatibility, where joint is canonicalized to full.
    """
    endpoint = float(sign) * float(magnitude)
    if abs(float(anchor.point)) < 1e-15:
        raise ValueError("joint scan can anchor only on a non-zero point estimate")
    mode_shifts: Dict[str, Dict[str, float]] = {}
    for rec in records:
        if str(rec.channel) != str(anchor.channel):
            continue
        if abs(float(rec.point)) < 1e-15:
            raise ValueError("joint scan can anchor only on non-zero point estimates")
        if str(scale_rule) == "qt1":
            rec_endpoint = endpoint * float(rec.point) / float(anchor.point)
        elif str(scale_rule) == "qt3":
            ci_max = max(abs(float(x)) for x in rec.ci90)
            rec_endpoint = endpoint * ci_max
        else:
            raise ValueError("unknown joint scale rule: %s" % scale_rule)
        per_link = link_residuals(rec)
        if per_link is not None:
            vec = variant_vectors(per_link, rec_endpoint, rec.point, level=rec.level)["full"]
            mode_shifts[str(rec.mode)] = expand_tandem_shifts(vec)
            continue
        if str(rec.level) == "per_path":
            raise ValueError(
                "joint khong xac dinh cho phan du muc DUONG; chi common_mode duoc ho tro"
            )
        per_link_loss, per_link_delay = residual_to_link_shift(rec, rec_endpoint)
        scalar = per_link_loss if rec.channel == "loss" else per_link_delay
        mode_shifts[str(rec.mode)] = {link: float(scalar) for link in T7.LINK_NAMES}
    return JointLinkShiftTruthTable(mode_shifts, anchor.channel)


def unsupported_reason(variant: str) -> str:
    if variant == "joint":
        return (
            "joint requires non-zero per-link residuals for at least two mode records "
            "in the same channel; path-only residual is common-mode only"
        )
    return "requires per_unit L1/L2/L3; path-only residual is common-mode only"


def truth_table_for_variant(
    rec: RS.ResidualRecord,
    variant: str,
    magnitude: float,
    sign: float = 1.0,
    records: Optional[Sequence[RS.ResidualRecord]] = None,
    joint_scale_rule: str = "qt3",
) -> D.TruthTable:
    if variant == "joint":
        if records is None:
            raise ValueError("joint requires all residual records")
        return truth_table_for_joint(records, rec, magnitude, sign=sign, scale_rule=joint_scale_rule)
    return truth_table_for(rec, variant, magnitude, sign=sign)


def path_ranking(tt: D.TruthTable, mode: str, rho_bar: float, w_loss: float) -> Tuple[str, ...]:
    rho = C.rho_vector(float(rho_bar))
    rho_mat = np.asarray([[rho[link] for link in T7.LINK_NAMES]], dtype=float)
    _delay, _loss, cost = tt.path_tables(mode, rho_mat, w_loss)
    order = np.argsort(cost[0])
    return tuple(T7.PATH_NAMES[int(i)] for i in order)


def cell_metrics(tt: D.TruthTable, cv2: C.CostV2, cell: Mapping[str, Any], seeds: Sequence[int], n: int) -> Dict[str, float]:
    acc: Dict[str, List[float]] = {"err_total": [], "d_sla": []}
    for seed in seeds:
        arrays = D._cell_arrays(tt, cv2, cell, seed=int(seed), n=int(n))
        series = D._sawtooth_metric_series(arrays)
        for key in acc:
            acc[key].append(float(np.mean(series[key])))
    return {key: float(np.mean(vals)) for key, vals in acc.items()}


def mcnemar_p_value(b_count: int, c_count: int) -> Dict[str, Any]:
    """Two-sided paired sign/McNemar p value for discordant binary outcomes."""
    b_count = int(b_count)
    c_count = int(c_count)
    disc = b_count + c_count
    if disc == 0:
        return {"p_mcnemar": 1.0, "p_mcnemar_exact": 1.0, "p_mcnemar_method": "degenerate"}
    if disc <= 25:
        k = min(b_count, c_count)
        p = 2.0 * sum(math.comb(disc, i) for i in range(k + 1)) / float(2**disc)
        return {
            "p_mcnemar": float(min(p, 1.0)),
            "p_mcnemar_exact": float(min(p, 1.0)),
            "p_mcnemar_method": "exact_binomial",
        }
    z = abs(b_count - c_count) / math.sqrt(float(disc))
    p = math.erfc(z / math.sqrt(2.0))
    return {"p_mcnemar": float(p), "p_mcnemar_exact": None, "p_mcnemar_method": "normal_approx"}


def paired_binary_counts(base: np.ndarray, perturbed: np.ndarray) -> Dict[str, int]:
    e0 = np.asarray(base).astype(bool)
    e1 = np.asarray(perturbed).astype(bool)
    if e0.shape != e1.shape:
        raise AssertionError("hai chuoi khong cung do dai -> KHONG ghep cap duoc")
    b_count = int(np.sum(~e0 & e1))
    c_count = int(np.sum(e0 & ~e1))
    return {
        "b": b_count,
        "c": c_count,
        "n_discordant": b_count + c_count,
        "n_total": int(e0.size),
    }


def paired_binary_contrast(base: np.ndarray, perturbed: np.ndarray) -> Dict[str, Any]:
    counts = paired_binary_counts(base, perturbed)
    n_total = max(int(counts["n_total"]), 1)
    disc = int(counts["n_discordant"])
    d_err = float((int(counts["b"]) - int(counts["c"])) / n_total)
    out: Dict[str, Any] = {
        **counts,
        "d_err": d_err,
        "se_paired": float(math.sqrt(disc) / n_total) if disc else 0.0,
        "se_unpaired_for_reference": float(math.sqrt(0.25 / n_total)),
        "note": (
            "se_unpaired KHONG dung cho d_err: hai ve dung CUNG mau, "
            "chi khac bang tra. Chi cap BAT DONG mang thong tin."
        ),
    }
    out.update(mcnemar_p_value(int(counts["b"]), int(counts["c"])))
    out["mc_resolvable"] = bool(out["p_mcnemar"] < 0.05)
    return out


def block_bootstrap_mean(
    block_means: Sequence[np.ndarray],
    n_boot: int = N_BOOT_BAND,
    seed: int = 20206,
) -> Dict[str, Any]:
    blocks = np.concatenate([np.asarray(part, dtype=float) for part in block_means])
    if blocks.size == 0:
        raise ValueError("khong co block nao de bootstrap")
    rng = np.random.default_rng(int(seed))
    draws = np.empty(int(n_boot), dtype=float)
    for i in range(int(n_boot)):
        pick = rng.integers(0, int(blocks.size), size=int(blocks.size))
        draws[i] = float(blocks[pick].mean())
    return {
        "se": float(np.std(draws, ddof=1)) if draws.size > 1 else 0.0,
        "ci90": [float(np.percentile(draws, 5.0)), float(np.percentile(draws, 95.0))],
        "n_blocks": int(blocks.size),
        "n_boot": int(n_boot),
    }


def _series_block_means(values: np.ndarray, requested_block_len: int = BLOCK_LEN_G7) -> Tuple[np.ndarray, int, bool]:
    arr = np.asarray(values, dtype=float)
    block_len = min(int(requested_block_len), int(arr.size))
    if block_len <= 0:
        raise ValueError("chuoi rong -> khong bootstrap duoc")
    return D._block_means(arr, block_len), int(block_len), bool(block_len != int(requested_block_len))


def _block_resolvable(mean: float, ci90: Sequence[float]) -> bool:
    lo, hi = float(ci90[0]), float(ci90[1])
    return bool((lo > 0.0 and hi > 0.0) or (lo < 0.0 and hi < 0.0))


def paired_metric_contrast(
    tt_base: D.TruthTable,
    tt_pert: D.TruthTable,
    cv2: C.CostV2,
    cell: Mapping[str, Any],
    seeds: Sequence[int],
    n: int,
) -> Dict[str, Any]:
    """Paired contrasts for sawtooth metrics on identical seeds and rho traces."""
    b_tot = c_tot = n_tot = 0
    base_err_sum = pert_err_sum = 0.0
    base_dsla_sum = pert_dsla_sum = 0.0
    dsla_delta_sum = 0.0
    dsla_delta_sumsq = 0.0
    err_blocks = []
    dsla_blocks = []
    block_len_effective: Optional[int] = None
    block_len_truncated = False
    for seed in seeds:
        base_series = D._sawtooth_metric_series(D._cell_arrays(tt_base, cv2, cell, seed=int(seed), n=int(n)))
        pert_series = D._sawtooth_metric_series(D._cell_arrays(tt_pert, cv2, cell, seed=int(seed), n=int(n)))
        e0 = np.asarray(base_series["err_total"]).astype(bool)
        e1 = np.asarray(pert_series["err_total"]).astype(bool)
        counts = paired_binary_counts(e0, e1)
        b_tot += int(counts["b"])
        c_tot += int(counts["c"])
        n_tot += int(counts["n_total"])
        base_err_sum += float(np.sum(e0))
        pert_err_sum += float(np.sum(e1))
        signed_err = (~e0 & e1).astype(float) - (e0 & ~e1).astype(float)
        blocks, eff_len, truncated = _series_block_means(signed_err)
        err_blocks.append(blocks)
        block_len_effective = eff_len if block_len_effective is None else min(block_len_effective, eff_len)
        block_len_truncated = bool(block_len_truncated or truncated)

        d0 = np.asarray(base_series["d_sla"], dtype=float)
        d1 = np.asarray(pert_series["d_sla"], dtype=float)
        if d0.shape != d1.shape:
            raise AssertionError("hai chuoi d_sla khong cung do dai -> KHONG ghep cap duoc")
        delta = d1 - d0
        base_dsla_sum += float(np.sum(d0))
        pert_dsla_sum += float(np.sum(d1))
        dsla_delta_sum += float(np.sum(delta))
        dsla_delta_sumsq += float(np.sum(delta * delta))
        blocks, eff_len, truncated = _series_block_means(delta)
        dsla_blocks.append(blocks)
        block_len_effective = eff_len if block_len_effective is None else min(block_len_effective, eff_len)
        block_len_truncated = bool(block_len_truncated or truncated)

    n_safe = max(n_tot, 1)
    err_boot = block_bootstrap_mean(err_blocks, seed=20206)
    dsla_boot = block_bootstrap_mean(dsla_blocks, seed=20207)
    err_iid_se = float(math.sqrt(b_tot + c_tot) / n_safe) if (b_tot + c_tot) else 0.0
    err = {
        "b": int(b_tot),
        "c": int(c_tot),
        "n_discordant": int(b_tot + c_tot),
        "n_total": int(n_tot),
        "d_err": float((b_tot - c_tot) / n_safe),
        "base_err": float(base_err_sum / n_safe),
        "perturbed_err": float(pert_err_sum / n_safe),
        "se_paired": err_iid_se,
        "se_iid_mcnemar": err_iid_se,
        "se_block": err_boot["se"],
        "ci90_block": err_boot["ci90"],
        "resolvable_block": _block_resolvable(float((b_tot - c_tot) / n_safe), err_boot["ci90"]),
        "inflation_factor": (
            float(err_boot["se"] / err_iid_se) if err_iid_se > 0.0 else None
        ),
        "block_len": int(block_len_effective or BLOCK_LEN_G7),
        "block_len_requested": int(BLOCK_LEN_G7),
        "block_len_truncated": block_len_truncated,
        "n_blocks": int(err_boot["n_blocks"]),
        "n_boot": int(err_boot["n_boot"]),
        "se_unpaired_for_reference": float(math.sqrt(0.25 / n_safe)),
        "note": (
            "se_iid_mcnemar gia dinh cap bat dong doc lap; chuoi rho(t) co tuong quan "
            "thoi gian. Gate G7 yeu cau block bootstrap, nen dung se_block/ci90_block."
        ),
    }
    err.update(mcnemar_p_value(b_tot, c_tot))
    err["mc_resolvable"] = bool(err["p_mcnemar"] < 0.05)

    if n_tot > 1:
        var = max((dsla_delta_sumsq - (dsla_delta_sum * dsla_delta_sum) / n_tot) / (n_tot - 1), 0.0)
    else:
        var = 0.0
    dsla_iid_se = float(math.sqrt(var / n_safe))
    d_sla = {
        "d_d_sla": float(dsla_delta_sum / n_safe),
        "base_d_sla": float(base_dsla_sum / n_safe),
        "perturbed_d_sla": float(pert_dsla_sum / n_safe),
        "se_paired": dsla_iid_se,
        "se_iid": dsla_iid_se,
        "se_block": dsla_boot["se"],
        "ci90_block": dsla_boot["ci90"],
        "resolvable_block": _block_resolvable(float(dsla_delta_sum / n_safe), dsla_boot["ci90"]),
        "inflation_factor": (
            float(dsla_boot["se"] / dsla_iid_se) if dsla_iid_se > 0.0 else None
        ),
        "block_len": int(block_len_effective or BLOCK_LEN_G7),
        "block_len_requested": int(BLOCK_LEN_G7),
        "block_len_truncated": block_len_truncated,
        "n_blocks": int(dsla_boot["n_blocks"]),
        "n_boot": int(dsla_boot["n_boot"]),
        "n_total": int(n_tot),
    }
    return {"err": err, "d_sla": d_sla}


def is_algebraic_identity_case(rec: RS.ResidualRecord, variant: str) -> bool:
    if rec.channel != "delay_ms" or variant != "common_mode":
        return False
    path_lengths = {len(path) for path in T7.PATHS.values()}
    return len(path_lengths) == 1


def injection_vector(rec: RS.ResidualRecord, variant: str, endpoint: float) -> Dict[str, float]:
    per_link = link_residuals(rec)
    if variant == "joint":
        variant = "full"
    if per_link is not None:
        return variant_vectors(per_link, float(endpoint), rec.point)[variant]
    if variant != "common_mode":
        raise ValueError("variant %s requires per-unit residuals" % variant)
    loss_shift, delay_shift = residual_to_link_shift(rec, float(endpoint))
    scalar = loss_shift if rec.channel == "loss" else delay_shift
    return {link: float(scalar) for link in TANDEM_CLASS_TO_T7}


def injection_rms(rec: RS.ResidualRecord, variant: str, endpoint: float) -> float:
    vals = np.asarray(list(injection_vector(rec, variant, endpoint).values()), dtype=float)
    return float(np.sqrt(np.mean(vals * vals)))


def potency_summary(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    by_key: Dict[str, Dict[str, float]] = {}
    for row in rows:
        if not row.get("supported", True) or row.get("variant") == "joint":
            continue
        key = "%s|%s" % (row.get("cell"), row.get("channel"))
        by_key.setdefault(key, {})[str(row.get("variant"))] = float(row.get("potency", 0.0))

    out: Dict[str, Any] = {}
    for key, vals in by_key.items():
        common = vals.get("common_mode")
        diff = vals.get("differential")
        if common is None or diff is None:
            ratio = None
        elif common == 0.0:
            ratio = float("inf") if diff > 0.0 else None
        else:
            ratio = float(diff / common)
        out[key] = {
            "potency_by_variant": vals,
            "differential_over_common_mode": ratio,
        }
    return out


def loss_common_mode_leakage(tt: D.TruthTable, modes: Sequence[str], rho_bar: float) -> Dict[str, Any]:
    """Sensitivity of nonlinear path loss composition to a uniform link-loss shift."""
    rho = C.rho_vector(float(rho_bar))
    out: Dict[str, Any] = {}
    for mode in sorted(set(str(mode) for mode in modes)):
        deriv_by_path = {}
        for path_name, links in T7.PATHS.items():
            losses = []
            for link in links:
                _delay, loss = tt.delay_loss(mode, link, np.asarray([rho[link]], dtype=float))
                losses.append(float(loss[0]))
            keeps = np.asarray([1.0 - p for p in losses], dtype=float)
            deriv = 0.0
            for i in range(len(keeps)):
                deriv += float(np.prod(np.delete(keeps, i)))
            deriv_by_path[str(path_name)] = deriv
        vals = np.asarray(list(deriv_by_path.values()), dtype=float)
        out[mode] = {
            "path_derivative": deriv_by_path,
            "mean": float(vals.mean()),
            "sd": float(vals.std(ddof=0)),
            "range": [float(vals.min()), float(vals.max())],
            "cv": float(vals.std(ddof=0) / vals.mean()) if vals.mean() else None,
            "note": "uniform link-level loss shift leaks into path-level differential when path loss is nonlinear",
        }
    return out


def fixed_z_errs(tt: D.TruthTable, cv2: C.CostV2, cell: Mapping[str, Any], seeds: Sequence[int], n: int) -> Dict[str, float]:
    z_values = [float(z) for z in D.Z_GRID]
    max_k = max(int(round(z / D.DT)) for z in z_values)
    out = {D.z_key(z): [] for z in z_values}
    for seed in seeds:
        arrays = D._cell_arrays(tt, cv2, cell, seed=int(seed), n=int(n))
        for z in z_values:
            series = D._fixed_metric_series(arrays, z, max_k)
            out[D.z_key(z)].append(float(np.mean(series["err_total"])))
    return {key: float(np.mean(vals)) for key, vals in out.items()}


def evaluate_conclusions(
    tt: D.TruthTable,
    cv2: C.CostV2,
    cells: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n: int,
    baseline: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    per_cell: Dict[str, Dict[str, float]] = {}
    rankings: Dict[str, Tuple[str, ...]] = {}
    spearman_by_cell: Dict[str, Dict[str, float]] = {}
    for cell in cells:
        key = "%s@%.3f" % (cell["mode"], float(cell["rho_bar"]))
        per_cell[key] = cell_metrics(tt, cv2, cell, seeds, n)
        rankings[key] = path_ranking(tt, str(cell["mode"]), float(cell["rho_bar"]), float(cell["w_loss"]))
        err_by_z = fixed_z_errs(tt, cv2, cell, seeds, n)
        z_vals = [float(key_z) for key_z in sorted(err_by_z, key=float)]
        err_vals = [err_by_z[D.z_key(z)] for z in z_vals]
        rho = spearman_rho(z_vals, err_vals)
        spearman_by_cell[key] = {"rho": float(rho["rho"]), "n": int(rho["n"])}

    k1 = all(G1_LO <= metric["err_total"] <= G1_HI for metric in per_cell.values())
    k3 = all(row["rho"] > 0.0 for row in spearman_by_cell.values())

    if baseline is None:
        # Baseline defines the G2 set. Cells already below the floor are outside
        # that set, so they cannot be "flipped" by the residual band.
        k2 = True
        k4 = True
        k5 = True
    else:
        k2 = all(
            per_cell[key]["d_sla"] >= G2_FLOOR
            for key, metric in baseline["per_cell"].items()
            if metric["d_sla"] >= G2_FLOOR
        )
        k4 = all(rankings[key] == tuple(old) for key, old in baseline["rankings"].items())
        k5 = True
        for rho_key in {key.split("@", 1)[1] for key in per_cell}:
            p_key, h_key = "poisson@" + rho_key, "h2@" + rho_key
            if p_key in per_cell and h_key in per_cell:
                old_sign = np.sign(baseline["per_cell"][p_key]["err_total"] - baseline["per_cell"][h_key]["err_total"])
                new_sign = np.sign(per_cell[p_key]["err_total"] - per_cell[h_key]["err_total"])
                if new_sign != old_sign:
                    k5 = False

    return {
        "K1_err_in_g1_band": bool(k1),
        "K2_d_sla_floor": bool(k2),
        "K3_spearman_err_z_positive": bool(k3),
        "K4_path_ranking_preserved": bool(k4),
        "K5_family_order_preserved": bool(k5),
        "per_cell": per_cell,
        "rankings": {key: list(val) for key, val in rankings.items()},
        "spearman_err_z": spearman_by_cell,
    }


def all_hold(result: Mapping[str, Any]) -> bool:
    return all(bool(val) for key, val in result.items() if key.startswith("K"))


def broken_detail(flags: Mapping[str, Any], baseline: Mapping[str, Any]) -> Dict[str, Any]:
    detail: Dict[str, Any] = {}
    if not flags.get("K1_err_in_g1_band", True):
        detail["K1_err_in_g1_band"] = {
            key: {"err_total": float(metric["err_total"]), "g1": [G1_LO, G1_HI]}
            for key, metric in flags.get("per_cell", {}).items()
            if not (G1_LO <= float(metric["err_total"]) <= G1_HI)
        }
    if not flags.get("K2_d_sla_floor", True):
        detail["K2_d_sla_floor"] = {
            key: {
                "base_d_sla": float(baseline["per_cell"][key]["d_sla"]),
                "perturbed_d_sla": float(metric["d_sla"]),
                "floor": G2_FLOOR,
            }
            for key, metric in flags.get("per_cell", {}).items()
            if key in baseline.get("per_cell", {})
            and float(baseline["per_cell"][key]["d_sla"]) >= G2_FLOOR
            and float(metric["d_sla"]) < G2_FLOOR
        }
    if not flags.get("K3_spearman_err_z_positive", True):
        detail["K3_spearman_err_z_positive"] = {
            key: {"rho": float(row["rho"])}
            for key, row in flags.get("spearman_err_z", {}).items()
            if float(row["rho"]) <= 0.0
        }
    if not flags.get("K4_path_ranking_preserved", True):
        detail["K4_path_ranking_preserved"] = {
            key: {"base": list(base_rank), "pert": list(flags.get("rankings", {}).get(key, []))}
            for key, base_rank in baseline.get("rankings", {}).items()
            if list(flags.get("rankings", {}).get(key, [])) != list(base_rank)
        }
    if not flags.get("K5_family_order_preserved", True):
        out: Dict[str, Any] = {}
        for rho_key in {key.split("@", 1)[1] for key in flags.get("per_cell", {})}:
            p_key, h_key = "poisson@" + rho_key, "h2@" + rho_key
            if p_key not in flags.get("per_cell", {}) or h_key not in flags.get("per_cell", {}):
                continue
            old_sign = np.sign(
                baseline["per_cell"][p_key]["err_total"] - baseline["per_cell"][h_key]["err_total"]
            )
            new_sign = np.sign(
                flags["per_cell"][p_key]["err_total"] - flags["per_cell"][h_key]["err_total"]
            )
            if new_sign != old_sign:
                out["family@%s" % rho_key] = {
                    "base_sign": float(old_sign),
                    "pert_sign": float(new_sign),
                    "base": {
                        p_key: float(baseline["per_cell"][p_key]["err_total"]),
                        h_key: float(baseline["per_cell"][h_key]["err_total"]),
                    },
                    "pert": {
                        p_key: float(flags["per_cell"][p_key]["err_total"]),
                        h_key: float(flags["per_cell"][h_key]["err_total"]),
                    },
                }
        detail["K5_family_order_preserved"] = out
    return detail


def first_broken_cells(first_broken: Optional[Sequence[str]], detail: Mapping[str, Any]) -> List[str]:
    cells: List[str] = []
    for key in first_broken or []:
        value = detail.get(str(key), {})
        if isinstance(value, Mapping):
            for cell in value:
                if str(cell) not in cells:
                    cells.append(str(cell))
    return cells


def residual_to_link_shift(rec: RS.ResidualRecord, r: float) -> Tuple[float, float]:
    per_link = float(r) / N_LINKS_IN_PATH if rec.level == "per_path" else float(r)
    if rec.channel == "loss":
        return per_link, 0.0
    if rec.channel == "delay_ms":
        return 0.0, per_link
    raise ValueError("channel khong hop le: %s" % rec.channel)


def truth_table_for_endpoint(rec: RS.ResidualRecord, variant: str, endpoint: float) -> D.TruthTable:
    return truth_table_for(rec, variant, float(endpoint), sign=1.0)


def clip_summary(tables: Sequence[D.TruthTable]) -> Dict[str, Any]:
    clips = int(sum(int(getattr(tt, "clip_events", 0)) for tt in tables))
    evals = int(sum(int(getattr(tt, "eval_count", 0)) for tt in tables))
    ratio = float(clips / max(evals, 1))
    return {
        "clip_events": clips,
        "eval_count": evals,
        "clip_ratio": ratio,
        "band_is_lower_bound": bool(ratio > 0.01),
    }


def run_band(
    records: Sequence[RS.ResidualRecord],
    cv2: C.CostV2,
    tt0: D.TruthTable,
    cells: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n: int,
    variants: Sequence[str],
) -> List[Dict[str, Any]]:
    base = evaluate_conclusions(tt0, cv2, cells, seeds, n)
    rows = []
    print("=== BIEN SAI SO HE THONG (bom ca hai dau CI90) ===")
    hdr = "%-12s %-13s %-9s %8s %-20s %8s %-20s %8s %7s"
    print(hdr % ("cell", "variant", "kenh", "err", "bien d_err", "d_sla", "bien d_d_sla", "clip", "clip%"))
    for rec in records:
        per_link = link_residuals(rec)
        decomposition = decompose_residual(per_link) if per_link is not None else None
        if decomposition is not None:
            diff_over = decomposition["diff_over_cm"]
            print(
                "  decompose %-8s %-9s cm=%+.6g diff_rms=%.6g diff/cm=%s"
                % (
                    rec.mode,
                    rec.channel,
                    decomposition["common_mode"],
                    decomposition["diff_rms"],
                    "inf" if not np.isfinite(diff_over) else "%.3g" % diff_over,
                )
            )
        for cell in [item for item in cells if str(item["mode"]) == rec.mode]:
            key = "%s@%.3f" % (cell["mode"], float(cell["rho_bar"]))
            b = base["per_cell"][key]
            for variant in variants:
                if not variant_supported(rec, variant, records):
                    rows.append(
                        {
                            "cell": key,
                            "mode": rec.mode,
                            "channel": rec.channel,
                            "variant": variant,
                            "supported": False,
                            "reason": unsupported_reason(variant),
                        }
                    )
                    continue
                ends = []
                tables = []
                paired_endpoints = []
                for r in rec.ci90:
                    if variant == "joint":
                        tt = truth_table_for_variant(rec, variant, float(r), records=records, joint_scale_rule="qt1")
                    else:
                        tt = truth_table_for_endpoint(rec, variant, r)
                    tables.append(tt)
                    contrast = paired_metric_contrast(tt0, tt, cv2, cell, seeds, n)
                    d_sla_se = contrast["d_sla"]["se_paired"]
                    d_sla_z = abs(contrast["d_sla"]["d_d_sla"]) / max(d_sla_se, 1e-15)
                    paired_endpoints.append(
                        {
                            "r_endpoint": float(r),
                            **contrast["err"],
                            "d_d_sla": contrast["d_sla"]["d_d_sla"],
                            "d_sla_se_paired": d_sla_se,
                            "d_sla_se_iid": contrast["d_sla"]["se_iid"],
                            "d_sla_se_block": contrast["d_sla"]["se_block"],
                            "d_sla_ci90_block": contrast["d_sla"]["ci90_block"],
                            "d_sla_resolvable_block": contrast["d_sla"]["resolvable_block"],
                            "d_sla_inflation_factor": contrast["d_sla"]["inflation_factor"],
                            "d_sla_z": d_sla_z,
                            "d_sla_z_block": (
                                abs(contrast["d_sla"]["d_d_sla"]) / max(contrast["d_sla"]["se_block"], 1e-15)
                            ),
                            "d_sla_resolvable_iid": bool(d_sla_z > 1.96),
                            "d_sla_resolvable": bool(contrast["d_sla"]["resolvable_block"]),
                            "d_sla_se_method": "paired_sd_of_samplewise_d_sla_delta",
                            "d_sla_block_len": contrast["d_sla"]["block_len"],
                            "d_sla_n_blocks": contrast["d_sla"]["n_blocks"],
                            "base_d_sla": contrast["d_sla"]["base_d_sla"],
                            "perturbed_d_sla": contrast["d_sla"]["perturbed_d_sla"],
                        }
                    )
                    ends.append(
                        {
                            "err_total": contrast["err"]["perturbed_err"],
                            "d_sla": contrast["d_sla"]["perturbed_d_sla"],
                        }
                    )
                d_err = sorted(endpoint["d_err"] for endpoint in paired_endpoints)
                d_sla = sorted(endpoint["d_d_sla"] for endpoint in paired_endpoints)
                potency_endpoint = max(paired_endpoints, key=lambda endpoint: abs(endpoint["d_err"]))
                rms_worst = injection_rms(rec, variant, potency_endpoint["r_endpoint"])
                potency = abs(float(potency_endpoint["d_err"])) / max(rms_worst, 1e-15)
                clip = clip_summary(tables)
                identity = is_algebraic_identity_case(rec, variant)
                if identity:
                    se_mc = 0.0
                    mc_resolvable = None
                    p_min = None
                    se_unpaired = max(endpoint["se_unpaired_for_reference"] for endpoint in paired_endpoints)
                    worst_endpoint_resolvable = None
                    both_endpoints_resolvable = None
                else:
                    se_mc = max(endpoint["se_block"] for endpoint in paired_endpoints)
                    se_unpaired = max(endpoint["se_unpaired_for_reference"] for endpoint in paired_endpoints)
                    p_min = min(endpoint["p_mcnemar"] for endpoint in paired_endpoints)
                    worst_endpoint_resolvable = bool(any(endpoint["resolvable_block"] for endpoint in paired_endpoints))
                    both_endpoints_resolvable = bool(all(endpoint["resolvable_block"] for endpoint in paired_endpoints))
                    mc_resolvable = worst_endpoint_resolvable
                d_sla_z_max = max(endpoint["d_sla_z_block"] for endpoint in paired_endpoints)
                d_sla_resolvable = bool(any(endpoint["d_sla_resolvable_block"] for endpoint in paired_endpoints))
                equals_full_by_construction = bool(variant == "joint")
                print(
                    hdr
                    % (
                        key,
                        variant,
                        rec.channel,
                        "%.4f" % b["err_total"],
                        "[%+.4f, %+.4f]" % tuple(d_err),
                        "%.4f" % b["d_sla"],
                        "[%+.4f, %+.4f]" % tuple(d_sla),
                        "%d" % clip["clip_events"],
                        "%.2f" % (100.0 * clip["clip_ratio"]),
                    )
                )
                if clip["band_is_lower_bound"]:
                    print("  !! clip %.2f%% -> dau am la CAN DUOI, khong phai tac dong that" % (100.0 * clip["clip_ratio"]))
                if identity:
                    print("  == d_err la DONG NHAT THUC dai so, khong ap dung kiem dinh MC")
                elif not mc_resolvable:
                    print("  !! block bootstrap: chua phan biet duoc d_err voi 0 o n nay")
                else:
                    print(
                        "  block MC: D=[%d,%d] p_iid_min=%.3g -> co the phan biet d_err"
                        % (
                            min(endpoint["n_discordant"] for endpoint in paired_endpoints),
                            max(endpoint["n_discordant"] for endpoint in paired_endpoints),
                            p_min,
                        )
                    )
                rows.append(
                    {
                        "cell": key,
                        "mode": rec.mode,
                        "channel": rec.channel,
                        "variant": variant,
                        "supported": True,
                        "err": b["err_total"],
                        "d_err": d_err,
                        "d_sla": b["d_sla"],
                        "d_d_sla": d_sla,
                        "potency": potency,
                        "potency_endpoint": potency_endpoint["r_endpoint"],
                        "potency_abs_d_err": abs(float(potency_endpoint["d_err"])),
                        "potency_injection_rms": rms_worst,
                        "potency_rule": "max_abs_d_err_endpoint / rms_injected_residual_vector",
                        "se_monte_carlo": se_mc,
                        "se_monte_carlo_method": "algebraic_identity" if identity else "block_bootstrap_paired_signed_err",
                        "se_iid_mcnemar_max": max(endpoint["se_iid_mcnemar"] for endpoint in paired_endpoints),
                        "se_block_max": max(endpoint["se_block"] for endpoint in paired_endpoints),
                        "ci90_block_by_endpoint": [
                            endpoint["ci90_block"] for endpoint in paired_endpoints
                        ],
                        "block_inflation_factor_max": max(
                            [
                                endpoint["inflation_factor"]
                                for endpoint in paired_endpoints
                                if endpoint["inflation_factor"] is not None
                            ]
                            or [None]
                        ),
                        "block_len": paired_endpoints[0]["block_len"],
                        "block_len_requested": paired_endpoints[0]["block_len_requested"],
                        "block_len_truncated": any(endpoint["block_len_truncated"] for endpoint in paired_endpoints),
                        "n_blocks": min(endpoint["n_blocks"] for endpoint in paired_endpoints),
                        "se_unpaired_for_reference": se_unpaired,
                        "p_mcnemar_min": p_min,
                        "mc_resolvable": mc_resolvable,
                        "worst_endpoint_resolvable": worst_endpoint_resolvable,
                        "both_endpoints_resolvable": both_endpoints_resolvable,
                        "resolvability_rule": (
                            "worst-endpoint: band row is resolvable if at least one CI endpoint "
                            "is distinguishable from zero; the other endpoint may remain within MC noise"
                        ),
                        "is_algebraic_identity": identity,
                        "d_sla_resolvable": d_sla_resolvable,
                        "d_sla_z_max": d_sla_z_max,
                        "d_sla_se_method": "block_bootstrap_paired_samplewise_d_sla_delta",
                        "d_sla_se_iid_max": max(endpoint["d_sla_se_iid"] for endpoint in paired_endpoints),
                        "d_sla_se_block_max": max(endpoint["d_sla_se_block"] for endpoint in paired_endpoints),
                        "d_sla_ci90_block_by_endpoint": [
                            endpoint["d_sla_ci90_block"] for endpoint in paired_endpoints
                        ],
                        "d_sla_inflation_factor_max": max(
                            [
                                endpoint["d_sla_inflation_factor"]
                                for endpoint in paired_endpoints
                                if endpoint["d_sla_inflation_factor"] is not None
                            ]
                            or [None]
                        ),
                        "equals_full_by_construction": equals_full_by_construction,
                        "paired_err_endpoints": paired_endpoints,
                        "n_discordant_range": [
                            min(endpoint["n_discordant"] for endpoint in paired_endpoints),
                            max(endpoint["n_discordant"] for endpoint in paired_endpoints),
                        ],
                        "b_range": [
                            min(endpoint["b"] for endpoint in paired_endpoints),
                            max(endpoint["b"] for endpoint in paired_endpoints),
                        ],
                        "c_range": [
                            min(endpoint["c"] for endpoint in paired_endpoints),
                            max(endpoint["c"] for endpoint in paired_endpoints),
                        ],
                        "n_total": paired_endpoints[0]["n_total"],
                        **clip,
                        "residual_decomposition": decomposition,
                    }
                )
                if identity:
                    rows[-1]["note_identity"] = (
                        "d_err = 0 la DONG NHAT THUC: moi duong co cung so chang, "
                        "common-mode delay dich moi duong cung mot hang so nen argmin bat bien."
                    )
                elif not mc_resolvable:
                    rows[-1]["note_mc"] = (
                        "d_err chua phan biet duoc voi 0 theo block bootstrap ghep cap; "
                        "tang n hoac tang so seed"
                    )
    return rows


def _scan_r_max(rec: RS.ResidualRecord, requested: Optional[float]) -> float:
    ci_max = max(abs(x) for x in rec.ci90)
    base = float(requested) if requested is not None else float(R_MAX_DEFAULT[rec.channel])
    return max(base, 10.0 * ci_max)


def _scan_axis(variant: str) -> str:
    return "lambda_ci90_multiple" if str(variant) == "joint" else "residual_native_unit"


def _scan_r_max_for_variant(rec: RS.ResidualRecord, variant: str, requested: Optional[float]) -> float:
    if str(variant) == "joint":
        return float(JOINT_LAMBDA_R_MAX_DEFAULT if requested is None else requested)
    return _scan_r_max(rec, requested)


def _flags_for_variant(
    rec: RS.ResidualRecord,
    variant: str,
    magnitude: float,
    sign: float,
    cv2: C.CostV2,
    cells: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n: int,
    baseline: Mapping[str, Any],
    records: Optional[Sequence[RS.ResidualRecord]] = None,
) -> Dict[str, Any]:
    tt = truth_table_for_variant(rec, variant, float(magnitude), sign=float(sign), records=records)
    return evaluate_conclusions(tt, cv2, cells, seeds, n, baseline=baseline)


def variant_holds(
    rec: RS.ResidualRecord,
    variant: str,
    magnitude: float,
    cv2: C.CostV2,
    cells: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n: int,
    baseline: Mapping[str, Any],
    records: Optional[Sequence[RS.ResidualRecord]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    for sign in (+1.0, -1.0):
        flags = _flags_for_variant(rec, variant, magnitude, sign, cv2, cells, seeds, n, baseline, records=records)
        if not all_hold(flags):
            return False, flags
    return True, None


def evaluate_k4_only(
    tt: D.TruthTable,
    cells: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
) -> Dict[str, Any]:
    rankings: Dict[str, Tuple[str, ...]] = {}
    for cell in cells:
        key = "%s@%.3f" % (cell["mode"], float(cell["rho_bar"]))
        rankings[key] = path_ranking(tt, str(cell["mode"]), float(cell["rho_bar"]), float(cell["w_loss"]))
    k4 = all(rankings[key] == tuple(old) for key, old in baseline["rankings"].items())
    return {
        "K4_path_ranking_preserved": bool(k4),
        "rankings": {key: list(val) for key, val in rankings.items()},
    }


def _k4_flags_for_variant(
    rec: RS.ResidualRecord,
    variant: str,
    magnitude: float,
    sign: float,
    cells: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
    records: Optional[Sequence[RS.ResidualRecord]] = None,
) -> Dict[str, Any]:
    tt = truth_table_for_variant(rec, variant, float(magnitude), sign=float(sign), records=records)
    return evaluate_k4_only(tt, cells, baseline)


def variant_k4_holds(
    rec: RS.ResidualRecord,
    variant: str,
    magnitude: float,
    cells: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
    records: Optional[Sequence[RS.ResidualRecord]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    for sign in (+1.0, -1.0):
        flags = _k4_flags_for_variant(rec, variant, magnitude, sign, cells, baseline, records=records)
        if not flags["K4_path_ranking_preserved"]:
            return False, flags
    return True, None


def scan_k4_threshold(
    rec: RS.ResidualRecord,
    variant: str,
    cells: Sequence[Mapping[str, Any]],
    baseline: Mapping[str, Any],
    records: Optional[Sequence[RS.ResidualRecord]],
    r_max: float,
    n_steps: int,
    tol: float,
) -> Dict[str, Any]:
    ci_max = max(abs(x) for x in rec.ci90)
    grid = np.linspace(0.0, float(r_max), int(n_steps) + 1)[1:]
    zero_holds, zero_flags = variant_k4_holds(rec, variant, 0.0, cells, baseline, records=records)
    if not zero_holds:
        first = ["K4_path_ranking_preserved"]
        detail = broken_detail(zero_flags or {}, baseline)
        return {
            "method": "deterministic_path_ranking",
            "n_dependence": "none",
            "baseline_broken": True,
            "r_star": None,
            "r_star_bracket": None,
            "safety_factor": None,
            "first_broken": first,
            "first_broken_cell": first_broken_cells(first, detail),
            "first_broken_detail": detail,
        }

    last_good = 0.0
    for r in grid:
        holds, _flags = variant_k4_holds(rec, variant, float(r), cells, baseline, records=records)
        if holds:
            last_good = float(r)
            continue
        eval_fn = lambda x, rec=rec, variant=variant: variant_k4_holds(
            rec, variant, float(x), cells, baseline, records=records
        )[0]
        bracket = refine_r_star(eval_fn, last_good, float(r), tol=tol)
        r_star = float(bracket["r_star"])
        refined_flags = variant_k4_holds(rec, variant, r_star, cells, baseline, records=records)[1]
        first = ["K4_path_ranking_preserved"]
        detail = broken_detail(refined_flags or {}, baseline)
        return {
            "method": "deterministic_path_ranking",
            "n_dependence": "none",
            "baseline_broken": False,
            "r_star": r_star,
            "r_star_bracket": bracket,
            "safety_factor": {
                "bound": "bracket",
                "lo": float(bracket["r_star_lo"] if variant == "joint" else bracket["r_star_lo"] / max(ci_max, 1e-12)),
                "hi": float(bracket["r_star_hi"] if variant == "joint" else bracket["r_star_hi"] / max(ci_max, 1e-12)),
            },
            "first_broken": first,
            "first_broken_cell": first_broken_cells(first, detail),
            "first_broken_detail": detail,
        }

    safety_value = float(r_max if variant == "joint" else float(r_max) / max(ci_max, 1e-12))
    return {
        "method": "deterministic_path_ranking",
        "n_dependence": "none",
        "baseline_broken": False,
        "r_star": None,
        "r_star_bracket": None,
        "safety_factor": {"bound": "lower", "value": safety_value},
        "first_broken": None,
        "first_broken_cell": [],
        "first_broken_detail": {},
    }


def refine_r_star(eval_fn, r_lo: float, r_hi: float, tol: float = 1e-4, max_iter: int = 20) -> Dict[str, float]:
    if not eval_fn(r_lo):
        raise AssertionError("r_lo phai con DUNG -- luoi tho sai")
    if eval_fn(r_hi):
        raise AssertionError("r_hi phai da GAY -- luoi tho sai")
    lo, hi = float(r_lo), float(r_hi)
    for _ in range(int(max_iter)):
        if (hi - lo) <= float(tol):
            break
        mid = 0.5 * (lo + hi)
        if eval_fn(mid):
            lo = mid
        else:
            hi = mid
    return {"r_star_lo": lo, "r_star_hi": hi, "r_star": hi, "bracket_width": hi - lo}


def summarize_published_safety(scans: Sequence[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the conservative min-over-variants safety summary."""
    candidates = []
    for scan in scans:
        if not scan.get("supported", True):
            continue
        if scan.get("baseline_broken"):
            candidates.append(
                {
                    "mode": scan.get("mode"),
                    "channel": scan.get("channel"),
                    "variant": scan.get("variant"),
                    "bound": "baseline_broken",
                    "value": 0.0,
                    "first_broken": scan.get("first_broken"),
                    "first_broken_cell": scan.get("first_broken_cell"),
                    "scan_axis": scan.get("scan_axis"),
                }
            )
            continue
        safety = scan.get("safety_factor")
        if not safety:
            continue
        if safety.get("bound") == "bracket":
            candidates.append(
                {
                    "mode": scan.get("mode"),
                    "channel": scan.get("channel"),
                    "variant": scan.get("variant"),
                    "bound": "bracket_lo",
                    "value": float(safety["lo"]),
                    "hi": float(safety["hi"]),
                    "first_broken": scan.get("first_broken"),
                    "first_broken_cell": scan.get("first_broken_cell"),
                    "scan_axis": scan.get("scan_axis"),
                }
            )
        elif safety.get("bound") == "lower":
            candidates.append(
                {
                    "mode": scan.get("mode"),
                    "channel": scan.get("channel"),
                    "variant": scan.get("variant"),
                    "bound": "lower",
                    "value": float(safety["value"]),
                    "first_broken": scan.get("first_broken"),
                    "first_broken_cell": scan.get("first_broken_cell"),
                    "scan_axis": scan.get("scan_axis"),
                }
            )
    if not candidates:
        return None
    binding = min(candidates, key=lambda row: row["value"])
    return {
        "rule": "min over supported variants; bracket rows use conservative lo; joint uses QT-3 lambda directly",
        "value": float(binding["value"]),
        "binding": binding,
        "candidates": candidates,
    }


def run_scan(
    records: Sequence[RS.ResidualRecord],
    cv2: C.CostV2,
    tt0: D.TruthTable,
    cells: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n: int,
    r_max: Optional[float],
    n_steps: int,
    variants: Sequence[str],
    tol: float,
) -> Dict[str, Any]:
    base = evaluate_conclusions(tt0, cv2, cells, seeds, n)
    out: Dict[str, Any] = {
        "baseline": base,
        "scans": [],
        "scan_split_policy": {
            "K4_path_ranking_preserved": "deterministic_path_ranking_no_seed_no_n",
            "K1_K2_K3_K5": "monte_carlo_at_requested_n",
        },
    }
    if not all_hold(base):
        print("WARNING: baseline da co ket luan khong giu; scan van chay de chan doan.")

    for rec in records:
        ci_max = max(abs(x) for x in rec.ci90)
        for variant in variants:
            effective_r_max = _scan_r_max_for_variant(rec, variant, r_max)
            grid = np.linspace(0.0, effective_r_max, int(n_steps) + 1)[1:]
            scan_axis = _scan_axis(variant)
            print()
            print("=== QUET NGUONG GAY -- %s / %s / %s ===" % (rec.mode, rec.channel, variant))
            if not variant_supported(rec, variant, records):
                print("  BO QUA: %s" % unsupported_reason(variant))
                out["scans"].append(
                    {
                        "mode": rec.mode,
                        "channel": rec.channel,
                        "variant": variant,
                        "supported": False,
                        "reason": unsupported_reason(variant),
                    }
                )
                continue

            k4_deterministic = scan_k4_threshold(
                rec,
                variant,
                cells,
                base,
                records,
                effective_r_max,
                n_steps,
                tol,
            )
            r_star: Optional[float] = None
            bracket: Optional[Dict[str, float]] = None
            first_broken: Optional[List[str]] = None
            first_broken_detail: Dict[str, Any] = {}
            first_broken_cell: List[str] = []
            trace = []
            last_good = 0.0
            print("  %10s | %-5s %-5s %-5s %-5s %-5s | %s" % ("r'", "K1", "K2", "K3", "K4", "K5", "trang thai"))
            zero_holds, zero_flags = variant_holds(rec, variant, 0.0, cv2, cells, seeds, n, base, records=records)
            if not zero_holds:
                first_broken = [
                    key for key, val in (zero_flags or {}).items() if key.startswith("K") and not val
                ]
                detail = broken_detail(zero_flags or {}, base)
                cells_broken = first_broken_cells(first_broken, detail)
                print("  %10.6f | %-5s %-5s %-5s %-5s %-5s | BASELINE GAY" % (
                    0.0,
                    zero_flags["K1_err_in_g1_band"],
                    zero_flags["K2_d_sla_floor"],
                    zero_flags["K3_spearman_err_z_positive"],
                    zero_flags["K4_path_ranking_preserved"],
                    zero_flags["K5_family_order_preserved"],
                ))
                out["scans"].append(
                    {
                        "mode": rec.mode,
                        "channel": rec.channel,
                        "variant": variant,
                        "supported": True,
                        "scan_axis": scan_axis,
                        "k4_deterministic": k4_deterministic,
                        "baseline_broken": True,
                        "first_broken": first_broken,
                        "first_broken_cell": cells_broken,
                        "first_broken_detail": detail,
                        "r_point": rec.point,
                        "r_ci90": rec.ci90,
                        "r_max": effective_r_max,
                        "r_star": None,
                        "r_star_bracket": None,
                        "safety_factor": None,
                        "trace": [{"r": 0.0, **{key: val for key, val in (zero_flags or {}).items() if key.startswith("K")}, "holds": False}],
                        "residual_decomposition": decompose_residual(link_residuals(rec)) if link_residuals(rec) else None,
                    }
                )
                continue
            for r in grid:
                holds, broken = variant_holds(rec, variant, float(r), cv2, cells, seeds, n, base, records=records)
                flags = broken or _flags_for_variant(rec, variant, 0.0, 1.0, cv2, cells, seeds, n, base, records=records)
                print(
                    "  %10.6f | %-5s %-5s %-5s %-5s %-5s | %s"
                    % (
                        r,
                        flags["K1_err_in_g1_band"],
                        flags["K2_d_sla_floor"],
                        flags["K3_spearman_err_z_positive"],
                        flags["K4_path_ranking_preserved"],
                        flags["K5_family_order_preserved"],
                        "OK" if holds else "*** GAY ***",
                    )
                )
                trace.append({"r": float(r), **{key: val for key, val in flags.items() if key.startswith("K")}, "holds": bool(holds)})
                if holds:
                    last_good = float(r)
                    continue

                eval_fn = lambda x, rec=rec, variant=variant: variant_holds(
                    rec, variant, float(x), cv2, cells, seeds, n, base, records=records
                )[0]
                bracket = refine_r_star(eval_fn, last_good, float(r), tol=tol)
                r_star = float(bracket["r_star"])
                refined_flags = variant_holds(rec, variant, r_star, cv2, cells, seeds, n, base, records=records)[1]
                first_broken = [
                    key for key, val in (refined_flags or flags).items() if key.startswith("K") and not val
                ]
                first_broken_detail = broken_detail(refined_flags or flags, base)
                first_broken_cell = first_broken_cells(first_broken, first_broken_detail)
                break

            print("  ---")
            print("  r do duoc        = %+.6f   CI90 = [%+.6f, %+.6f]" % (rec.point, *rec.ci90))
            print("  r_max da quet    = %.6f" % effective_r_max)
            if r_star is None:
                safety_value = float(effective_r_max if variant == "joint" else effective_r_max / max(ci_max, 1e-12))
                safety = {"bound": "lower", "value": safety_value}
                print("  r* nguong gay    = > %.6f" % effective_r_max)
                print("  ket luan gay     = khong co")
                print("  HE SO AN TOAN    = > %.2f (CAN DUOI)" % safety_value)
            else:
                safety = {
                    "bound": "bracket",
                    "lo": float(bracket["r_star_lo"] if variant == "joint" else bracket["r_star_lo"] / max(ci_max, 1e-12)),
                    "hi": float(bracket["r_star_hi"] if variant == "joint" else bracket["r_star_hi"] / max(ci_max, 1e-12)),
                }
                print(
                    "  r* nguong gay    = [%.6f, %.6f]  width=%.6f"
                    % (bracket["r_star_lo"], bracket["r_star_hi"], bracket["bracket_width"])
                )
                print("  ket luan gay     = %s" % (first_broken or "khong ro"))
                print("  HE SO AN TOAN    = [%.2f, %.2f]" % (safety["lo"], safety["hi"]))

            out["scans"].append(
                {
                    "mode": rec.mode,
                    "channel": rec.channel,
                    "variant": variant,
                    "supported": True,
                    "scan_axis": scan_axis,
                    "k4_deterministic": k4_deterministic,
                    "r_point": rec.point,
                    "r_ci90": rec.ci90,
                    "r_max": effective_r_max,
                    "r_star": r_star,
                    "r_star_bracket": bracket,
                    "first_broken": first_broken,
                    "first_broken_cell": first_broken_cell,
                    "first_broken_detail": first_broken_detail,
                    "safety_factor": safety,
                    "trace": trace,
                    "residual_decomposition": decompose_residual(link_residuals(rec)) if link_residuals(rec) else None,
                }
            )
    out["safety_published"] = summarize_published_safety(out["scans"])
    if out["safety_published"] is not None:
        binding = out["safety_published"]["binding"]
        print()
        print(
            "=== SAFETY CONG BO (min qua bien the) = %.3f tai %s/%s/%s ==="
            % (
                out["safety_published"]["value"],
                binding.get("mode"),
                binding.get("channel"),
                binding.get("variant"),
            )
        )
    return out


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def independent_variants(kind: str, variants: Sequence[str]) -> List[str]:
    seen = set()
    out = []
    for variant in variants:
        canonical = "full" if str(kind) == "band" and str(variant) == "joint" else str(variant)
        if canonical in seen:
            continue
        seen.add(canonical)
        out.append(canonical)
    return out


def build_report(
    kind: str,
    payload: Mapping[str, Any],
    residual_path: str,
    seeds: Sequence[int],
    n: int,
    rho_bar_filter: Optional[float],
    variants: Sequence[str],
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "kind": str(kind),
        "phase": "20R.6-v2",
        "schema": "band_v2/v1",
        "seeds": [int(seed) for seed in seeds],
        "n": int(n),
        "rho_bar_filter": None if rho_bar_filter is None else float(rho_bar_filter),
        "residual_file": str(residual_path),
        "residual_sha256": sha256_of_file(residual_path),
        "truth_table": D.TRUTH_TABLE,
        "truth_table_sha256": sha256_of_file(D.TRUTH_TABLE),
        "calibration": D.CALIBRATION,
        "calibration_sha256": sha256_of_file(D.CALIBRATION),
        "wall_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "is_smoke": bool(int(n) < 50_000),
        "variants": [str(variant) for variant in variants],
        "variant_universe": list(VARIANTS),
        "independent_variants": independent_variants(kind, variants),
        "n_independent_variants": len(independent_variants(kind, variants)),
        "joint_scaling_rule": (
            "QT-3 for scan: joint coordinate is dimensionless lambda; lambda=1 "
            "perturbs every same-channel mode by its own worst CI90 endpoint. "
            "Band rows canonicalize joint to full for per-cell metrics."
        ),
        "band_joint_identity": (
            "In band reports, joint is identical to full by construction for per-cell metrics; "
            "joint only has independent meaning in scan conclusions that include inter-mode K5"
        ),
    }
    report.update(RS.git_commit())
    report.update(dict(payload))
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--residual", required=True, help="residual_spec/v1 JSON")
    ap.add_argument("--mode", choices=["band", "scan"], default="band")
    ap.add_argument("--seeds", default="101,102,103,104,105")
    ap.add_argument("--n", type=int, default=120_000)
    ap.add_argument("--rho-bar", type=float, default=None)
    ap.add_argument("--r-max", type=float, default=None, help="override scan max; default is per-channel and at least 10x CI90")
    ap.add_argument("--n-steps", type=int, default=25)
    ap.add_argument("--r-star-tol", type=float, default=1e-4)
    ap.add_argument("--variants", default=",".join(DEFAULT_VARIANTS))
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)

    seeds = [int(part) for part in args.seeds.split(",") if part.strip()]
    variants = [part.strip() for part in args.variants.split(",") if part.strip()]
    unknown = sorted(set(variants) - set(VARIANTS))
    if unknown:
        raise ValueError("unknown variants: %s" % unknown)
    records = RS.load(args.residual)
    cv2 = C.CostV2()
    tt0 = D.TruthTable()
    cells = [cell for cell in D.feasible_cells(D.CALIBRATION, include_pc1=True) if str(cell["mode"]) != "cbr"]
    if args.rho_bar is not None:
        cells = [cell for cell in cells if abs(float(cell["rho_bar"]) - float(args.rho_bar)) < 1e-9]
    if not cells:
        raise ValueError("khong co o nao thoa dieu kien -- kiem tra --rho-bar")

    print("=== PHAN DU DAU VAO ===")
    for rec in records:
        print("  [%s/%s/%s] %s" % (rec.source, rec.mode, rec.channel, rec.estimand[:70] + "..."))
        print(
            "      r = %+.6f  se = %.6f  CI90 = [%+.6f, %+.6f]  I2 = %s"
            % (
                rec.point,
                rec.se,
                *rec.ci90,
                "n/a" if rec.i_squared is None else "%.0f%%" % (100.0 * rec.i_squared),
            )
        )
    print()

    if args.mode == "band":
        rows = run_band(records, cv2, tt0, cells, seeds, args.n, variants)
        result = build_report(
            "band",
            {
                "rows": rows,
                "potency_ratio_diff_over_cm": potency_summary(rows),
                "loss_common_mode_leakage": loss_common_mode_leakage(
                    tt0,
                    [str(cell["mode"]) for cell in cells],
                    float(args.rho_bar if args.rho_bar is not None else cells[0]["rho_bar"]),
                ),
            },
            args.residual,
            seeds,
            args.n,
            args.rho_bar,
            variants,
        )
        default_out = "results/phase-20R/band_v2_cascade.json"
    else:
        result = build_report(
            "scan",
            run_scan(records, cv2, tt0, cells, seeds, args.n, args.r_max, args.n_steps, variants, args.r_star_tol),
            args.residual,
            seeds,
            args.n,
            args.rho_bar,
            variants,
        )
        default_out = "results/phase-20R/breakdown_scan.json"

    out = args.out or default_out
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, default=str)
        f.write("\n")
    print()
    print("-> %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
