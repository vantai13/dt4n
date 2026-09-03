# G-A014 kappa ladder results

Date: 2026-09-03 UTC. Verdict: **PASS 6/6**. Status: `SYNTHETIC_NO_NETWORK`.
No emitter, Mininet, OVS, or RAW network run was started; the ladder is pure
algebra over the signed topology plus one Monte Carlo control.

Source commit: `61beee884dd03c700075e0bfe02ff6e667de8dc2`, the commit carrying
the annotated preregistration tag `phase-G-g3-a014-prereg`. The artifact was
generated after that tag reached `origin`, as G-L80 requires.

## Ladder and selection

The selection rule, fixed before the table, is the smallest `kappa` whose
analytic pairwise flip spread reaches `1.5 x 0.10`. All eight rows are reported,
including the four the rule rejects.

| kappa | tau_p (s) | T_pc (s) | flip spread | campaign hours | selected |
|---:|---:|---:|---:|---:|:--|
| 1 | 3 | 600 | .00000 | 6.42 | negative control |
| 2 | 6 | 1200 | .08265 | 9.75 | below inherited gate |
| 3 | 9 | 1800 | .12394 | 13.08 | below design margin |
| 4 | 12 | 2400 | .14966 | 16.42 | below design margin by .00034 |
| **5** | **15** | **3000** | **.16763** | **19.75** | **selected** |
| 6 | 18 | 3600 | .18109 | 23.08 | |
| 8 | 24 | 4800 | .20023 | 29.75 | |
| 10 | 30 | 6000 | .21344 | 36.42 | regime signed in 31-prereg-g3 |

The `kappa=10` row reproduces the signed `DRY-D-PC` value
`0.2134360846918576` exactly, because the ladder imports `contrast`,
`quad_forms`, and `p_flip` from `tools.g2_decision_flow` rather than restating
the algebra. `test_g3_kappa_ladder` asserts that reproduction against the
committed `g3_dryrun_a013.json` to `1e-12`.

Selecting `kappa=5` over the signed `kappa=10` cuts the campaign from 36.42 to
19.75 wall-clock hours, a 45.8% reduction, and leaves the flip spread 67.6%
above the inherited `0.10` gate.

## Omega round trip at the selected regime

Five omega values, 40 replicates, seed `20260910`, `T=3000 s`.

| omega | median | bias | SD |
|---:|---:|---:|---:|
| .00 | -.000126 | -.000126 | .012714 |
| .25 | .247460 | -.002540 | .022934 |
| .50 | .489942 | -.010058 | .030588 |
| .75 | .746998 | -.003002 | .032040 |
| 1.00 | .999087 | -.000913 | .028442 |

## Gate table

| id | check | value | gate | verdict |
|---|---|---:|---:|:--|
| KAP-1 | selected kappa flip spread | .167632 | >= .150000 | PASS |
| KAP-2 | kappa=1 negative control flat | .000000 | <= 1e-12 | PASS |
| KAP-3a | omega round-trip max abs median bias | .010058 | <= .05 | PASS |
| KAP-3b | omega round-trip max SD | .032040 | <= .05 | PASS |
| KAP-4 | mixture ACF monotonicity violation | .000000 | <= 0 | PASS |
| KAP-5 | campaign wall-clock hours | 19.75 | <= 24.0 | PASS |

`KAP-2` is exactly zero, not merely small: at `kappa=1` the two exponentials
coincide and omega cancels from the stale correlation identically. That is
G-A010 restated as arithmetic.

## Artifact and verification

    results/SMOKE/phase-G/g3_kappa_ladder.json
    sha256 a9534bafd289ecd08b53eabdf586e473870a73db6114999df05f4264b3964f5f

Runtime was 19.662 s. A re-execution measured 19.73 s wall clock and maximum
RSS 44,804 KiB, and reproduced the artifact field-for-field apart from
`git_hash` and `elapsed_s`. Unlike `g3_dryrun_a013.json` (see
`43-amendment-G-A014a-corrigendum-and-reanchor.md` section 3), this artifact is
bit-reproducible on this host.

This closes the budget prerequisite for the G.3 campaign. It authorizes no
network run: `G3-V`, `G3-F`, and `G3-C` are gates on the first physical run,
and Mininet remains prohibited until the L0 emitter gates pass.
