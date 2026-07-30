# Phase L / Lesson L.7 -- Fit link_model_v2

Source: `results/phase-L/campaign_state.json`

Output model: `results/phase-L/link_model_v2_fit.json`

## Gates

| gate | result |
|---|---:|
| G-L7a predictive gate | 10/10 PASS |
| G-L7b monotone model | 10/10 PASS |
| G-L7c efficiency | mean 1.00, min 1.00, max 1.00 PASS |
| G-L7d sigma exported | PASS |
| G-L7e rho=1.05 marked extrapolated in held-out | PASS |

## Fit Table

| mode | bw | q | R2 interp | RMSE interp | R2 all | R2 kingman | resid sd | sigma sched | efficiency | adj max | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| cbr | 4 | 10 | -314701.2199 | 0.6141 | 0.9971 | 0.6831 | 1.0575 | 1.0575 | 1.00 | 0.0044 | PASS |
| cbr | 6 | 13 | -5353.7750 | 0.9042 | 0.9940 | 0.7309 | 2.5729 | 2.5729 | 1.00 | 0.0059 | PASS |
| cbr | 8 | 18 | -4638.6624 | 1.0389 | 0.9934 | 0.7386 | 1.5743 | 1.5743 | 1.00 | 0.0068 | PASS |
| h2 | 4 | 10 | 0.9999 | 0.0338 | 0.9935 | 0.9308 | 0.2501 | 0.2501 | 1.00 | 0.0000 | PASS |
| h2 | 6 | 13 | 1.0000 | 0.0138 | 0.9906 | 0.9429 | 0.1867 | 0.1867 | 1.00 | 0.0000 | PASS |
| h2 | 8 | 18 | 1.0000 | 0.0201 | 0.9914 | 0.9384 | 0.2057 | 0.2057 | 1.00 | 0.0000 | PASS |
| onoff | 6 | 13 | 0.9969 | 0.2891 | 0.9829 | 0.9632 | 0.4494 | 0.4494 | 1.00 | 0.0061 | PASS |
| poisson | 4 | 10 | 0.9995 | 0.0943 | 0.9775 | 0.9334 | 0.2223 | 0.2223 | 1.00 | 0.0000 | PASS |
| poisson | 6 | 13 | 0.9996 | 0.0795 | 0.9679 | 0.9455 | 0.2491 | 0.2491 | 1.00 | 0.0000 | PASS |
| poisson | 8 | 18 | 0.9997 | 0.0695 | 0.9617 | 0.9403 | 0.2253 | 0.2253 | 1.00 | 0.0000 | PASS |

CBR uses held-out RMSE instead of R2 because the curve is nearly flat at the software floor.
For CBR, the predictive gate is evaluated only on subcritical held-out rho <= 0.90; the critical shoulder is reported separately because Amendment 6 marked rho near 1 as singular.
Small non-monotone measurement wiggles are projected with weighted isotonic regression before PCHIP; the raw means remain in `delay_observed`.

![Delay curves](figures/l7_ref_curves.svg)

![Sigma curves](figures/l7_ref_sigma.svg)

## Variance Floor

| quantity | value ms |
|---|---:|
| sigma_machine | 0.0029 |
| sigma_repeat | 0.0096 |
| sigma_schedule | 0.2824 |
| alpha=0.10 half-width floor | 0.4646 |
| schedule variance share | 0.99874 |

## c_a Counterexample at bw=6 q=13 rho=0.90

| mode | c_a mean | c_a sd | q mean ms | q sd ms | Reich mean ms |
|---|---:|---:|---:|---:|---:|
| cbr | 0.0042 | 0.0018 | 0.1330 | 0.0029 | 2.0161 |
| poisson | 1.0032 | 0.0063 | 5.7248 | 0.2800 | 10.7442 |
| h2 | 2.0316 | 0.0208 | 11.0411 | 0.2824 | 35.3998 |
| onoff | 2.3122 | 0.6022 | 6.6310 | 0.5836 | 25.9100 |

Reich/delay correlation across the four modes: `0.9376`.

Conclusion: do not build `f(rho, c_a)`. The deployable model remains conditioned by traffic family.
