#!/usr/bin/env python3
"""Kiểm 1 (Lesson 10.1) — golden test: frozen v1 chưa trôi."""
import hashlib
import json
import os

FROZEN = "frozen_policies/v1"
NOISE_FLOOR = 0.04   # từ train.json


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def test_sha256_matches_manifest():
    manifest = json.load(open(os.path.join(FROZEN, "manifest.json")))
    for entry in manifest["seeds"]:
        seed = entry["seed"]
        model = os.path.join(FROZEN, f"seed{seed}", "model.pt")
        got = sha256(model)
        want = entry["model_sha256"]
        assert got == want, f"seed{seed} SHA256 LỆCH! model.pt đã đổi.\n got={got}\nwant={want}"
        print(f"seed{seed}: sha256 OK")


if __name__ == "__main__":
    test_sha256_matches_manifest()
    print("\n✅ KIỂM 1 PASS — 5 model.pt khớp manifest, frozen chưa trôi.")
    