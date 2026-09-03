# G-A014a — corrigendum to G-A014, and the emitter preregistration re-anchor

Signed: 2026-09-03 UTC, after `phase-G-g3-a014-prereg` and before the first
real-time emitter benchmark. Status: `SYNTHETIC_NO_NETWORK`.

`42-amendment-G-A014-certificate-renewal.md` is published under the annotated
tag `phase-G-g3-a014-prereg` at commit `61beee88`. It is not edited. Two
defects and one blocking omission were found after that tag was pushed, and
they are corrected here in a new document, append-only, as the repository
hygiene rule requires.

No gate, threshold, ladder row, selection rule, or regime from G-A014 is
changed by this corrigendum. `G3-V`, `G3-F`, `G3-C`, `KAP-1`..`KAP-5`, the
ladder, the safety factor 1.5, and the selected `kappa=5` all stand exactly as
signed.

## 1. Corrigendum: the v1 correlation range was quoted selectively

Section 3 of G-A014 states that shared scheduler stalls produced
`rho(uA,uB)` of "0.9912--0.9942 across cells". That range covers only cells B,
C, and F. The full six-cell table in `19-g1-static-nc-smoke-results.md` is:

| cell | A | B | C | D | E | F |
|---|---:|---:|---:|---:|---:|---:|
| v1 `rho(uA,uB)` | 0.7738 | 0.9915 | 0.9942 | 0.9777 | 0.9234 | 0.9912 |
| v2, spin removed | -0.052 | 0.078 | 0.061 | 0.012 | -0.046 | 0.052 |

The correct statement is that v1 produced `rho(uA,uB)` from **0.7738 to
0.9942** across the six A--F cells, and that v2 collapsed the same statistic to
-0.052 .. 0.078 once spin pacing was removed (`22-g1-static-nc-v2-smoke-results.md`).

The corrected range strengthens the argument it was quoting. Every one of the
six v1 values is above the 0.10 gate that G-A014 adopts for `G3-C`, and every
one of the six v2 values is inside it. The conclusion of section 3 is
unaffected; only its quoted interval was wrong.

**G-L90:** a range quoted from a prior table must be read off the whole table.
A subset that happens to support the sentence is the failure mode that is
hardest to catch in review, because the number itself is real.

## 2. The emitter runner cannot execute above G-A014 without a re-anchor

`tools/g3_emitter_dryrun.py` refuses to execute unless local HEAD,
`origin/main`, and its `PREREG_TAG` resolve to one commit:

    "pass": result.returncode == 0 and remote_main == head and remote_tag == head
    ...
    raise SystemExit("REFUSED: origin main/prereg tag do not match local HEAD")

`PREREG_TAG` was `phase-G-g3-emitter-reduction-prereg`, which resolves to
`eaacc1da`. G-A014 commits above it, so that tag can no longer satisfy the
identity and the runner refuses. G-A014 did not notice this, which is why this
is an omission and not a change of decision.

The tag is NOT moved; moving it would rewrite evidence and is forbidden by
G-L80. A new annotated tag `phase-G-g3-emitter-run-prereg` is created at the
commit carrying this corrigendum, and `PREREG_TAG` is repointed to it. That is
the only line changed in `tools/g3_emitter_dryrun.py`.

A re-anchor preserves the purpose of the stop rule -- proving the executed code
was frozen before execution -- only if no gate moved with it.
`git diff phase-G-g3-emitter-reduction-prereg..phase-G-g3-emitter-run-prereg --
mininet/modulated_emitter.py` must be empty; it is. Everything else the
reduction preregistration pinned is audited unchanged, and is now asserted
against literals in `test/test_g3_emitter_reanchor.py`, so a later silent edit
under a new tag fails the suite:

- `GATE_OVERRUN_FRACTION`, `GATE_QUANT_SIGN`, `GATE_QUANT_PREDICTION`,
  `GATE_TIMING_CORRELATION`, `GATE_SNAPSHOT_P99_S`;
- `EMIT3_NULL_TRIALS`, `EMIT3_NULL_SEED`, `REPLICATES`, `N_WINDOWS` -- the four
  inputs that determine the locked null calibration (median .032332,
  p95 .045294, p99 .051107);
- `SEED`, `DT_S`, `DURATION_S`, `PAYLOAD_BYTES`, `CELLS`;
- the L0/L1/L2 ladder mapping;
- the provenance identity itself, including its three refusal branches.

One consequence is recorded rather than worked around. `test_closure_tags_exist`
requires every tag named in a document to exist in git. This document names
`phase-G-g3-emitter-run-prereg`, which cannot exist until the commit it points
at exists. The suite therefore reports exactly one expected failure,
`test_no_doc_claims_a_missing_tag`, between this commit and the creation of
that tag, and clears with no code change when it is created. The tag is
deliberately not added to `UNRESOLVED_DOC_CLAIMS`: that allow-list is for
milestones that will never exist, and using it for a tag that is about to exist
would be the empty-PASS shape `L79` records.

**G-L89:** a provenance rule that pins HEAD to a tag must ship with a re-anchor
procedure. Otherwise the first legitimate amendment above it either blocks
execution permanently or invites moving a tag, and the second outcome is worse
than the rule was designed to prevent.

## 3. Reproduction status of the pinned dry-run artifact

G-A014 renamed the private `_ar1` helper in `tools/g3_dryrun.py` to `ar1` so
the ladder reuses it instead of copying it, and asserted that no dry-run value
changes. That assertion was verified after the fact rather than assumed: the
pre-rename code at `eaacc1da` and the renamed code produce byte-identical
artifacts on this host, and the renamed code reproduces itself across repeated
runs. The rename is confirmed behaviour-preserving.

The check surfaced a separate, pre-existing fact that is recorded here rather
than left unstated. `results/SMOKE/phase-G/g3_dryrun_a013.json` does not
reproduce field-for-field on this host today. The discrepancy is confined to
simulated quantities in the `tau_p=30 s` regime, is at most `1.07e-13` in
relative terms, changes no verdict, and is present at `eaacc1da` exactly as it
is at `61beee88`. It is therefore not caused by G-A014 and not by the rename.

The two analytic decision checks are bit-identical to the signed artifact:
`DRY-D-NC` `0.01003344481605356` and `DRY-D-PC` `0.2134360846918576`. The kappa
ladder pins only the analytic value, so `test_g3_kappa_ladder` is unaffected.

This is a limitation on the bit-exact reproduction claim for one already-signed
artifact. It is recorded, not adjudicated, and it opens no gate.

## 4. Scope boundary

Unchanged from G-A014. This corrigendum authorizes nothing new to execute.
Mininet remains prohibited until the L0 emitter gates of
`40-amendment-g3-emitter-ladder.md` and `41-amendment-g3-emitter-reduction.md`
pass. The public DOI remains null.

## Artifacts

- `tools/g3_emitter_dryrun.py` (one line: `PREREG_TAG`)
- `test/test_g3_emitter_reanchor.py`

Preregistration tag of G-A014: `phase-G-g3-a014-prereg` (`61beee88`).
Emitter execution anchor: `phase-G-g3-emitter-run-prereg`.
