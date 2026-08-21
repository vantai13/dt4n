# 12 -- Lesson 23.7: conditioning va do nhay cua chan ly

Code: `cert/conditioning_audit.py`  
Artifact: `results/phase-23/conditioning_audit_*.json`  
Hinh: `results/phase-23/fig6_conditioning_audit.png`

## 1. Doi chung truoc khi doc cell giu kin

Pipeline tai lap Lesson 23.6: `c* = 0.453347031`, `c_F2 = 0.394852400`, `Delta = -0.012868850`; sai lech lon nhat `6.56e-10` (PASS).

M-16 duoc bao cao thanh CAP doi chung: NC23v2-8 = `0.923055`, PC23v2-3 = `0.727862`, nominal = `0.90`; cap nay `PHAN BIET DUOC`.

## 2. Bang cham 16 dong lop 3

| ID | Cell cham | Gia tri | KQ |
|---|---|---|:--:|
| M-4 | poisson@0.925, poisson@0.850, h2@0.700 | poisson@0.925=0.998970; poisson@0.850=0.998975; h2@0.700=0.994568 | MISS 0/3 |
| M-5 | poisson@0.925, poisson@0.850, h2@0.700 | poisson@0.925=[0.907212, 0.932194]; poisson@0.850=[0.895203, 0.919408]; h2@0.700=[0.901142, 0.936162] | MISS 1/3 |
| M-6 | poisson@0.850, h2@0.700 | poisson@0.850=0.139041; h2@0.700=0.076709 | MISS 1/2 |
| M-6b | poisson@0.850, h2@0.700 | poisson@0.850=0.881322; h2@0.700=0.991604 | HIT 2/2 |
| M-6c | poisson@0.850, h2@0.700 | poisson@0.850=0.119122; h2@0.700=0.008396 | HIT 2/2 |
| M-9 | poisson@0.850, h2@0.700 | poisson@0.850=0.036479; h2@0.700=0.053079 | MISS 1/2 |
| M-10 | poisson@0.925, poisson@0.850, h2@0.700 | poisson@0.925=0.000091; poisson@0.850=0.000071; h2@0.700=-0.000517 | MISS 0/3 |
| M-11 | poisson@0.850, h2@0.700 | poisson@0.850=1.642175; h2@0.700=1.091198 | MISS 1/2 |
| M-12a | poisson@0.925, poisson@0.850, h2@0.700 | poisson@0.925=0.274081; poisson@0.850=0.162519; h2@0.700=0.241834 | HIT 3/3 |
| M-12b | poisson@0.925 | poisson@0.925=CO | HIT 1/1 |
| M-13 | poisson@0.850, h2@0.700 | poisson@0.850=2.123575; h2@0.700=n/a | HIT 1/1 danh gia; NEUTRAL 1 |
| M-13b | poisson@0.850, h2@0.700 | poisson@0.850=0.916695; h2@0.700=0.000000 | MISS 0/2 |
| M-13c | poisson@0.850, h2@0.700 | poisson@0.850=0.763260; h2@0.700=n/a | HIT 1/1 danh gia; NEUTRAL 1 |
| M-14 | poisson@0.850, h2@0.700 | poisson@0.850=0.827402; h2@0.700=0.851461 | HIT 2/2 |
| M-15 | poisson@0.850, h2@0.700 | poisson@0.850=0.134359; h2@0.700=0.284635 | HIT 2/2 |
| M-16 | poisson@0.925 | poisson@0.925=0.727862 | HIT 1/1 |

## 3. Co che

M-4 dung doi chung `post_variant=none` van giu `z_bin`, nen no do dong gop rieng cua truc `m_hat_bin`. Doi chung qhat hang so toan cuc duoc bao cao rieng, khong dung de cham.

Trong phep bom residual, `y_hat` va tap accept giu nguyen; chi `y_true`, `a_star`, wrong, `c*`, `c_F2` va `Delta` duoc tinh lai. Vi vay phep do khong dua chan ly vao quyet dinh (khong ro ri oracle).

NC23v2-8 bom ca calib va test nen giu trao doi duoc. PC23v2-3 bom chi test trong khi qhat lay tu the gioi goc, nen co chu dich pha trao doi duoc. Day la sai lech he thong cua thuoc do, khong phai ket luan rang conformal prediction noi chung khong hoat dong.
