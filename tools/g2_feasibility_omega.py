#!/usr/bin/env python3
"""Per-link feasibility for the physically wireable G.2 omega generator."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from tools.g1_quant_model import (
    QUANT_VAR_PACKETS_CUMULATIVE_MIXED,
    QUANT_VAR_PACKETS_INDEPENDENT_ROUND,
    WIRE_BYTES_DEFAULT,
    packet_rho_quantum,
)
from tools.g2_topology import (
    CAP_BPS,
    DEGREE,
    LINKS,
    a0_from_sigma_at,
    sigma_per_link,
)


Z_CLIP = 2.58
RHO_MAX = 0.995
HEADROOM_MIN = 5.0
WIRE_BYTES = WIRE_BYTES_DEFAULT
DEFAULT_G1_CERTIFICATE = Path(
    "results/LIVE/phase-G/measurement_path_cert.json"
)
DEFAULT_G1_MEASUREMENT = Path(
    "results/SMOKE/phase-G/g1_closed_form_sf.json"
)
QUANT_MODES = {
    "independent_round": QUANT_VAR_PACKETS_INDEPENDENT_ROUND,
    "cumulative_mixed": QUANT_VAR_PACKETS_CUMULATIVE_MIXED,
}


def git_hash() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() or "unknown"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_g1_contract(
    certificate_path: Path, measurement_path: Path
) -> tuple[dict[str, float], dict[str, object]]:
    """Verify the LIVE certificate pin, then load worst-case per-link floors."""
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    if certificate.get("schema") != "dt4n.phase_g.measurement_path_certificate.v1":
        raise SystemExit("REFUSED: unsupported G.1 certificate schema")
    if certificate.get("status") != "CONDITIONAL_PASS" or not certificate.get("g1_closed"):
        raise SystemExit("REFUSED: G.1 certificate is not a closed conditional pass")
    validity = certificate.get("validity")
    if not isinstance(validity, dict) or validity.get("schema") != "dt4n.validity.v1":
        raise SystemExit("REFUSED: G.1 certificate lacks a valid validity block")

    measurement_sha = sha256(measurement_path)
    pinned = certificate.get("provenance", {}).get("artifacts", {})
    if measurement_sha not in pinned.values():
        raise SystemExit(
            "REFUSED: G.1 measurement sha256 is not pinned by the LIVE certificate"
        )
    scope = certificate.get("scope", {})
    expected_scope = {
        "quantization_mode": "independent_round",
        "carry_accumulator": False,
        "wire_bytes": WIRE_BYTES,
        "measured_window_s": 0.2,
        "topology": "phase-20-v7",
    }
    for key, expected in expected_scope.items():
        if scope.get(key) != expected:
            raise SystemExit(
                "REFUSED: certificate scope %s=%r, expected %r"
                % (key, scope.get(key), expected)
            )

    measurement = json.loads(measurement_path.read_text(encoding="utf-8"))
    if measurement.get("schema") != "dt4n.phase_g.g1_closed_form_measure.v2":
        raise SystemExit("REFUSED: unsupported G.1 measurement schema")
    if measurement.get("future_quantization_mode") != "independent_round":
        raise SystemExit("REFUSED: G.1 measurement used another future mode")
    if float(measurement.get("wire_bytes", -1.0)) != WIRE_BYTES:
        raise SystemExit("REFUSED: G.1 measurement used another wire size")

    sigma_min: dict[str, float] = {}
    for run in measurement.get("runs", []):
        for row in run.get("links", []):
            link = str(row["link"])
            value = float(row["sigma_min_conservative_sf85"])
            sigma_min[link] = max(sigma_min.get(link, 0.0), value)
    missing = set(LINKS) - set(sigma_min)
    extra = set(sigma_min) - set(LINKS)
    if missing or extra:
        raise SystemExit(
            "REFUSED: G.1 links mismatch (missing=%s, extra=%s)"
            % (sorted(missing), sorted(extra))
        )
    binding = max(sigma_min.values())
    if not np.isclose(
        binding, float(measurement["sigma_min_binding_all_runs"]), rtol=0.0, atol=1e-15
    ):
        raise SystemExit("REFUSED: G.1 binding floor disagrees with per-link rows")
    return sigma_min, {
        "certificate_path": str(certificate_path),
        "certificate_sha256": sha256(certificate_path),
        "measurement_path": str(measurement_path),
        "measurement_sha256": measurement_sha,
        "measurement_sha256_pinned": True,
        "certificate_status": certificate["status"],
        "certificate_expiry_conditions": certificate.get("expiry_conditions", []),
        "sigma_grid_boundary": float(scope["sigma_min_grid"]),
    }


def sigma_pack(dt_s: float, quant_var_packets: float) -> np.ndarray:
    quantum = np.asarray(
        [packet_rho_quantum(WIRE_BYTES, dt_s, capacity) for capacity in CAP_BPS]
    )
    return quantum * np.sqrt(quant_var_packets)


def evaluate(
    a0: float,
    rho_bar: float,
    dt_s: float,
    quant_var_packets: float,
    sigma_min: np.ndarray,
) -> dict[str, object]:
    """Evaluate all three feasibility gates separately on all eight links."""
    sigma = sigma_per_link(a0)
    packet_floor = sigma_pack(dt_s, quant_var_packets)
    headroom = sigma / packet_floor
    clipping_bound = rho_bar + Z_CLIP * sigma
    gate_headroom = headroom >= HEADROOM_MIN
    gate_measurement = sigma >= sigma_min
    gate_clipping = clipping_bound <= RHO_MAX
    return {
        "a0": float(a0),
        "rho_bar": float(rho_bar),
        "dt_s": float(dt_s),
        "quant_var_packets": float(quant_var_packets),
        "sigma_per_link": dict(zip(LINKS, sigma.tolist())),
        "sigma_nom_uA": float(sigma[LINKS.index("uA")]),
        "sigma_min_link": float(sigma.min()),
        "sigma_max_link": float(sigma.max()),
        "sigma_spread": float(sigma.max() / sigma.min()),
        "headroom_per_link": dict(zip(LINKS, headroom.tolist())),
        "gate_headroom": bool(gate_headroom.all()),
        "gate_measurement": bool(gate_measurement.all()),
        "gate_clipping": bool(gate_clipping.all()),
        "binding_headroom": [LINKS[i] for i in np.where(~gate_headroom)[0]],
        "binding_measurement": [LINKS[i] for i in np.where(~gate_measurement)[0]],
        "binding_clipping": [LINKS[i] for i in np.where(~gate_clipping)[0]],
        "feasible": bool(
            gate_headroom.all() and gate_measurement.all() and gate_clipping.all()
        ),
    }


def feasible_window(
    rho_bar: float,
    dt_s: float,
    quant_var_packets: float,
    sigma_min: np.ndarray,
) -> dict[str, object]:
    """Compute the exact closed-form feasible interval for ``a0``."""
    packet_floor = sigma_pack(dt_s, quant_var_packets)
    unit = np.sqrt(DEGREE) / CAP_BPS
    lower_headroom_per_link = HEADROOM_MIN * packet_floor / unit
    lower_measurement_per_link = sigma_min / unit
    lower_per_link = np.maximum(lower_headroom_per_link, lower_measurement_per_link)
    upper_per_link = ((RHO_MAX - rho_bar) / Z_CLIP) / unit
    lower = float(lower_per_link.max())
    upper = float(upper_per_link.min())
    lower_link = int(np.argmax(lower_per_link))
    upper_link = int(np.argmin(upper_per_link))
    lower_source = (
        "headroom"
        if lower_headroom_per_link[lower_link] >= lower_measurement_per_link[lower_link]
        else "measurement"
    )
    nonempty = upper >= lower
    return {
        "a0_min": lower,
        "a0_min_from": lower_source,
        "a0_min_link": LINKS[lower_link],
        "a0_max": upper,
        "a0_max_link": LINKS[upper_link],
        "ratio": float(upper / lower) if nonempty else 0.0,
        "nonempty": bool(nonempty),
        "sigma_nom_range_uA": [
            float(lower * unit[LINKS.index("uA")]),
            float(upper * unit[LINKS.index("uA")]),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--g1-certificate", default=str(DEFAULT_G1_CERTIFICATE))
    parser.add_argument("--g1-measurement", default=str(DEFAULT_G1_MEASUREMENT))
    parser.add_argument("--rho-bar", type=float, nargs="*", default=[0.857, 0.9195])
    parser.add_argument("--dt", type=float, default=0.2)
    parser.add_argument("--sigma-ref", type=float, nargs="*")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    sigma_min_by_link, provenance = load_g1_contract(
        Path(args.g1_certificate), Path(args.g1_measurement)
    )
    sigma_min = np.asarray([sigma_min_by_link[link] for link in LINKS])
    sigma_grid = (
        args.sigma_ref
        if args.sigma_ref is not None
        else [
            provenance["sigma_grid_boundary"] * multiplier
            for multiplier in (1.0, 1.5, 2.0)
        ]
    )

    windows = []
    cells = []
    for mode, quant_variance in QUANT_MODES.items():
        for rho_bar in args.rho_bar:
            window = feasible_window(
                rho_bar, args.dt, quant_variance, sigma_min
            )
            window.update({"quant_mode": mode, "rho_bar": rho_bar})
            windows.append(window)
            for sigma_ref in sigma_grid:
                cell = evaluate(
                    a0_from_sigma_at("uA", sigma_ref),
                    rho_bar,
                    args.dt,
                    quant_variance,
                    sigma_min,
                )
                cell.update({"quant_mode": mode, "sigma_ref_at_uA": sigma_ref})
                cells.append(cell)

    artifact = {
        "schema": "dt4n.phase_g.g2_feasibility_omega.v1",
        "status": "ANALYTIC_NO_NETWORK",
        "git_hash": git_hash(),
        "g1_contract": provenance,
        "sigma_min_per_link": sigma_min_by_link,
        "sigma_ref_grid": list(sigma_grid),
        "constants": {
            "z_clip": Z_CLIP,
            "rho_max": RHO_MAX,
            "headroom_min": HEADROOM_MIN,
            "wire_bytes": WIRE_BYTES,
        },
        "windows": windows,
        "cells": cells,
        "n_feasible": sum(cell["feasible"] for cell in cells),
        "n_cells": len(cells),
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    print("G.1 certificate: %s" % provenance["certificate_path"])
    print("  certificate sha256 %s..." % provenance["certificate_sha256"][:16])
    print("  measurement sha256 %s... (PIN MATCH)" % provenance["measurement_sha256"][:16])
    print("  sigma_min_l = " + "  ".join(
        "%s:%.5f" % (link, sigma_min_by_link[link]) for link in LINKS
    ))
    for window in windows:
        state = "%.2fx" % window["ratio"] if window["nonempty"] else "EMPTY"
        print("\nMODE %-20s rho_bar=%s" % (
            window["quant_mode"], window["rho_bar"]
        ))
        print("  a0 in [%10,.0f, %10,.0f]  %s  floor:%s(%s) ceiling:%s" % (
            window["a0_min"], window["a0_max"], state,
            window["a0_min_link"], window["a0_min_from"], window["a0_max_link"],
        ))
        for cell in cells:
            if (
                cell["quant_mode"] != window["quant_mode"]
                or cell["rho_bar"] != window["rho_bar"]
            ):
                continue
            failures = []
            for label, key in (
                ("hr", "binding_headroom"),
                ("sf", "binding_measurement"),
                ("clip", "binding_clipping"),
            ):
                if cell[key]:
                    failures.append("%s:%s" % (label, ",".join(cell[key])))
            print(
                "    sigma_ref=%.8f a0=%9,.0f sig_l=[%.4f,%.4f] %-8s %s"
                % (
                    cell["sigma_ref_at_uA"], cell["a0"],
                    cell["sigma_min_link"], cell["sigma_max_link"],
                    "FEASIBLE" if cell["feasible"] else "REJECT",
                    " | ".join(failures),
                )
            )
    print("\nG.2 FEASIBILITY: %d/%d cells" % (
        artifact["n_feasible"], artifact["n_cells"]
    ))


if __name__ == "__main__":
    main()

