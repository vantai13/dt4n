# Amendment G-A017a -- the nugget is not one thing

Date: 2026-09-05 UTC. Status: `AMENDMENT_PRE_EXECUTION`.

This is an append-only amendment to `docs/phase-G/55-prereg-G-A017.md`, which
is published at commit `44ad1227` under tag `phase-G2-a017-prereg` and is NOT
edited. It is signed before any data is taken, so it changes a budget rather
than a result. It relaxes no gate on the claim; it splits one gate into the
two different claims it was silently serving.

## 1. The correction

Doc 55 gate `B-1` treats the nugget `v` as a single quantity and bounds it via
`sf >= 0.95`. That is too coarse, because `v` is a sum of sources with
different cross-link correlation:

    eps_l = q_l + c_l

    q_l   INDEPENDENT across links.   Var = v_q
          frame quantisation (each link's frame boundaries are unrelated),
          per-interface counter read jitter
    c_l   SHARED across links.        Var = v_c,  corr(c_l, c_m) = rho_c ~ 1
          machine-wide stalls, a shared telemetry collector

Substituting into the contamination formula:

    v      = v_q + v_c
    rho_eps = rho_c * v_c / (v_q + v_c)
    sf      = sigma^2 / (sigma^2 + v_q + v_c)

    bias = (1 - sf) * rho_eps
         = [ (v_q+v_c)/(sigma^2+v_q+v_c) ] * [ rho_c*v_c/(v_q+v_c) ]

    ★ bias = rho_c * v_c / (sigma^2 + v_q + v_c)

`v_q` appears ONLY in the denominator. Independent nugget therefore ATTENUATES
the bias rather than creating it. It cannot manufacture correlation, and more
of it makes the `omega` bias slightly smaller, not larger.

**G-L100:** a nugget budget must be stated per CORRELATION CLASS, not as a
total. Gating the sum `v` conflates an independent component that only
attenuates with a common component that contaminates, and therefore either
over-constrains the instrument or under-protects the claim. The quantity that
bounds claim A is `rho_c*v_c/(sigma^2+v)`, and the only measurement that reads
it directly is the cross-link correlation at `omega = 0`.

## 2. What this changes in the doc 55 budget

`B-1` is superseded by two gates that serve two different claims. Both are
signed here, before data.

| Gate | Quantity | Target | Limit | Derived from |
|---|---|---:|---:|---|
| B-1a | `sf = sigma^2/(sigma^2+v)`, total nugget | `>= 0.95` | `>= 0.90` | claim C, `sigma_hat/sigma = 1/sqrt(sf)`. Serves the `sigma` claim only |
| B-1b | `rho_c*v_c/(sigma^2+v)`, the contaminating part | `<= 0.10` | `<= 0.20` | claim A directly. Measured as `\|r_meas\|` at `omega = 0`, which IS this quantity |

`B-1b` is not a new requirement. It is the quantity doc 55's `B-1` was trying
to reach through a proxy, now measured directly.

## 3. Consequence for the `tau = 1 s` canary cell

`docs/phase-G/56-mutual-satisfiability.md` section 2.2 records that `T-2`
forces `dt = 0.05 s` at `tau = 1 s`, raising the quantisation floor and
leaving only a factor of 1.52 of `sigma` headroom. That figure was computed
against `B-1`, i.e. against the TOTAL nugget.

Under the decomposition, quantisation is entirely `v_q`. For claim A the
constraint disappears: `sigma_qfloor` does not enter the bias at all except in
the denominator, where it helps.

For claim C the constraint remains but is weaker. Requiring
`sigma_hat/sigma - 1 <= 0.10` uncorrected needs `v <= 0.21*sigma^2`, so with
`v_q = sigma_qfloor^2` at `dt = 0.05`:

    sigma >= sqrt(6.53e-5 / 0.21) = 0.0176
    headroom against the G.0 ceiling 0.0535 = 3.04x, not 1.52x

Moreover `v_q` has a CLOSED FORM, `v_q = (8L/(C*dt))^2/12`, in which every
term is known before the run. `sigma^2 = sigma_hat^2 - v_q` is therefore an
exact correction requiring no calibration branch.

The canary status of `tau = 1 s` is retained anyway, because the argument
above holds only while frame boundaries really are independent across links.
That is an assumption about the mechanism, and section 4 says how it is
tested rather than assumed.

## 4. What must be measured, not assumed

`rho_eps,quant ~ 0` requires that each link's frame boundaries be independent.
Under a per-link token bucket with its own phase this is expected, but expected
is not measured. `docs/phase-G/58-prereg-g2-kill-test.md` measures the pooled
quantity `|r_meas|` at `omega = 0`, which sums EVERY nugget source into one
number. If frame boundaries turn out to be coupled, that appears there.

## 5. What this amendment does not do

It does not relax any threshold on a claim. It does not reinterpret any
adjudicated result. It does not authorise a run; the kill test is authorised
by doc 58, separately and after this record is tagged. The estimator freeze of
doc 55 section 3 is unchanged, and `b(tau)` is unchanged.
