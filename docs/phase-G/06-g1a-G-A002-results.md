# G-A002 result — two-band estimator validation

Run date: 2026-08-29 UTC.  The first run followed annotated tag
`phase-G-g1a-g-a002-prereg` at commit `7c394589`.  It read only the prior
synthetic receipt and generated new synthetic NumPy data.

## Verdict

**G1-0 PASS.**  The complete interpretation is:

- G1-0a `sf` estimator: PASS 5/5 from the preserved receipt.
- G1-0b measurement-error model: PASS; maximum raw attenuation prediction
  error `0.000584`.
- G1-0c two-band estimator: PASS 10/10.
- G1-0d anti-degeneracy and conditioning controls: PASS 10/10.

| sf | r true | rho eps true | r hat | r error | rho hat | rho error | cond(A) p95 | gap p05 | verdict |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0.30 | 0.00 | 1.00 | -0.0199 | -0.0199 | 1.0005 | 0.0005 | 5.41 | 0.273 | PASS |
| 0.30 | 0.40 | 0.90 | 0.3977 | -0.0023 | 0.9004 | 0.0004 | 5.41 | 0.273 | PASS |
| 0.50 | 0.00 | 1.00 | 0.0112 | 0.0112 | 0.9998 | -0.0002 | 2.80 | 0.439 | PASS |
| 0.50 | 0.40 | 0.90 | 0.3875 | -0.0125 | 0.9008 | 0.0008 | 2.80 | 0.439 | PASS |
| 0.70 | 0.00 | 1.00 | 0.0107 | 0.0107 | 0.9980 | -0.0020 | 1.83 | 0.569 | PASS |
| 0.70 | 0.40 | 0.90 | 0.3947 | -0.0053 | 0.8993 | -0.0007 | 1.83 | 0.569 | PASS |
| 0.85 | 0.00 | 1.00 | 0.0015 | 0.0015 | 0.9998 | -0.0002 | 1.75 | 0.582 | PASS |
| 0.85 | 0.40 | 0.90 | 0.3982 | -0.0018 | 0.8996 | -0.0004 | 1.75 | 0.582 | PASS |
| 0.95 | 0.00 | 1.00 | 0.0110 | 0.0110 | 0.9856 | -0.0144 | 3.22 | 0.399 | PASS |
| 0.95 | 0.40 | 0.90 | 0.3989 | -0.0011 | 0.9060 | 0.0060 | 3.22 | 0.399 | PASS |

Maximum absolute median error was `0.01995` for `r_true` and `0.01439` for
`rho_epsilon`, below the locked 0.05 thresholds.  Maximum p95 condition number
was `5.409`; minimum p05 `abs(w-sf)` was `0.273`.

`physical_range_fraction` is retained per cell as a diagnostic.  Its minimum
was 0.3125 in a boundary case with `rho_epsilon_true=1`: finite-sample
unconstrained estimates can lie slightly above one even though median error is
small.  Future analysis must report this field and treat materially
out-of-range experimental estimates as model/measurement invalidity, not clip
them silently.

## Resource use and artifact

- Elapsed: `0:03.38`.
- Maximum RSS: `39,304 KiB`.
- Artifact: `results/SMOKE/phase-G/g1a_two_band_validation.json`.
- SHA256: `1cd444b9de028ab32b2cfa434968ef61b9ba8f9ed1d7b3f8980b0bc6dc5f59ff`.

This closes only synthetic G1-0.  Reanalysis of existing Phase D data needs a
separate preregistration; new RAW Mininet experiments remain DOI-blocked.
