"""Prove the C/F5 B3 amendment changes only explanations and source identity."""
import hashlib
import json
import subprocess
from pathlib import Path

BASE = "b4299d913d464a057b5f48a63de6a09a72d22bd9"
PATH = "docs/phase-20R2/B3-axis-marginal.json"
old_raw = subprocess.check_output(["git", "show", BASE + ":" + PATH])
new_raw = Path(PATH).read_bytes()
old, new = json.loads(old_raw), json.loads(new_raw)
changes = []


def walk(a, b, pointer=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            path = pointer + "/" + key
            if key not in a:
                changes.append({"pointer": path, "kind": "added", "after": b[key]})
            elif key not in b:
                changes.append({"pointer": path, "kind": "removed", "before": a[key]})
            else:
                walk(a[key], b[key], path)
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), pointer
        for index, values in enumerate(zip(a, b)):
            walk(*values, pointer + "/" + str(index))
    elif a != b:
        changes.append({"pointer": pointer, "kind": "changed", "before": a, "after": b})


walk(old, new)
source_pointer = "/source_sha256/tools/20r2_9_axis_marginal.py"
for change in changes:
    allowed_reason = change["kind"] == "added" and change["pointer"].endswith("_undefined_reason")
    allowed_source = change["kind"] == "changed" and change["pointer"] == source_pointer
    assert allowed_reason or allowed_source, change
assert sum(c["pointer"] == source_pointer for c in changes) == 1
report = {
    "schema": "dt4n.20r2_9_c.b3_amendment.v1",
    "status": "PASS",
    "base_commit": BASE,
    "artifact": PATH,
    "before_sha256": hashlib.sha256(old_raw).hexdigest(),
    "after_sha256": hashlib.sha256(new_raw).hexdigest(),
    "n_changes": len(changes),
    "changes": changes,
    "scientific_values_changed": False,
    "reason": "F5 adds a local explanation for every null and refreshes the producer source digest.",
}
out = Path("docs/phase-20R2/C-validation/B3-amendment-check.json")
with out.open("x") as handle:
    json.dump(report, handle, indent=2, sort_keys=True)
    handle.write("\n")
print("PASS", len(changes), "schema/provenance changes; zero scientific values changed")
