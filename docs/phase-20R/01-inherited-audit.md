# INHERITED AUDIT -- Phase 20R

Ngay lap: 2026-08-04
Trang thai: viet truoc khi sinh `results/phase-20R/`. Khong sua nguoc Phase 20.

## Muc dich

Phase 20 da dong bang tai tag `phase-20-complete`. Audit nay ghi ro vi sao
`err = 0.187` va `d_sla = 0.081` chi con la phu luc v7, khong duoc
trich dan nhu ket qua khoa hoc cua Phase 20R.

Moi bang ben duoi duoc sinh lai bang:

```bash
python3 tools/audit_v1_vs_v2.py --write
```

Nguon so lieu: `twin/topology_v7.py`, `twin/link_model.py`,
`twin/link_model_v2.py`, `results/phase-L/link_model_v2_fit.json`, va
`results/phase-20/decision_error_offered.json`.

## Bang 1 -- link_model v1 -> v2 la sai so vi sai

```text
BANG 1 -- lech theo link tai LOAD_MEAN (mode=poisson)
link   bw   q   rho   |  v1_delay  v1_loss |  v2_delay  v2_loss | v2/v1
uA      8  18 0.8000 |     3.726  0.00000 |     5.525  0.00003 |  1.48x
uB      6  13 0.8200 |     3.770  0.00000 |     7.042  0.00085 |  1.87x
ac      6  13 0.9200 |     5.978  0.00000 |    11.733  0.00847 |  1.96x
ad      4  10 0.9300 |    24.470  0.00346 |    14.966  0.01775 |  0.61x
bc      6  13 0.9150 |     7.949  0.00000 |    12.469  0.00764 |  1.57x
bd      6  13 0.9250 |     5.994  0.00000 |    12.000  0.00936 |  2.00x
vC      8  18 0.8000 |     3.726  0.00000 |     5.525  0.00003 |  1.48x
vD      6  13 0.8300 |     4.739  0.00000 |     7.798  0.00114 |  1.65x
```

Ket luan: v2/v1 khong dong pha. Tai LOAD_MEAN, `ad` giam xuong 0.61x
trong khi `bd` tang len 2.00x. Do la differential error, khong phai
common-mode error.

## Bang 2 -- xep hang path bi doi

```text
BANG 2 -- xep hang path tai LOAD_MEAN (mode=poisson, w_loss Phase 20)
model rank path |  delay_ms     loss   cost_ms
v1    1 P1   |    13.431  0.00000    13.431
v1    2 P4   |    14.503  0.00000    14.503
v1    3 P3   |    15.445  0.00000    15.445
v1    4 P2   |    32.936  0.00346    37.955
v2    1 P1   |    22.783  0.00854    35.172
v2    2 P3   |    25.036  0.00852    37.401
v2    3 P4   |    26.840  0.01133    43.289
v2    4 P2   |    28.290  0.01891    55.729
```

Ket luan: thu tu `P3`/`P4` hoan vi khi thay v1 bang v2. Vi ranking la
doi tuong duoc do trong `P(argmin_twin != argmin_true)`, Phase 20 khong
the duoc ke thua nhu dap an that.

## Bang 3 -- nguong SLA cu nam duoi phan phoi v2

Nguong Phase 20 doc tu artifact:

```text
T_delay = 14.5138 ms
T_loss  = 0.01000
w_loss  = 1451.3766
opt_viol_rate = 0.1500
```

```text
BANG 3 -- nguong SLA Phase 20 duoi v2 (mode=poisson, rho dong nhat de lay can duoi)
rho_bar best |  opt_delay opt_loss | delay-T20 | delay_viol loss_viol | opt_viol
0.700   P1   |    15.348  0.00006 |   +0.834 | 4/4 0/4 | YES
0.850   P1   |    22.036  0.00255 |   +7.522 | 4/4 0/4 | YES
0.925   P1   |    31.779  0.01693 |  +17.265 | 4/4 4/4 | YES
0.980   P1   |    44.028  0.05736 |  +29.514 | 4/4 4/4 | YES
```

Ket luan: ngay ca o `rho_bar = 0.70`, delay toi uu duoi v2 da la
`15.35 ms`, cao hon `T_delay` cu `14.5138 ms`. Neu giu nguong cu,
`d_sla` bi mat do phan giai mot cach co hoc.

## Bang 4 -- Q7 phai sua rho_bar max

Offset dung: mean(LOAD_MEAN) = 0.8675; offset = LOAD_MEAN[link] - mean.

```text
BANG 4 -- chan doan clipping Q7 (sigma_rho=0.010, domain=[0.50,1.05])
rho_bar link mean | clip_low% clip_high% clip_total% | verdict
0.700   uA   0.6325 |    0.0000    0.0000     0.0000 | OK
0.850   ad   0.9125 |    0.0000    0.0000     0.0000 | OK
0.925   ad   0.9875 |    0.0000    0.0000     0.0000 | OK
0.980   ad   1.0425 |    0.0000   22.6627    22.6627 | REJECT
0.960   ad   1.0225 |    0.0000    0.2980     0.2980 | OK
```

Ket luan: `rho_bar = 0.98` lam link `ad` bi clip khoang 22.66%, qua lon
de coi la threat nho. Phase 20R chot `rho_bar max = 0.96`; khi do clip
xau nhat con khoang 0.30%.

## Hanh dong

1. Khong chay lai Phase 20.
2. Khong sua `results/phase-20/`.
3. Them erratum moi tai `docs/phase-20/99c-erratum-2.md`.
4. Phase 20R dung `link_model_v2` va pre-registration Q1-Q7.

## Ghi chu tinh

Shortest-hop tinh theo `base + serialization`: P1 = 12.040 ms ; P2 = 14.052 ms ; P3 = 13.544 ms ; P4 = 13.548 ms.
