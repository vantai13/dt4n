#!/usr/bin/env python3
"""Render the Phase 21.4 usefulness frontier as a dependency-free SVG."""

from __future__ import annotations

import argparse
import json
import os
from html import escape
from typing import Iterable


SERIES = [
    ("adaptive", "Adaptive q_hat(z)", "#1f77b4"),
    ("const", "Constant threshold", "#d62728"),
    ("random", "Random accept", "#7f7f7f"),
    ("oracle", "Oracle", "#2ca02c"),
]


def _points(rows: list[dict], key: str) -> list[tuple[float, float]]:
    pts = []
    for row in rows:
        item = row[key]
        x = float(item["coverage"])
        y = float(item["err_accept"])
        if y == y:
            pts.append((x, y))
    return pts


def _polyline(points: Iterable[tuple[float, float]], color: str, sx, sy) -> str:
    encoded = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)
    return f'<polyline points="{encoded}" fill="none" stroke="{color}" stroke-width="2.5"/>'


def _recommended_coverage(rows: list[dict], eps_max: float) -> float:
    coverage = [
        float(row["adaptive"]["coverage"])
        for row in rows
        if float(row["eps_ms"]) <= float(eps_max)
    ]
    return max(coverage) if coverage else 0.0


def render_svg(report: dict, title: str, recommended_eps_max: float = 50.0) -> str:
    rows = report["frontier"]
    all_points = []
    for key, _label, _color in SERIES:
        all_points.extend(_points(rows, key))
    anchor = report.get("anchor", {})
    if anchor:
        all_points.append((1.0, float(anchor["err_accept"])))

    width, height = 900, 560
    left, right, top, bottom = 78, 32, 54, 68
    plot_w = width - left - right
    plot_h = height - top - bottom
    x_max = 1.0
    y_max = max(0.22, max(y for _x, y in all_points) * 1.08)

    def sx(x: float) -> float:
        return left + x / x_max * plot_w

    def sy(y: float) -> float:
        return top + (1.0 - y / y_max) * plot_h

    rec_cov = _recommended_coverage(rows, recommended_eps_max)
    rec_x = sx(rec_cov)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial,Helvetica,sans-serif;fill:#1f2937} .tick{font-size:12px;fill:#4b5563}",
        ".grid{stroke:#e5e7eb;stroke-width:1}.axis{stroke:#111827;stroke-width:1.4}",
        ".title{font-size:20px;font-weight:700}.label{font-size:14px;font-weight:700}.legend{font-size:13px}",
        "</style>",
        '<rect x="0" y="0" width="900" height="560" fill="#ffffff"/>',
        f'<text class="title" x="{left}" y="30">{escape(title)}</text>',
        (
            f'<rect x="{left}" y="{top}" width="{max(0.0, rec_x - left):.1f}" '
            f'height="{plot_h}" fill="#e8f3ff" opacity="0.55"/>'
        ),
        (
            f'<line x1="{rec_x:.1f}" y1="{top}" x2="{rec_x:.1f}" y2="{height-bottom}" '
            'stroke="#2563eb" stroke-width="1.4" stroke-dasharray="5 5"/>'
        ),
        (
            f'<text class="legend" x="{rec_x-8:.1f}" y="{top+18}" text-anchor="end">'
            f'recommended eps&lt;={recommended_eps_max:.0f}, cov&lt;={rec_cov:.2f}</text>'
        ),
    ]

    for i in range(6):
        x = i / 5
        px = sx(x)
        parts.append(f'<line class="grid" x1="{px:.1f}" y1="{top}" x2="{px:.1f}" y2="{height-bottom}"/>')
        parts.append(f'<text class="tick" x="{px:.1f}" y="{height-bottom+23}" text-anchor="middle">{x:.1f}</text>')
    for i in range(6):
        y = y_max * i / 5
        py = sy(y)
        parts.append(f'<line class="grid" x1="{left}" y1="{py:.1f}" x2="{width-right}" y2="{py:.1f}"/>')
        parts.append(f'<text class="tick" x="{left-10}" y="{py+4:.1f}" text-anchor="end">{y:.2f}</text>')

    parts.extend(
        [
            f'<line class="axis" x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}"/>',
            f'<text class="label" x="{left + plot_w/2:.1f}" y="{height-18}" text-anchor="middle">Coverage</text>',
            f'<text class="label" transform="translate(20 {top + plot_h/2:.1f}) rotate(-90)" text-anchor="middle">err|accept</text>',
        ]
    )

    for key, label, color in SERIES:
        pts = _points(rows, key)
        parts.append(_polyline(pts, color, sx, sy))
        for x, y in pts:
            parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3.2" fill="{color}"/>')

    if anchor:
        ax = sx(1.0)
        ay = sy(float(anchor["err_accept"]))
        parts.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="4.5" fill="#111827"/>')
        parts.append(f'<text class="legend" x="{ax-8:.1f}" y="{ay-10:.1f}" text-anchor="end">anchor</text>')

    legend_x, legend_y = left + 12, top + 16
    for i, (_key, label, color) in enumerate(SERIES):
        y = legend_y + i * 22
        parts.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x+24}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text class="legend" x="{legend_x+32}" y="{y+4}">{escape(label)}</text>')

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--out-svg", required=True)
    parser.add_argument("--title", default="Figure 3. Phase 21.4 risk-coverage frontier")
    parser.add_argument("--recommended-eps-max", type=float, default=50.0)
    args = parser.parse_args()

    with open(args.json, "r", encoding="utf-8") as fh:
        report = json.load(fh)
    svg = render_svg(report, args.title, args.recommended_eps_max)
    os.makedirs(os.path.dirname(args.out_svg) or ".", exist_ok=True)
    with open(args.out_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"[write] {args.out_svg}")


if __name__ == "__main__":
    main()
