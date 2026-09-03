# Addenda to the G.3 emitter receipts

Status: append-only notes on `docs/phase-G/45-g3-emitter-dryrun-results.md`
and `docs/phase-G/46-g3-emit3-decomposition-results.md`, both of which are
published at commit `0c6a6ca5` and are not edited. Neither note changes a
verdict, a gate, or a number in those documents.

## 1. Custody of the emitter dry-run artifact

`results/SMOKE/phase-G/g3_emitter_dryrun.json` entered the repository in
commit `23bf7ae8`, whose message, "add sth", does not record what was added
or why. That artifact is the evidence for an adjudicated `FAIL`, so it should
have arrived with a stated purpose.

The file has not been modified since. Its digest in `23bf7ae8`, its digest at
the commit carrying doc 45, and the digest recorded in doc 45 are all

    96a4a744abb2e00f457aa18b72c4bcbf5724487fd1f1fa2bdf6edca0c8423bdb

verified by `git show <ref>:<path> | sha256sum` at all three points. This note
supplies the provenance the original commit message omitted. No history is
rewritten.

**G-L95:** an adjudicating artifact must enter the repository through a commit
whose message says what it is. A message that does not forces a later custody
note, and a note written afterwards is weaker evidence than a message written
at the time.

## 2. Cross-phase confirmation that this host is not stationary

Doc 46 records that the A3 residual moved from `+0.127` to `+0.0842` between
two executions of the same design about twelve minutes apart, and states its
conclusion so that it depends only on the sign of that residual relative to
the calibrated baseline, not on its value.

That instability is independently corroborated.
`docs/phase-G/16-measurement-coherence-results.md` reports no stationary
window `W*` anywhere on the signed grid: every one of four links fails at
every one of five window widths, with `CV(v_projected) / null p95` ratios from
0.168 to 6.445.

Two different instruments, in two different phases of the project, months
apart, report the same property of this host: it is not stationary. The A3
run-to-run spread is therefore an expected observation about the measurement
environment rather than an anomaly of the decomposition, and it is one more
reason the clean-host repetition contemplated in doc 45 must be declared a new
run in a different environment rather than a replacement.

This note asserts no mechanism and opens no gate.
