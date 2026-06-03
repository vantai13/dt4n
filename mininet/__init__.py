"""DT4N local Mininet layer package.

This project intentionally keeps its Phase 1 code in a directory named
``mininet``. That collides with the real Mininet Python package, whose modules
are also imported as ``mininet.net``, ``mininet.log``, and so on.

To support commands like ``python3 -m mininet.run_phase1`` while still allowing
imports from the real Mininet library, extend this package search path with the
installed Mininet package directory when it is present on the system.
"""

from __future__ import annotations

import glob
import os
import sys


def _extend_with_system_mininet() -> None:
    local_dir = os.path.dirname(__file__)
    candidates = []

    for entry in sys.path:
        if not entry:
            entry = os.getcwd()
        candidates.append(os.path.join(entry, "mininet"))

    candidates.extend(glob.glob("/usr/lib/python*/dist-packages/mininet"))
    candidates.extend(glob.glob("/usr/local/lib/python*/dist-packages/mininet"))
    candidates.extend(glob.glob("/usr/lib/python*/site-packages/mininet"))
    candidates.extend(glob.glob("/usr/local/lib/python*/site-packages/mininet"))

    for candidate in candidates:
        candidate = os.path.abspath(candidate)
        if candidate == os.path.abspath(local_dir):
            continue
        if os.path.isfile(os.path.join(candidate, "log.py")):
            if candidate not in __path__:
                __path__.append(candidate)


_extend_with_system_mininet()
