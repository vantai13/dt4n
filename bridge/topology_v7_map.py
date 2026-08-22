#!/usr/bin/env python3
"""Single mapping from topology_v7 logical links to Ditto Thing IDs."""

from __future__ import annotations

import json
from typing import Dict

from bridge.ditto_common import make_thing_id_link
from twin import topology_v7 as T7


SPEC_PATH = "ditto/topology_v7_spec.json"


def link_thing_ids(spec_path: str = SPEC_PATH) -> Dict[str, str]:
    """Return IDs in exactly ``T7.LINK_NAMES`` order and reject drift."""
    with open(spec_path, encoding="utf-8") as handle:
        spec = json.load(handle)
    by_logical = {link["logical"]: link for link in spec["links"]}
    missing = set(T7.LINK_NAMES) - set(by_logical)
    extra = set(by_logical) - set(T7.LINK_NAMES)
    if missing:
        raise ValueError("spec thieu link logic: %s" % sorted(missing))
    if extra:
        raise ValueError("spec co link la: %s" % sorted(extra))
    return {
        name: make_thing_id_link(*by_logical[name]["endpoints"])
        for name in T7.LINK_NAMES
    }
