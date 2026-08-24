"""G23-225: mot cell legacy Phase 22 chi co mot parquet trong source song."""

from __future__ import annotations

import ast
import glob
import os
import re
from collections import defaultdict


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNSUFFIXED_CELL = "poisson@0.925"
PHASE22_CALIB = re.compile(
    r"^results/(?:SUPERSEDED/)?phase-22/calib_set_v3"
    r"(?:_(?P<mode>cbr|poisson|h2)_(?P<rho>[0-9]+\.[0-9]+)(?:_V[0-9]+)?)?"
    r"\.parquet$"
)


def _cell_for_path(path: str) -> str | None:
    match = PHASE22_CALIB.fullmatch(path)
    if match is None:
        return None
    if match.group("mode") is None:
        return UNSUFFIXED_CELL
    return "%s@%.3f" % (match.group("mode"), float(match.group("rho")))


def _references(source_by_name: dict[str, str]) -> dict[str, dict[str, set[str]]]:
    """cell -> parquet -> source files, chi tu string literal la ca path."""
    found: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for source_name, source in source_by_name.items():
        tree = ast.parse(source, filename=source_name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            cell = _cell_for_path(node.value)
            if cell is not None:
                found[cell][node.value].add(source_name)
    return found


def _live_sources() -> dict[str, str]:
    sources = {}
    for pattern in ("cert/*.py", "measurements/*.py", "tools/*.py"):
        for path in sorted(glob.glob(os.path.join(REPO, pattern))):
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            with open(path, encoding="utf-8") as handle:
                sources[rel] = handle.read()
    return sources


def _conflicts(source_by_name: dict[str, str]) -> dict[str, dict[str, set[str]]]:
    return {
        cell: by_path
        for cell, by_path in _references(source_by_name).items()
        if len(by_path) > 1
    }


def test_G23_225_each_legacy_cell_maps_to_one_parquet_path() -> None:
    conflicts = _conflicts(_live_sources())
    detail = []
    for cell, by_path in sorted(conflicts.items()):
        detail.append(cell)
        for path, sources in sorted(by_path.items()):
            detail.append("  %s <- %s" % (path, ", ".join(sorted(sources))))
    assert not conflicts, (
        "mot (mode, rho_bar) legacy anh xa toi NHIEU parquet:\n%s"
        % "\n".join(detail)
    )


def test_G23_225_detector_has_the_L85_positive_control() -> None:
    sources = {
        "canonical.py": (
            'P = "results/SUPERSEDED/phase-22/calib_set_v3.parquet"\n'
        ),
        "stale.py": (
            'P = "results/SUPERSEDED/phase-22/'
            'calib_set_v3_poisson_0.925.parquet"\n'
        ),
    }
    conflicts = _conflicts(sources)
    assert set(conflicts) == {"poisson@0.925"}
    assert len(conflicts["poisson@0.925"]) == 2
