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
is initially estimated with correlation after first differencing.  That raw
high-pass proxy is valid only if its signal-leakage positive control is small;
it is not silently treated as an exact estimator.

No estimator in `tools/measurement_path_calib.py` may be used on Phase D data
or new network data until it passes the synthetic G1-A gate.
