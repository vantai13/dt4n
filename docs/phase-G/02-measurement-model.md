# Phase G.1 — measurement-path model

The measured series is modelled per link as

```text
rho_measured,l(t) = rho_true,l(t) + epsilon_l(t)
```

The nugget `epsilon` is temporally white with variance `v_l`, but may be
correlated between links with correlation `rho_epsilon`.

The resulting signal fraction and corrections are

```text
sf_l = sigma_l^2 / (sigma_l^2 + v_l)
tau_true = (tau_hat_measured - 0.5*dt*(1-sf_l)) / sf_l
r_true = (r_measured - sqrt((1-sf_l)(1-sf_m))*rho_epsilon)
         / sqrt(sf_l*sf_m)
```

Signal fraction is estimated by fitting the first eight positive ACF lags
above `2/sqrt(n)` to `log(ACF(k)) = log(sf) + k*log(phi)`.  Common-mode noise
was initially estimated with correlation after first differencing.  G-A002
showed that this raw statistic follows the known attenuation

```text
Corr(diff(x_l),diff(x_m)) = rho_epsilon/(1+lambda)
lambda = (1-phi)*sf/(1-sf)
```

and is therefore a model positive control, not the primary estimator.

The primary estimator uses two bands.  Level correlation and first-difference
correlation provide two linear equations with different signal weights:

```text
r_level = sqrt(sf_l sf_m)*r_true + sqrt((1-sf_l)(1-sf_m))*rho_epsilon
r_diff  = sqrt(w_l w_m)*r_true + sqrt((1-w_l)(1-w_m))*rho_epsilon
w = sf*(1-phi)/(sf*(1-phi) + 1-sf)
```

The system is solved only when `cond(A)<=10`; the G0 constraint
`tau/dt>=10` keeps the synthetic validation well conditioned.

The two-band estimator passed G1-A/G-A002.  Applying it to existing Phase D
data is a separate, preregistered analysis; applying it to new network data
also remains subject to custody and measurement-path gates.
