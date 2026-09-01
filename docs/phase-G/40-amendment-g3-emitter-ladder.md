# G.3 emitter amendment — two-class estimator and CPU-sharing ladder

Signed: 2026-09-01 UTC, after `phase-G-g3-emitter-prereg` and before any
real-time benchmark result. Status: `CODE_ONLY_NO_BENCHMARK`.

This amendment replaces the assumed ten-distinct-CPU requirement. It preserves
sampler and UDP-sink isolation, but measures how emitter sharing affects common
deadline noise.

## Prospective two-class tau estimator

On the physical amplitude axis,

    sigma_rho,l = a0*sqrt(d_l)/C_l
    q_l         = wire_bits/(dt*C_l)
    sigma_pkt,l = sigma_rho,l/q_l
                = a0*sqrt(d_l)*dt/wire_bits.

Capacity cancels. The fixed topology has two design classes: degree one
`sigma_pkt≈1.984` and degree two `sigma_pkt≈2.806` at the stress amplitude.
For future physical analysis, before looking at network outcomes:

    degree 1 -> multi-lag corrected estimator
    degree 2 -> lag-2--3 corrected estimator

Neither branch uses the invalid white-round lag-1--2 estimator.

The proposed alternative threshold is not adopted. It defined relative lag-one
contamination as `v*c1/(T*acf1)` but its code computed `v*c1/T`. At the stress
cell the correct values are approximately `.00464` and `.00082`, not `.23` and
`.08`; a threshold `.10` would therefore select white-round for both classes
and restore known bias. The degree selector is topology-specific and derived
from the already completed A013 synthetic evidence; it is preregistered only
for future physical data.

## CPU dose-response ladder

The eight-CPU cpuset reserves its final two CPUs exclusively:

    sampler = CPU 6
    UDP sink = CPU 7

The first six CPUs form the emitter pool:

    L0: 8 emitters / 6 cores = 1.33 emitter/core
        map 0,1,2,3,4,5,0,1
    L1: 8 emitters / 3 cores = 2.67 emitter/core
        map 0,1,2,0,1,2,0,1
    L2: 8 emitters / 1 core  = 8.00 emitter/core
        map 0,0,0,0,0,0,0,0

Actual allowed CPU identifiers are sorted at runtime; the mappings above are
relative positions. Sampler and sink may never appear in an emitter mapping.

The independent-collision calculation is treated only as motivation. Packet
deadlines share an absolute window epoch and need not have independent phases,
so measured correlation remains the adjudicator.

## Replication and gates

A single 60 s trace has 300 windows and correlation sampling error about
`1/sqrt(300)=.058`. Taking the maximum over 28 link pairs makes a `.10` gate on
one trace unreliable. Therefore the ladder retains 16 replicates and centers
within replicate before pooling 4,800 windows per level.

Execution design:

- L0: 16 x 60 s at anchor and 16 x 60 s at stress;
- L1: 16 x 60 s at stress;
- L2: 16 x 60 s at stress;
- total wall-clock budget: approximately 64 minutes plus process startup.

The four existing gates apply to L0. In particular EMIT-3 requires L0 maximum
absolute off-diagonal deadline-lateness correlation `<=.10`. L1 and L2 form a
`REPORTED_DOSE_RESPONSE` curve; they do not receive post-observation pass
thresholds. EMIT-1 and EMIT-4 are also recorded by level, while only L0
adjudicates deployment on the current host.

The formal runner requires origin main and the annotated tag
`phase-G-g3-emitter-ladder-prereg` to equal local HEAD before execution.

## Lessons

**G-L83:** topology geometry can define a prospective estimator class, but a
selector must not reintroduce a known-invalid branch. Algebra and code for a
contamination score must agree numerically before a threshold is meaningful.

**G-L84:** a hardware constraint is an estimand when a gate already measures
its alleged failure mechanism. Preserve roles whose timing defines alignment,
then measure a dose-response curve for shareable workers instead of assuming
one core per worker.

Mininet remains prohibited until the L0 emitter gates pass.
