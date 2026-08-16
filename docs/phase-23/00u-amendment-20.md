# AMENDMENT 23-20 -- Studentized max-score DoF lock

Ngay: 2026-08-16
Commit: truoc khi them `cert/studentized_score.py`.

Ly do: Phase 22 Amendment 1 da de lai thu tuc exploratory studentized
max-score nhung chua khoa het bac tu do. Truoc khi chay bat ky code Phase
23.5[A] nao, amendment nay khoa cac quyet dinh do va ghi ro cac du doan v1 bi
mau thuan voi artifact Phase 22 da commit.

## 1. Khoa 7 bac tu do D1--D7

D1. `sigma` theo tung Mondrian bin, khong dung sigma toan cuc cho ket qua
chinh. Ly do: qhat Phase 22 da theo `z_bin`; neu qhat theo bin nhung sigma
toan cuc thi hai lop dieu kien hoa khong khop. Sensitivity phu bao cao sigma
toan cuc ben canh, khong thay ket qua chinh.

D2. Chia fold mot lan, toan cuc, tren tap block cua calib; sau do moi loc theo
bin. Mot block phai nam tron trong fold1 hoac fold2 o moi bin. Ly do: chia
doc lap trong tung bin co the de cung block roi vao fold1 o bin nay va fold2
o bin khac, tao ro ri do tuong quan trong block.

D3. `n_eff` truyen vao `conformal_level` la so block cua fold2 trong bin, khong
phai so hang. Ly do: hieu chinh mau-huu-han cua split conformal duoc khoa theo
block doc lap.

D4. San sigma: `SIGMA_FLOOR = 1e-9`. Ly do: chan chia cho 0 o cell/bucket suy
bien; bao dam conformal van giu vi sigma la ham tat dinh cua fold1.

D5. Neu fold2 trong mot bin co it hon `MIN_BLOCKS_FOLD = 9` block thi raise
som. Ly do: `conformal_level` se tra `None`, qhat vo cuc va acceptance bang 0;
khong duoc im lang sinh artifact vo dung.

D6. Fold split: `FRAC_FOLD1 = 0.5`, `SEED_FOLD = 7001`. Seed nay khac
`SEED_SPLIT = 7000` cua calib/test split.

D7. NC-S-1 chi duoc so sanh voi maxscore tinh tren dung fold2, cung `n_eff` va
cung level. Khong so voi maxscore tinh tren toan calib, vi hai quantile co
finite-sample correction khac nhau.

## 2. Dieu chinh dai du doan

Bang nay giu nguyen dai v1 de bao cao MISS khi can. Dai v2 chi duoc dung lam
khung doc ket qua exploratory cua Phase 23.5[A].

| ID | Dai v1 | KQ v1 | Dai v2 | Nguon v2 | Can cu |
|---|---:|---|---:|---|---|
| S-5 `sigma3/sigma1` | 1.5-3.0 | MISS tren 3 cell khong suy bien | 1.05-1.50 | [MO TA] | `rms_scores` trong `results/phase-22/conformal_sim_*.json` |
| S-1 `c` | 1.15-1.30 | MISS ve thang do | 1.90-2.30 | [CO CHE] | `c ~= 1.495 * rms(v)`, `rms(v)` bi chan boi `rms(s_sim)/sigma_j` |
| G3a slot 1 | 0.92-0.98 | giu v1 de cham | 0.90-1.00 | [CO CHE] | chan dai so cho `qhat_stud_1/qhat_max` |
| G3b slot 2 | 0.98-1.02 | giu v1 de cham | 0.94-1.05 | [CO CHE] | tach slot 2 vi `sigma2 != sigma3` |
| G3b slot 3 | 0.98-1.02 | gan nhu chac MISS v1 | 1.00-1.12 | [CO CHE] | slot co sigma lon nhat co the rong hon maxscore |
| G23-27 / PC-S-1 | coverage drop > 0.02 | doi thiet ke | PC-S-1a/b/c | diagnostic | thien lech ro ri `O(p/n)` voi `p=3` nho hon do phan giai full data |

Ba cau bao ve liem chinh:

```text
1. Viec dieu chinh dai dua TOAN BO tren artifact Phase 22 da commit tai
   `0a3bea3` (rms_scores, bridge_to_rms). KHONG du lieu Phase 23 nao,
   KHONG output nao cua cert/studentized_score.py duoc nhin thay truoc
   khi ky amendment nay.

2. Nhan nguon cua S-5 ha tu [NGOAI SUY] xuong [MO TA]: dai luong nay suy
   ra duoc tu artifact cong khai, nen no KHONG tinh la du doan confirmatory.

3. Dai cu (1.5-3.0 / 1.15-1.30 / 0.92-0.98 / 0.98-1.02) duoc GIU NGUYEN
   trong bang duoi dang cot "dai v1", va duoc bao cao la MISS trong
   docs/phase-23/08. Khong xoa, khong viet lai lich su.
```

## 3. Thiet ke lai PC-S-1

PC-S-1 trong du lieu day du co `p=3` tham so sigma va khoang `2.5e5` hang
fold2, nen thien lech do ro ri xap xi `3 / 250000 ~= 1e-5`, nho hon nguong
0.02 da khoa. Vi vay khong duoc doc full-data PC-S-1 im lang la PASS.

Thiet ke moi:

```text
PC-S-1a  Che do it du lieu: lay mau con n_block = 20 moi bin, roi ro ri sigma.
PC-S-1b  Ro ri chieu cao: thay sigma 3 tham so bang sigma theo block.
PC-S-1c  Chia fold theo hang: doi chung manh cho vi pham exchangeability.
```

Bao cao full data:

```text
Voi p=3 va n lon, can thien lech do ro ri nam duoi do phan giai do. Chung toi
chung minh co che bang che do mau nho va bang vi pham exchangeability; full
data PC-S-1 la "khong phat hien duoc", khong phai PASS.
```

## 4. Ha cap cac gate da bi lesson truoc cham du lieu

Cac gate G23-8, G23-14, G23-15, G23-17, va G23-23 da duoc anh huong boi cac
artifact/diagnostic Phase 23 truoc do. Trong Lesson 23.5[A], chung chi duoc
doc la DIAGNOSTIC neu duoc nhac lai; khong tinh vao prediction-hit confirmatory
cua studentized max-score.

## 5. Pham vi duoc phep chay

Sau amendment nay moi duoc them code `cert/studentized_score.py`, test
`tests/test_phase23_studentized.py`, va sinh artifact:

```text
results/phase-23/studentized_poisson_0.925.json
results/phase-23/studentized_poisson_0.850.json
results/phase-23/studentized_h2_0.700.json
```
