# AMENDMENT 8 -- Phase 21R

Ngay ky: 2026-08-12
Nguoi ky: Codex theo yeu cau owner repo DT4N
Boi canh: sau khi chay `cert/operational_sigma.py`. Day la phan tich do ben
da khai bao truoc o P9: duong operational bao cao rieng. Khong ha nguong gate.

## H1. Ket qua: 10 o duoi sigma van hanh

| Cell | sigma | anchor | cov marginal | q(B0) | q(B3) | ratio | acc(k=1) | err(k=1) | err\|reject |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `cbr@0.700` | 0.04622 | 0.000000 | 0.90858 | 0.0103 | 0.0103 | 0.998 | 1.0000 | 0.000000 | -- |
| `cbr@0.850` | 0.01308 | 0.000000 | 0.91110 | 0.0081 | 0.0081 | 0.999 | 1.0000 | 0.000000 | -- |
| `poisson@0.700` | 0.04622 | 0.141305 | 0.90399 | 1.0083 | 2.2645 | 2.246 | 0.3941 | 0.018530 | 0.22116 |
| `poisson@0.850` | 0.04797 | 0.330766 | 0.90090 | 15.1663 | 35.0995 | 2.314 | 0.0794 | 0.064478 | 0.35375 |
| `poisson@0.925` | 0.02180 | 0.288899 | 0.89912 | 24.3053 | 51.9968 | 2.139 | 0.1969 | 0.041572 | 0.34955 |
| `poisson@0.960` | 0.00959 | 0.199325 | 0.90735 | 17.8291 | 38.4545 | 2.157 | 0.2956 | 0.023267 | 0.27322 |
| `h2@0.700` | 0.04622 | 0.301304 | 0.90166 | 27.3326 | 58.9691 | 2.157 | 0.1697 | 0.047947 | 0.35307 |
| `h2@0.850` | 0.04797 | 0.258487 | 0.90594 | 81.4597 | 174.9093 | 2.147 | 0.2325 | 0.030575 | 0.32752 |
| `h2@0.925` | 0.02180 | 0.077595 | 0.90887 | 48.0028 | 102.9331 | 2.144 | 0.6146 | 0.008618 | 0.18758 |
| `h2@0.960` | 0.00959 | 0.000512 | 0.90615 | 24.3486 | 51.3169 | 2.108 | 0.9846 | 0.000240 | 0.01789 |

Gate summary:

```text
G3: marginal coverage in [0.89912, 0.91110] -> PASS 10/10
G4: per-bin coverage tolerance <= 0.05       -> PASS 10/10
H7: nondegenerate cells                      -> PASS 7/7
near-zero degenerate diagnostics             -> PASS 3/3
```

`poisson@0.850` is the useful edge case: it fails the fixed `kappa=1`
acceptance threshold (`0.0794 < 0.10`) but passes H7 at `kappa=0.5`. This is
why the risk-acceptance family must be parameterized by `kappa`.

## H2. Shape invariance of q_hat by age

Shape-invariance report includes `poisson` and `h2` cells. It excludes `cbr`
positive controls, but it does include `h2@0.960`: that cell is degenerate for
H7, yet still has nontrivial q_hat scale and is valid for the age-shape check.

```text
n_cells                  = 8
ratio mean               = 2.176621
ratio sd                 = 0.068233
ratio range              = [2.107591, 2.314317]
relative spread          = 0.09498
qhat(B0) spread factor   = 80.79x
```

So `q_hat(B0)` varies by about `81x`, but `q_hat(B3)/q_hat(B0)` stays in a
narrow band. Scientific statement:

```text
The scale of uncertainty depends strongly on traffic regime, but the age-shape
of uncertainty is nearly invariant under synthetic AR(1), tau=1.0.
```

Limit: this is not yet proven on real telemetry. It is a Phase 23 hypothesis.

## H3. Difficulty is not monotone in rho_bar

Operational anchor error:

```text
poisson: 0.700 -> 0.141, 0.850 -> 0.331, 0.925 -> 0.289, 0.960 -> 0.199
h2     : 0.700 -> 0.301, 0.850 -> 0.258, 0.925 -> 0.078, 0.960 -> 0.001
```

`poisson` peaks at `rho_bar=0.850`; `h2` decreases across the operational path.
The reason is the sigma-rho confound: operational `sigma_max(rho_bar)` also
peaks in the middle and then collapses near the reliability ceiling.

Required paper wording:

```text
In the operational path, decision difficulty is not monotone in mean load,
because the available fluctuation amplitude sigma_max(rho_bar) peaks at
intermediate load. The fixed-sigma path isolates rho_bar; the operational path
checks robustness under natural conditions.
```

## H4. Direct comparison with fixed-sigma path

| Cell | fixed anchor | fixed q(B0) | fixed acc(k=1) | operational sigma | operational anchor | operational q(B0) | operational acc(k=1) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `poisson@0.700` | 0.0000 | 0.2356 | 1.000 | 0.04622 | 0.1413 | 1.0083 | 0.394 |
| `poisson@0.850` | 0.2207 | 3.1843 | 0.241 | 0.04797 | 0.3308 | 15.1663 | 0.079 |
| `poisson@0.925` | 0.2224 | 11.5878 | 0.284 | 0.02180 | 0.2889 | 24.3053 | 0.197 |
| `poisson@0.960` | 0.1995 | 17.8431 | 0.296 | 0.00959 | 0.1993 | 17.8291 | 0.296 |
| `h2@0.700` | 0.1265 | 6.8197 | 0.497 | 0.04622 | 0.3013 | 27.3326 | 0.170 |
| `h2@0.850` | 0.0029 | 16.7382 | 0.945 | 0.04797 | 0.2585 | 81.4597 | 0.232 |
| `h2@0.925` | 0.0002 | 24.1219 | 0.987 | 0.02180 | 0.0776 | 48.0028 | 0.615 |
| `h2@0.960` | 0.0005 | 24.3657 | 0.984 | 0.00959 | 0.0005 | 24.3486 | 0.985 |

`n_rescued_by_operational = 3`: `poisson@0.700`, `h2@0.850`, and `h2@0.925`
move from degenerate under fixed sigma to nondegenerate under operational sigma.

This differs from the draft lesson text that said 4. The artifact is the source
of truth: `poisson@0.960` was already nondegenerate under fixed sigma, while
`h2@0.960` remains degenerate under the H7 threshold.

## H5. Method note

Robustness is not replication and not generalization:

```text
replication    : same design, new random seeds
robustness     : pre-declared analysis choice changes, same gates
generalization : new environment or real telemetry
```

This lesson is robustness. The variant was pre-declared, the conclusions checked
were G3/G4/H7 plus q_hat age-shape, and no gate threshold was relaxed.
