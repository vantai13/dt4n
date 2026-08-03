# PHASE T -- CLOSURE

Trang thai       : DRAFT_PENDING_DOI
Ngay lap draft   : 2026-08-03
Commit so lieu   : f91b4ad47684dc6429673480eb7a5c8c9b2135b0
Commit chot      : PENDING_FINAL_COMMIT_AFTER_DOI
Tag              : phase-T-closed (pending)
DOI (concept)    : PENDING_ZENODO_RESERVE
DOI (version 1.0): PENDING_ZENODO_RESERVE

---

## 1. MUC TIEU (MASTER_PLAN_v8)

> Sinh rho(t) tai lap duoc tu seed, va chung minh no khop dac trung
> thong ke da dat ra. (3 tuan, rui ro: ky thuat)

Phase T la phase cong cu. San pham cua no la dau vao cho Phase 20R.
No khong mang cau hoi nghien cuu rieng.

---

## 2. BANG GATE T

| Gate | Yeu cau | Ket qua | Artifact |
|---|---|---|---|
| T-G1 | Cung seed -> trace giong den tung bit | 324/324 trajectory_digest khop; 45/45 schedule_digest tinh khop | `results/phase-T/t7_gate_table.json`, `test_load_spec_frozen_digests.py` |
| T-G2 | sigma, tau khop muc tieu +/-10% | 48/48 thanh phan pass tren 270 dong regular, so voi ky vong giai tich | `results/phase-T/t7_gate_table.json` |
| T-G3 | c_a do va ghi cho moi trace | 324/324 co `ca_operational`; sd(z)=0.7436 | `campaign_state.json`, `control_state.json` |
| T-G4 | Trace goc co DOI | PENDING_ZENODO_RESERVE | Zenodo |
| T-G5 | rho_offered vs rho_measured dinh luong | mean=+0.000729, max\|.\|=0.008190, theo 4 muc tai | `results/phase-T/t7_gate_table.json` |

**Ket luan hien tai: 4/5 PASS local; T-G4 dang cho DOI.**
Sau khi dien Concept DOI va Version DOI hop le, Gate T du dieu kien dong 5/5.

### Ghi chu T-G2

So sanh dung la voi **ky vong giai tich duoi cua so huu han**, khong voi gia
tri thiet ke tho:

- `sigma_hat` chech am do tru trung binh mau -> `expected_sigma_hat()`.
- `tau_hat` tu lag-1 chech am, `E[r1] ~ phi - (1+3phi)/n`; khi `phi -> 1`,
  `ln()` khuech dai. Voi `tau=5`, `dt=0.005`, `n=21000`: ky vong khoang
  4.20 s, tuc lech -16% so voi thiet ke.

Bang bao cao ca hai cot `vs_thiet_ke` va `vs_ky_vong`. Gate dung cot
`vs_ky_vong`.

T-G2 gate tren 270 dong regular. 9 dong block `S` la diem canh lap lai cung
seed `999`, khong phai mau thiet ke doc lap. Neu can ca 279 dong main voi
sentinel duoc can theo so lan lap, ket qua la 47/48 do o `(rho=0.85, a=0.9,
tau=1.0)` bi seed `999` lap 9 lan keo lech. Day khong duoc dung lam gate
dac trung bo sinh.

### Ghi chu T-G3

`c_s` khong do tung trace: link da shaping, goi BG co dinh 1500 B, thoi gian
phuc vu tat dinh => `c_s = 0` theo cau tao. Ghi la hang so.

### Ghi chu: `kappa` Pareto trong T-G2 ban goc

Khong ap dung. `kappa` thuoc bo sinh cu `traffic_v7.py`. Phase T dung bon che
do `cbr / poisson / h2 / onoff` voi `c_a` la truc thiet ke thay cho `kappa`.

---

## 3. SAN PHAM BAN GIAO CHO PHASE 20R

| San pham | Duong dan | Trang thai |
|---|---|---|
| Bo sinh rho(t) tai lap bit-exact | `mininet/rho_spec.py` | Doc lap interpreter sau A12 |
| Bo sinh lich tai bit-exact | `mininet/load_spec.py` | 4 che do, digest khoa bang test |
| Mo hinh link do that | `results/phase-L/link_model_v2_fit.json` | Chuyen giao L->T da kiem: 9/9 o khong lech, max\|t\|=1.68 |
| Runner chien dich + cong QA | `measurements/t5_campaign.py`, `measurements/gate_specs.py` | 22 cong; mo hinh nhieu xac nhan nhieu lan |
| Artifact Gate T | `results/phase-T/t7_gate_table.json` | Local gates T-G1/T-G2/T-G3/T-G5 pass |

---

## 4. THREATS TO VALIDITY

1. **Drift giua phien.** 9 diem canh trong chien dich dai cho thay ha tang co
   drift nho nhung do duoc; cac so sanh phai dung block/baseline da ghi.
2. **Hai commit trong mot chien dich.** idx 0-126 tren `2eec098e`,
   127-278 tren `10dcd4d8` (Amendment 14). `git diff` xac nhan chi doi
   nguong, khong doi duong do.
3. **Offset thiet bi cong tinh.** Phase T do tre cao hon Phase L
   `15.8 +/- 2.3 us` moi goi. Do va hieu chinh (A13). Nguyen nhan: vong lap
   gui lam them viec moi goi.
4. **Bat doi xung loc `n_late`.** idx 0-126 loc bang 1e-3 co retry;
   127-278 loc bang 1e-2 (A14). Da chung minh bien loc khong tuong quan voi
   ket qua: `corr(n_late, ca_operational_z) = +0.003`, KTC 95% [-0.19,+0.20].
5. **San nhieu phep do.** `se_batch` 0.096-0.411 ms; `se_naive` thap hon
   6-11 lan do tu tuong quan hang doi. Moi ket luan ve do tre phai so voi
   `se_batch`.
6. **Do chech uoc luong dac trung.** `sigma_hat` va `tau_hat` deu chech am
   duoi cua so huu han. Da hieu chinh giai tich trong T-G2.
7. **`cbr` chi ton tai o `rho=0.98`.** Khong tach duoc anh huong cua mode
   khoi anh huong cua `rho` cho che do tat dinh.
8. **Baseline khoi C chi 5 seed/o.** Do chinh xac cua moi so sanh chua
   baseline bi gioi han boi khoi C, khong boi 279 diem khoi chinh.
9. **`c_s = 0` la gia dinh cau tao**, khong phai so do.
10. **Mo hinh nhieu `c_a` bao thu.** `sd(ca_operational_z) = 0.744` tren
    324 hang (ky vong 1.0 neu mo hinh chinh xac). SE giai tich cao hon do
    tan thuc te khoang 25% (phuong sai ~1.8 lan). Huong bao thu: giam fail
    gia, khong tao ket luan sai. Ket hop voi `mean(z) = +0.95` do o khoi C',
    mo hinh vua co do lech duong nho vua uoc luong thua do tan.
11. **Chinh sach mau cho T-G2.** 9 hang `block S` (sentinel, `seed=999`
    lap lai) bi loai khoi kiem phan bo vi khong phai mau doc lap. Neu tinh
    ca chung, T-G2 la 47/48 thay vi 48/48. Bao cao ca hai con so.

---

## 5. KET QUA PHU -- KHONG THUOC GATE T

Trong qua trinh chay chien dich T, mot loat phan tich ve xap xi quasi-static
da duoc thuc hien (T.6b - T.6h, Amendment 15-21). Chung **khong phuc vu gate
nao cua Phase T**.

Da dong goi tai `docs/phase-T/APPENDIX-quasistatic.md`, dong bang theo so lieu
o commit `f91b4ad`. Se duoc dung lam dau vao cho **Phase 21R** (phan ra
`e_model` / `e_staleness`). **Khong phan tich them cho den Phase 21R.**

---

## 6. QUYET DINH CHOT

Gate T local: **T-G1/T-G2/T-G3/T-G5 PASS**.
Gate T external: **T-G4 pending DOI**.

Buoc con lai de dong Phase T:

1. Upload artifact len Zenodo va reserve Concept DOI + Version DOI.
2. Dien hai DOI vao file nay.
3. Commit final, tao tag `phase-T-closed`, roi publish Zenodo.

Sau do sang **Phase 20R** -- decision error tren 4 che do van hanh
`(rho_bar, c_a)`, ground truth la so do that (RQ-A).

Nguyen tac moi rut ra trong phase nay: **NT-L10 .. NT-L22**
(xem cac amendment 12-21).
