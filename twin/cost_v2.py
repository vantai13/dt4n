#!/usr/bin/env python3
"""Phase 20R -- bang cost end-to-end tren link_model_v2 (do that).

Thay the build_cost_tables() cua Phase 20. Ly do thay, theo audit Phase L:
  A2  link_model v1 gan do doc gia: d(delay)/d(rho) = base_delay_ms.
      Do doc la thu quyet dinh argmin, nen sai do doc = sai quyet dinh.
  L1  Mininet KHONG tinh phi serialization o chieu do -> phai cong giai tich.
  --  v1 khong co khai niem traffic family; link_model_v2 bat buoc co `mode`.

Hop dong delay ba thanh phan:

    total_delay_ms = base_delay_ms
                   + frame_bytes * 8 / bw_bps * 1000
                   + link_model_v2.predict_delay(mode, bw, q, rho)
"""

from __future__ import annotations

import argparse
import math
from typing import Dict, Sequence, Tuple

import numpy as np

from twin import topology_v7 as T7
from twin.link_model import loss_rate as v1_loss_rate
from twin.link_model import total_delay_ms as v1_total_delay_ms
from twin.link_model_v2 import LinkModelV2


FRAME_BYTES = 1512
FIT_PATH = "results/LIVE/phase-L/link_model_v2_fit.json"
RHO_MIN, RHO_MAX = 0.50, 1.05
GRID_STEP = 0.0005
Z_FEASIBLE = 2.58
RELIABLE_CEILING = {"cbr": 0.95, "poisson": RHO_MAX, "h2": RHO_MAX}

_MEAN_LOAD = sum(T7.LOAD_MEAN.values()) / len(T7.LOAD_MEAN)
LINK_OFFSET: Dict[str, float] = {
    link: float(T7.LOAD_MEAN[link]) - _MEAN_LOAD
    for link in T7.LINK_NAMES
}


def serialization_ms(bw_mbps: float, frame_bytes: int = FRAME_BYTES) -> float:
    """Thoi gian day mot frame ra day. Mininet khong tinh phi nay (L1)."""
    return float(frame_bytes) * 8.0 / (float(bw_mbps) * 1e6) * 1000.0


def static_link_ms(link: str) -> float:
    """Phan delay cua mot link khong phu thuoc rho: base + serialization."""
    bw, base, _q = T7.LINKS[link]
    return float(base) + serialization_ms(bw)


def static_path_ms(path: str) -> float:
    """Phan delay cua mot duong khong phu thuoc rho."""
    return sum(static_link_ms(link) for link in T7.PATHS[path])


def rho_vector(rho_bar: float) -> Dict[str, float]:
    """Q7: mot rho_bar -> tam rho, mot gia tri cho moi link."""
    return {
        link: float(np.clip(float(rho_bar) + LINK_OFFSET[link], RHO_MIN, RHO_MAX))
        for link in T7.LINK_NAMES
    }


def clip_fraction(rho_bar: float, sigma: float = 0.010) -> Dict[str, float]:
    """Ti le mau bi ep ve bien, gia dinh rho_link ~ N(rho_bar + offset, sigma)."""

    def phi(x: float) -> float:
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    out = {}
    for link in T7.LINK_NAMES:
        mu = float(rho_bar) + LINK_OFFSET[link]
        out[link] = (1.0 - phi((RHO_MAX - mu) / float(sigma))) + phi(
            (RHO_MIN - mu) / float(sigma)
        )
    return out


def sigma_max_regime(mode: str, rho_bar: float, z: float = Z_FEASIBLE) -> float:
    """Bien do lon nhat cho phep o mot o (mode, rho_bar).

    Khac ``mininet.rho_spec.sigma_max_feasible`` o hai diem:
    (1) tinh tren rho tung link sau offset Q7;
    (2) tran la tran do tin cay cua traffic family.
    """
    if mode not in RELIABLE_CEILING:
        raise ValueError("unknown mode %r; expected one of %s" % (mode, sorted(RELIABLE_CEILING)))
    ceil_hi = RELIABLE_CEILING[mode]
    head_hi = min(float(ceil_hi) - (float(rho_bar) + LINK_OFFSET[ln]) for ln in T7.LINK_NAMES)
    head_lo = min((float(rho_bar) + LINK_OFFSET[ln]) - RHO_MIN for ln in T7.LINK_NAMES)
    return max(0.0, min(head_hi, head_lo) / float(z))


def sigma_from_a_regime(mode: str, rho_bar: float, a: float) -> float:
    """Phase T design axis: sigma = a * sigma_max, but now per regime."""
    return float(a) * sigma_max_regime(mode, rho_bar)


class CostV2:
    """Bang cost end-to-end. Moi lesson sau deu goi qua lop nay."""

    def __init__(self, fit_path: str = FIT_PATH, strict_reliable: bool = True):
        self.m = LinkModelV2.load(fit_path)
        self.strict_reliable = bool(strict_reliable)
        self._cache: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    def link_delay_ms(self, mode: str, link: str, rho: float) -> float:
        bw, base, q = T7.LINKS[link]
        if self.strict_reliable and not self.m.is_reliable(mode, bw, q, rho):
            raise ValueError(
                "unreliable region: mode=%s bw=%s q=%s rho=%.4f "
                "(link_model_v2 danh dau vung nay khong tin cay)"
                % (mode, bw, q, float(rho))
            )
        return float(base) + serialization_ms(bw) + self.m.predict_delay(mode, bw, q, rho)

    def link_loss(self, mode: str, link: str, rho: float) -> float:
        bw, _base, q = T7.LINKS[link]
        if self.strict_reliable and not self.m.is_reliable(mode, bw, q, rho):
            raise ValueError(
                "unreliable region: mode=%s bw=%s q=%s rho=%.4f "
                "(link_model_v2 danh dau vung nay khong tin cay)"
                % (mode, bw, q, float(rho))
            )
        return float(self.m.predict_loss(mode, bw, q, rho))

    def tables(self, rho: Dict[str, float], mode: str, w_loss: float):
        """Return ``(delay[K], loss[K], cost[K])`` cho mot trang thai."""
        delay = np.zeros(T7.K, dtype=float)
        keep = np.ones(T7.K, dtype=float)
        for action, path in enumerate(T7.PATH_NAMES):
            for link in T7.PATHS[path]:
                delay[action] += self.link_delay_ms(mode, link, rho[link])
                keep[action] *= 1.0 - self.link_loss(mode, link, rho[link])
        loss = 1.0 - keep
        return delay, loss, delay + float(w_loss) * loss

    @staticmethod
    def _grid() -> np.ndarray:
        n = int(round((RHO_MAX - RHO_MIN) / GRID_STEP)) + 1
        return np.linspace(RHO_MIN, RHO_MAX, n)

    def _link_curves(self, mode: str, link: str):
        """Cache duong cong delay/loss tren luoi rho min, mot lan moi link."""
        key = "%s|%s" % (mode, link)
        if key not in self._cache:
            bw, base, q = T7.LINKS[link]
            grid = self._grid()
            delay = np.array(
                [
                    float(base)
                    + serialization_ms(bw)
                    + self.m.predict_delay(mode, bw, q, float(r))
                    for r in grid
                ],
                dtype=float,
            )
            loss = np.array(
                [self.m.predict_loss(mode, bw, q, float(r)) for r in grid],
                dtype=float,
            )
            self._cache[key] = (delay, loss)
        return self._cache[key]

    def tables_batch(self, rho_mat: np.ndarray, mode: str, w_loss: float):
        """Return ``(delay[n,K], loss[n,K], cost[n,K])`` for many states."""
        rho_mat = np.asarray(rho_mat, dtype=float)
        if rho_mat.ndim != 2 or rho_mat.shape[1] != len(T7.LINK_NAMES):
            raise ValueError("rho_mat phai co shape (n, %d)" % len(T7.LINK_NAMES))
        if rho_mat.size and (
            float(rho_mat.min()) < RHO_MIN - 1e-12
            or float(rho_mat.max()) > RHO_MAX + 1e-12
        ):
            raise ValueError("rho ngoai mien do [%.2f, %.2f]" % (RHO_MIN, RHO_MAX))
        if self.strict_reliable:
            self._assert_reliable_batch(rho_mat, mode)

        idx_of = {link: i for i, link in enumerate(T7.LINK_NAMES)}
        grid = self._grid()
        n = rho_mat.shape[0]
        delay = np.zeros((n, T7.K), dtype=float)
        keep = np.ones((n, T7.K), dtype=float)
        for action, path in enumerate(T7.PATH_NAMES):
            for link in T7.PATHS[path]:
                r = rho_mat[:, idx_of[link]]
                d_curve, l_curve = self._link_curves(mode, link)
                delay[:, action] += np.interp(r, grid, d_curve)
                keep[:, action] *= 1.0 - np.interp(r, grid, l_curve)
        loss = 1.0 - keep
        return delay, loss, delay + float(w_loss) * loss

    def _assert_reliable_batch(self, rho_mat: np.ndarray, mode: str) -> None:
        for i, link in enumerate(T7.LINK_NAMES):
            bw, _base, q = T7.LINKS[link]
            self.m.domain(mode, bw, q)  # validates that the curve exists
            col = rho_mat[:, i]
            if col.size == 0:
                continue
            if mode == "cbr" and bool(np.any((0.95 < col) & (col < 1.05))):
                bad = float(col[(0.95 < col) & (col < 1.05)][0])
                raise ValueError(
                    "unreliable region trong batch: mode=%s link=%s rho=%.4f"
                    % (mode, link, bad)
                )


def _v2_link(model: CostV2, mode: str, link: str, rho: float) -> Tuple[float, float]:
    return model.link_delay_ms(mode, link, rho), model.link_loss(mode, link, rho)


def _path_from_link_fn(link_fn, path: str, w_loss: float) -> Tuple[float, float, float]:
    delay = 0.0
    keep = 1.0
    for link in T7.PATHS[path]:
        d, loss = link_fn(link)
        delay += d
        keep *= 1.0 - loss
    loss = 1.0 - keep
    return delay, loss, delay + float(w_loss) * loss


def audit_v1_vs_v2(mode: str = "poisson", w_loss: float = 2500.0) -> str:
    """Return the short audit printed by ``python3 -m twin.cost_v2 --audit``."""
    cv2 = CostV2(strict_reliable=False)
    lines = [
        "BANG 1 -- lech theo link tai LOAD_MEAN (mode=%s)" % mode,
        "link  bw  q   rho   | v1_delay v1_loss | v2_delay v2_loss | v2/v1",
    ]
    for link in T7.LINK_NAMES:
        bw, base, q = T7.LINKS[link]
        rho = float(T7.LOAD_MEAN[link])
        d1 = v1_total_delay_ms(base, rho, bw_mbps=bw, queue_pkts=q)
        l1 = v1_loss_rate(rho)
        d2, l2 = _v2_link(cv2, mode, link, rho)
        lines.append(
            "%-4s %2.0f %2d %.3f | %8.3f %.5f | %8.3f %.5f | %.2fx"
            % (link, bw, q, rho, d1, l1, d2, l2, d2 / d1)
        )
    lines.extend(["", "PHAN TINH (base + serialization), khong phu thuoc rho:"])
    lines.append(
        "  " + "    ".join("%s = %.3f ms" % (path, static_path_ms(path)) for path in T7.PATH_NAMES)
    )
    lines.extend(["", "Ti le clip tai tran 1.05 (sigma = 0.010):"])
    for rho_bar in (0.925, 0.960, 0.980):
        clips = clip_fraction(rho_bar, sigma=0.010)
        worst = max(clips, key=clips.get)
        lines.append(
            "  rho_bar=%.3f  link te nhat=%-4s p_clip=%.4f"
            % (rho_bar, worst, clips[worst])
        )
    lines.extend(["", "Xep hang path tai LOAD_MEAN (w_loss=%.1f):" % w_loss])
    for label, link_fn in (
        (
            "v1",
            lambda link: (
                v1_total_delay_ms(
                    T7.LINKS[link][1],
                    T7.LOAD_MEAN[link],
                    bw_mbps=T7.LINKS[link][0],
                    queue_pkts=T7.LINKS[link][2],
                ),
                v1_loss_rate(T7.LOAD_MEAN[link]),
            ),
        ),
        ("v2", lambda link: _v2_link(cv2, mode, link, T7.LOAD_MEAN[link])),
    ):
        vals = [
            (path, *_path_from_link_fn(link_fn, path, w_loss))
            for path in T7.PATH_NAMES
        ]
        ranking = " < ".join(path for path, _d, _l, _c in sorted(vals, key=lambda x: x[3]))
        lines.append("  %s: %s" % (label, ranking))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", action="store_true", help="print the inherited v1-vs-v2 audit")
    ap.add_argument("--mode", default="poisson", choices=tuple(RELIABLE_CEILING))
    ap.add_argument("--w-loss", type=float, default=2500.0)
    args = ap.parse_args(argv)
    if args.audit:
        print(audit_v1_vs_v2(mode=args.mode, w_loss=args.w_loss))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
