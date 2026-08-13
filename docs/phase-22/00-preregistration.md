# PRE-REGISTRATION -- Phase 22
# Chung nhan hop le cho QUYET DINH THAT (RQ-B2)

Ngay ky : 2026-08-13
Nguoi ky: vantai (Codex-assisted)
Tag du kien: phase-22-start
Revision 2: 2026-08-13, sau dry-run Lesson 22.1 tren du lieu TONG HOP sinh
tu `topology_v7`; chua cham bat ky artifact 21R/22 that nao.

Tien de: Phase 21R PASS tai tag `phase-21R-complete` (11 PASS / 1 PASS_MARGINAL).

Tai lieu bat buoc doc kem:

```text
docs/phase-21R/99-gate-decision.md          (L1-L10)
docs/phase-21R/00b..00i-amendment-1..8.md
docs/phase-22/01-inherited-audit.md         (L11, L12 -- PHAT HIEN MOI)
docs/phase-22/00b-amendment-1.md            (P3c, exploratory studentized max)
```

## Cau hoi cua phase

```text
Co the phat bieu mot chung nhan ve CHINH QUYET DINH DUOC TRIEN KHAI --
hop le dong thoi tren ca K hanh dong, hop le co dieu kien tren su kien chap
nhan, va hop le duoi AoI khong dong nhat -- ma van con HUU ICH khong?
```

Ket qua chinh KHONG phai mot con so. No la DUONG CONG risk-coverage theo
`kappa`, tren bon cau hinh C0/C1/C2/C3.

## Hai dai luong vi pham -- khong duoc tron

Moi lesson phai bao cao CA HAI cot, khong duoc gop:

| Dai luong | Marginal | Given accept (kappa=1, 21R) |
|---|---:|---:|
| Vi pham bao phu `P(s_margin > q_hat)` | 0.0913 | 0.1214 (lon hon alpha) |
| That bai quyet dinh `P(m_true < 0)` | 0.2135 | 0.0307 (nho hon alpha) |

Ly do cot thu hai tot hon cot thu nhat: tren tap accept ta biet
`m_hat >= q_hat`, ma that bai quyet dinh can `s_signed > m_hat >= q_hat`.
Day la nguong cao hon va chi mot phia. Do duoc:
`median(m_hat - q_hat | accept) = 7.617 ms`.

CAM viet: "conformal dam bao 90% tren tap duoc chap nhan."

DUNG viet: "bao dam bao phu la bao dam bien va khong tu dong chuyen sang tap
duoc chon (0.0913 -> 0.1214); tuyen bo van hanh van giu (0.0307 << 0.10)."

## Input da khoa (sha256)

| File | sha256 |
|---|---|
| `results/phase-21R/calib_set_poisson_0.925.parquet` | `6e089de6e3221083e75394750991f677eb5a5877fdbd4e2ccf4e33c89ed65c96` |
| `results/phase-21R/calib_set_poisson_0.850.parquet` | `8c75cbf884b44147786eb36ef0f2c043aedf63e4ff121bb94dba91e747965651` |
| `results/phase-21R/calib_set_h2_0.700.parquet` | `e425dba0df2d1106de1b67245106530eaa1d069c81bebcd726d9cff62eaf145c` |
| `results/phase-21R/calib_set_cbr_0.700.parquet` | `67c6ca2af2cc63bb75ac3216f2bbd79bf9850c12a908ac073bbdcabc9c0c8380` |
| `results/phase-21R/conformal_poisson_0.925.json` | `d707add38ae8cdfae1c97130193ca53e8b02f4edf2f25e3bfe3dd2b89075fcd5` |
| `results/phase-21R/usefulness_poisson_0.925.json` | `740238549007474daa61531131a2d8c8ab5f3ebac61230d484b666bb949751f7` |
| `results/phase-21R/decomposition_poisson_0.925.json` | `36ea4ac8fb66edd962d810846d99fc3ded4782775abfed7d515bef3cafd62b0e` |
| `results/phase-21R/anchor.json` | `2fe8afe7c360b141ce49f10075f3c4d38e1675784217db041a63f651bc668163` |
| `results/phase-20R/truth_table.parquet` | `5260b8f8aabb59ca81e2af1168bbbc98a7dfd804aa0506a266d0b34fac5d927e` |
| `results/phase-20R/sla_calibration.json` | `0387d300dbdd039c004a7fc89d062a0e9219968be8ad0cfeac65e53cf34826db` |
| `cert/margin_score.py` | `452f5840ecf867cde9690510ed0e49065c8c29de75c39b62c1a03377bd00b328` |
| `cert/build_calib_set_v2.py` | `c3852083439df64633e8a62faa6c8f588fca79d6eb833cf1430584244316f73c` |
| `cert/conformal_v2.py` | `c731149fc07f7d5a532d4d05619d62f1b04c24bc973b2ec1f090924e882ba43e` |
| `cert/usefulness_v2.py` | `2675cbaf58c9a2a8d24423ee5c7bd6b47a6160962eb5f372b7aa6146a39d2187` |
| `twin/cost_v2.py` | `ba591392e19ab6a10e10d6a45ec4782e83cb6516e2e616e54f744913ffd3bfab` |
| `twin/link_model_v2.py` | `17011990fa50c7d0c7155831cce475513684022c20b551440acead00ed1ef2a1` |
| `twin/topology_v7.py` | `c8263ce17feffdd17031dbcb3694880a4f649c6870068ce7a1f6631ec859076a` |
| `measurements/decision_error_v2.py` | `ff16f35cd1536d71f5d9f7c3d8b94052cd7db45cbff3a22e53ce22e57adc4533` |

## Canh bao ky luat

Cot `s_vs_a1` -- chinh la `s_sim` cua Phase 22 -- da ton tai trong
`calib_set_v2.parquet` tu Phase 21R. So headline cua Lesson 22.3 cach mot dong
code. Tai thoi diem ky, tac gia KHONG tinh bat ky phan vi nao cua cot do.
Bang chung: `git tag phase-22-start` dung truoc moi commit code Phase 22.

## Muoi ba quyet dinh -- chot, khong sua sau khi thay ket qua

### P1. Dai luong du doan

Giu nguyen tu 21R: `y_true = TruthTable(rho(t))`,
`y_hat = CostV2(rho(t-z))`. Tai su dung
`measurements/decision_error_v2.py::_cell_arrays`. Khong viet lai.

### P2. Score

```text
CHINH : s_sim(t) = max_{a != a1} |e(a) - e(a1)| (= s_vs_a1 cua v7)
PHU   : s_margin = |e(a2) - e(a1)|              (21R)
        s_pair_j = |e(a_j) - e(a1)|, j = 2,3,4 (Bonferroni/Sidak)
        s_signed = m_hat - m_true               (mot phia)
a1 chi duoc chon tu y_hat. Kiem bang inspect.signature (GS-1).
```

### P2b. Chi so cua ho so sanh

```text
Cot j danh theo HANG THEO TWIN (rank slot), khong theo danh tinh duong.
Cot 0 = a1 vs hang 2, cot 1 = a1 vs hang 3, cot 2 = a1 vs hang 4.
Ly do: slot theo hang dinh nghia duoc o moi hang va kha hoan doi; slot theo
danh tinh cho 12 nhom, nhieu nhom co the rong.
He qua ve phat bieu: bao dam la ve THU HANG THEO TWIN, khong phai ve mot cap
duong cu the. Phai viet dung trong luan van.
```

### P2c. Hieu chuan theo slot, khong gop

```text
Moi slot hieu chuan rieng, n_eff = so KHOI calib.
Khong gop 3 score trong cung mot hang vao pool 3n.
Ly do: 3 score trong cung hang phu thuoc do chung e(a1); gop lam phong n gia
tao, cung loai loi voi positive-control V3 cua Phase 21R.
```

### P3. Muc tin cay

```text
alpha = 0.10 cho bao dam dong thoi.
So so sanh = K - 1 = 3 vi moi khang dinh la hieu so voi a1.
Bonferroni : alpha/(K-1) = 0.033333
Sidak      : 1 - 0.9^(1/3) = 0.034512
Max-score  : hieu chuan s_sim o alpha, khong chia
```

### P3b. Hoa giai voi 21R G8 va MASTER_PLAN v8

```text
21R G8 va MASTER_PLAN dung alpha/K = 0.025 (K khoang rieng cho K hanh dong).
Phase 22 dung alpha/(K-1) = 0.0333 (K-1 khang dinh, deu la hieu voi a1).
Ca hai hop le; alpha/(K-1) chat hon.
Bao cao song song ca hai o Lesson 22.3 de dong chenh lech nay cong khai.
```

### P3c. Bridge half-normal la score-dependent

Them sau Lesson 22.3, xem `docs/phase-22/00b-amendment-1.md`.

```text
1.645*rms co the dung lam bridge ratio cho cung mot score.
Voi s_sim, chi bao cao qhat/(1.645*rms(s_sim)) de giai thich theo z-bin.
Khong dung bridge nay lam du doan absolute qhat confirmatory, va khong thay
qhat conformal bang proxy half-normal.
```

### P4. Che do

```text
CHINH : poisson @ 0.925   (sigma_rho = 0.0096, w_loss = 3222.24)
PHU   : poisson @ 0.850, h2 @ 0.700
PC    : cbr @ 0.700, poisson @ 0.700
Duong van hanh 10 o: Lesson 22.8.
```

### P5. Bin tuoi -- giu nguyen 21R

```text
CHINH  B0 [0.055,0.10)  B1 [0.10,0.20)  B2 [0.20,0.30)  B3 [0.30,0.550]
PHU    5 bin deu-so-mau (Z_EDGES_SECONDARY)
z dai dien cho tien doan ly thuyet: B0 -> 0.077, B3 -> 0.425
Khong chon bin moi.
```

### P6. Bin cho m_hat

```text
Chi dung o thu tuc Mondrian-theo-m_hat.
Phan vi cua m_hat tren tap calib, 4 bin deu-so-mau (Q1..Q4).
Ly do dung phan vi: m_hat bien thien 80x giua cac o.
Quy tac gop neu o giao rong: gop bin m_hat lien ke (Q1+Q2, Q3+Q4) truoc,
chi gop bin z neu van rong. Khong chon lai ranh gioi.
```

### P7. Chia calib / test

```text
block 5.0 s = 5*tau, chia 50/50 theo khoi, seed chia 7000.
Kiem chung doc lap theo seed: calib {101,102,103} / test {104,105}.
Doi chung duong V3 (chia theo hang) phai lam SD bao phu sup (< 0.5).
```

### P8. Tieu chi chap nhan

```text
accept <=> m_hat >= kappa * q_hat(z)
luoi kappa: {0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0}
diem co ten: kappa=0 neo, kappa=1 chung nhan, kappa=2 quy uoc v7
```

### P9. eps_regret

Giu nguyen P8 cua 21R: `0.10 * T_delay` theo o. Voi `poisson@0.925`,
`eps_regret = 3.2222 ms`. Anh xa sang kappa. Neu ra 0 thi bao cao C2 suy bien.

### P10. Diem neo

Tai su dung neo 21R (`err = 0.220835` khai bao, `0.222399` tren test) chi khi
thiet ke lay mau khong doi. Lesson 22.7 (AoI khong dong nhat) doi thiet ke,
nen phai tinh neo rieng cho tung ho so U0/U1/U2.

### P11. Ho so AoI khong dong nhat

```text
U0  dong nhat   : offset = [0,0,0,0,0,0,0,0] ms
U1  tuan tu deu : offset = [0,6,13,19,26,32,39,45] ms
U2  hai nhom    : offset = [0,0,0,0,25,25,25,25] ms
PC22-4 cuc doan : offset = [0,0,0,0,0,0,0,500] ms (chi de bat bug)
Thu tu link: (uA, uB, ac, ad, bc, bd, vC, vD).
z_bar giu nguyen o ca ba ho so bang cach bu offset trung binh vao d_sync.
Khong them ho so sau khi thay ket qua.
```

Ghi chu thuc thi Lesson 22.2: `dt = 5 ms`, nen offset thuc te bi luong tu hoa
ve boi so 5 ms. P11 khoa ho so danh nghia; artifact phai bao cao ca
`offset_ms_nominal`, `offset_steps`, `offset_ms_realised`, `link_order`, va
kiem `|realised - nominal| <= dt/2`.

### P12. Luoi tau

```text
tau in {0.5, 1.0, 2.0, 2.87, 5.0} s
2.87 la tau do duoc cua tai loi that.
Dai AoI giu nguyen [0.055, 0.550] de tach hieu ung tau khoi hieu ung dai.
```

### P13. Thu tuc diem bat dong

Thu tuc "Bonferroni tren su kien chon" khong duoc dung mot buoc. No tu tham
chieu: `q_hat` rong len thi `P(accept)` giam, `alpha'` nho di, roi `q_hat`
lai rong them.

```text
q_hat^0 = q_hat cua 21R (muc alpha)
lap i = 1..50:
    P_i      = ti le mau CALIB thoa m_hat >= kappa * q_hat^(i-1)
    alpha'_i = alpha * P_i / (K-1)      [C3]
               hoac alpha * P_i        [C2]
    q_hat^i  = phan vi conformal muc (1 - alpha'_i) tren tap tuong ung
    dung khi |q_hat^i - q_hat^(i-1)| / q_hat^(i-1) < 1e-6
Neu khong hoi tu: lay q_hat lon nhat trong 50 vong va bao cao khong hoi tu.
Neu P_i cham 0: bao cao suy bien, khong ngoai suy.
```

Quan sat dang ghi: thu tuc (a) va thu tuc (c) la hai diem bat dong cua cung mot
bai toan -- (a) lap tren muc alpha, (c) lap tren tap hieu chuan.

### D5. Sao chep co canh, khong refactor artifact da khoa

```text
Khong sua `cert/build_calib_set_v2.py` de tach logic chon hang vi v2 da la
evidence dong cua 21R. v3 duoc phep sao chep logic chon hang, nhung bat buoc
co V22-1 approval test: U0 shared columns phai khop artifact v2 bit-for-bit.
G22-2 duoc siết thanh max|diff| == 0.0 tren tat ca cot dung chung.
```

### D6. Khong luu z_s_per_link trong parquet

```text
Khong luu ma tran (n,8) `z_s_per_link`. Tuoi tung link suy ra duoc tu ho so
offset + sawtooth age, nen luu ma tran se tao du lieu du thua va co the mau
thuan. Metadata bat buoc gom offset_ms_nominal, offset_steps,
offset_ms_realised, va link_order.
```

### D7. Bin m_hat tinh sau split, chi tren calib

```text
Thu tu bat buoc: split theo block -> tinh canh m_hat tren CALIB -> gan bin cho
tat ca hang. Tinh canh tren toan bo du lieu la ro ri taxonomy vao test.
```

### D8. Pham vi cua P(accept) trong diem bat dong FCR

Them sau Lesson 22.4.

```text
CHINH: p_scope = "global"
       P(accept) do tren toan bo tap CALIB, bao dam P(viol|accept) <= alpha
       theo bien. Ly do: on dinh tren o chinh; ban per-bin sup do tai B3.

PHU:   p_scope = "per_bin"
       Bao dam manh hon neu ton tai, nhung khong kha thi tai poisson@0.925:
       B3 di vao trang thai hap thu P(accept)=0, q_hat=inf.

Gioi han dung luong huu han:
       FCR can P(accept) >= 1/(alpha*(n_eff+1)).
       Voi n_eff=500 va alpha=0.10, nguong la 0.01996.

Moi P(accept) dung trong fixed point phai do tren CALIB, khong do tren TEST.
```

### D9. He so nhan cua thu tuc thich ung khong phai mot so

Them sau Lesson 22.4.

```text
Voi FCR global, co the bao cao mot he so theo z-bin.
Voi Mondrian/selective/adaptive taxonomy, "he so nhan" la mot mang theo nhom.
Du doan sau nay phai noi ro he so cua nhom nao, hoac du doan hinh dang phan bo
he so. Khong duoc viet "he so nhan cua Mondrian" nhu mot so don.
```

### P15. Quy tac dinh danh du doan

Them sau Lesson 22.5.

```text
Moi dong trong bang du doan phai xac dinh day du:
  1. THU TUC nao: khong duoc viet "C3" chung chung neu C3 co nhieu post variant.
  2. NHOM/SLOT nao: khong duoc viet "he so nhan" chung chung.
  3. TAP HANG nao: calib/test, z-bin, m_hat-bin, score-level.

Neu mot lesson sau se chon giua nhieu thu tuc, bang du doan phai co mot dong
cho moi thu tuc, khong phai mot dong cho "thu tuc thang" sau khi nhin du lieu.
Du doan cau truc (hinh dang, thu hang, vung hong) phai duoc tach khoi du doan
mot con so.
```

### P16. Phan tich cong suat truoc khi du doan mot dau

Them sau Lesson 22.7.

```text
Truoc khi viet mot dong du doan dang "X > Y", "X < Y", hoac "ti so < 1",
phai uoc luong:
  1. do lon du kien cua hieu ung, uu tien tu mo hinh co che;
  2. san nhieu cua phep do, uu tien bootstrap / artifact truoc do.

Neu do lon du kien nam duoi san nhieu, khong duoc khoa du doan ve DAU.
Thay vao do khoa du doan ve CAN:
  "|ti so - 1| < epsilon o muc tin cay 95%"

Lesson 22.7 la vi du: Jensen du doan U1/U2 chi ~0.05-0.07% tren rms, trong
khi san nhieu qhat khoang 1%. Du doan dung phai la "khong co hieu ung lon hon
2%", khong phai "U1 < U0".
```

## Bang du doan -- dien truoc, doi chieu sau

| Dai luong | Du doan | Do duoc | KQ |
|---|---:|---:|---:|
| q_hat_Bonferroni(B0) / q_hat_21R(B0) | 1.28 - 1.33 | ______ | ___ |
| q_hat_Sidak(B0) / q_hat_21R(B0) | 1.27 - 1.32 | ______ | ___ |
| q_hat_maxscore(B0) / q_hat_21R(B0) | 1.22 - 1.30 | ______ | ___ |
| q_hat_maxscore / q_hat_Bonferroni | 0.94 - 0.98 | ______ | ___ |
| bao phu dong thoi (Bonferroni) | 0.90 +/- 0.02 | ______ | ___ |
| bao phu tung cai khi dung dong thoi | 0.955 - 0.975 | ______ | ___ |
| doi chung am: bao phu dong thoi, alpha | 0.74 - 0.80 | ______ | ___ |
| corr giua cac cot s_pair | 0.20 - 0.35 | ______ | ___ |
| vi pham sau chon loc, truoc sua | 0.115 - 0.130 | ______ | ___ |
| vi pham sau chon loc, sau sua (a) diem bat dong | <= 0.10 | ______ | ___ |
| vi pham sau chon loc, sau sua (b) Mondrian-m | <= 0.10 | ______ | ___ |
| vi pham sau chon loc, sau sua (c) selective | <= 0.10 | ______ | ___ |
| he so nhan q_hat cua (a) tai diem bat dong, C2 | 1.45 - 1.58 | ______ | ___ |
| he so nhan q_hat cua (b) Mondrian-m_hat | 1.05 - 1.15 | ______ | ___ |
| so vong hoi tu cua (a) va (c) | 3 - 12 | ______ | ___ |
| he so nhan q_hat C3 tai diem bat dong | 1.72 - 1.88 | ______ | ___ |
| acceptance C3 tai kappa=1 | 0.075 - 0.110 | ______ | ___ |
| acceptance C3 tai kappa=0.5 | 0.30 - 0.42 | ______ | ___ |
| acceptance C3 tai kappa=0.75 | 0.15 - 0.24 | ______ | ___ |
| err\|accept C3 tai kappa=0.5 | 0.045 - 0.075 | ______ | ___ |
| err\|reject / err\|accept tai diem tot nhat | >= 3 | ______ | ___ |
| ti so q_hat(B3)/q_hat(B0) tai tau=0.50 | 1.77 - 2.16 | ______ | ___ |
| ti so q_hat(B3)/q_hat(B0) tai tau=1.00 | 1.87 - 2.29 | ______ | ___ |
| ti so q_hat(B3)/q_hat(B0) tai tau=2.00 | 1.88 - 2.30 | ______ | ___ |
| ti so q_hat(B3)/q_hat(B0) tai tau=2.87 | 1.86 - 2.27 | ______ | ___ |
| ti so q_hat(B3)/q_hat(B0) tai tau=5.00 | 1.77 - 2.17 | ______ | ___ |
| dinh tinh: R(tau) hinh chuong, dinh tai tau ~1.55, khong don dieu | TRUE | ______ | ___ |
| co che: o cbr (A/rms_em nho) phai lech khoi 2.16 | TRUE | ______ | ___ |
| q_hat(U1)/q_hat(U0) | 0.95 - 1.00 | ______ | ___ |
| q_hat(U2)/q_hat(U0) | 0.96 - 1.00 | ______ | ___ |
| acceptance(U1) >= acceptance(U0) | TRUE | ______ | ___ |

Ghi chu: acceptance C3 tai `kappa=1` du kien co the fail nguong van hanh; ket
qua chinh la duong cong theo `kappa`, khong phai mot diem.

## Doi chung bat buoc

```text
NC22-1  K = 2 -> s_sim === s_margin, moi thu tuc dong thoi quy ve 21R
NC22-2  kappa = 0 -> moi thu tuc sau chon loc quy ve 21R
NC22-3  offset = 0 (U0) -> moi ket qua trung 21R trong 1e-9
NC22-4  twin = su that -> moi q_hat = 0, chap nhan 100%

PC22-1  cbr@0.700 -> q_hat ~ san do luong, chap nhan ~100%,
        va ti so q_hat(B3)/q_hat(B0) phai lech khoi 2.16
PC22-2  alpha khong hieu chinh cho K-1=3 -> bao phu dong thoi phai tut
        ve ~0.729 neu doc lap, cao hon neu tuong quan
PC22-3  chia calib/test theo hang -> SD bao phu phai sup (< 0.5)
PC22-4  offset = [0,0,0,0,0,0,0,500] ms -> phai khac ro so voi U0
        Test bat buoc: hai duong tinh (dich rho vs dich bang chi phi) trung
        nhau khi offset = 0 va khac nhau khi offset != 0.

V22-5   kiem chung doc lap theo seed: calib {101,102,103} / test {104,105}
V22-6   tai tao 21R: moi so cua cau hinh C0 phai trung artifact 21R
```

## Quy tac ba nhan -- thuc thi bang may

```text
Moi con so lay tu artifact phai kem ba nhan:
  1. THANG    : delay (ms) | cost (ms, da gom w_loss*loss) | chuan hoa
  2. MUC      : per-link | per-path | margin (cap) | simultaneous (K)
  3. TAP HANG : cua so nao, z nao, seed nao, calib hay test

Moi ham trong cert/ cua Phase 22 phai tra ve dict co khoa
`scale`, `level`, `rowset`. Test G22-14 kiem dieu nay.
```
