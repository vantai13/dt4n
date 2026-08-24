# AMENDMENT 23-63 -- Hau kiem theo ho, clean replay, va semantics cua delta

Ngay ky : 2026-08-24
Lesson  : 23.21h-close
Loai    : HAU KIEM DA CONG BO + PROTOCOL TAI CHAY + DOI CHUNG DUONG
Moc     : sau artifact/commit `08b6879`, truoc clean replay

## 0. Disclosure

Amendment nay KHONG tien dang ky mot ket qua chua thay. Artifact
`live_region_sweep_slaB.json` va review doc lap da ton tai. Vi vay `M-180`
duoi day la **EXPLORATORY/POST-HOC**, khong duoc cham HIT/PASS va khong duoc
dem vao mau so du doan cua Lesson 23.21.

Trong luc kiem toan truoc khi ky, mot positive-control read-only tren
`poisson@0.900` da ep `F2b` thay `F2` va do duoc
`forced_F2b_minus_F2 = +0.012923831842096334`. Con so nay la PILOT DA XEM;
test sau chi la regression control cho wiring, khong phai bang chung ngoai
mau hay mot nguong tien dang ky.

## 1. M-180 -- cau truc theo ho (EXPLORATORY)

Nhom lai 12 cell theo `mode` cho mau mo ta:

```text
poisson LIVE      : gate hai 3/3
poisson non-LIVE  : gate giup 3/3
h2 LIVE           : gate giup 3/3
h2 non-LIVE       : giup 1, trung tinh 2
```

`gate giup` nghia la `delta_system_vs_neo < 0`; `gate hai` nghia la > 0.
Hinh se ve `rho`--`delta`, tach hai ho va to vung LIVE. No la hinh mo ta,
khong mang CI/p-value va khong bien 6 diem thanh mot phep kiem doc lap.

Can than voi cau `rho_hit=0.925`: `poisson@0.700` cung giup nhung TRIVIAL.
Phat bieu dung la **tren nhanh tai cao da phu `.850,.875,.900,.925`, dau
chuyen tu hai sang giup tai cell collapsed dau tien `.925`**; khong duoc viet
"gate chi bat dau giup o .925" tren toan truc.

## 2. Hai MISS va NT 51

M_57 va M_47b la hai mat cua cung mau theo ho, khong phai hai bang chung doc
lap. Phan loai cu "menh de dau song qua doi truc" da sai vi dai luong la
hieu cua hai ve cung phu thuoc objective theo hai duong khac nhau.

**NT 51 -- chan doan bat bien qua doi truc:** viet dai luong thanh cong
thuc va dem vi tri tham so truc. Mot gia tri qua phep bien doi don dieu co co
hoi giu dau/thu tu. Hieu/ti so co tham so xuat hien o hai ve khac nhau khong
duoc mac dinh bat bien; phai ky lai hoac ha thanh diagnostic.

M_54 duoc ha thanh `DIAGNOSTIC`. Dinh nghia code chi cam dau am quay lai sau
dau duong; voi ba am va mot duong, PASS ngau nhien co xac suat 1/4, chi 2 bit
thong tin. Them bon diem thanh 7 am + 1 duong chi cho 1/8 (3 bit). Muon 4 bit
trong cau hinh mot diem duong can it nhat 16 diem tong.

## 3. G23-228 -- clean replay

Artifact headline cu khai:

```text
git_hash  = cb8bd11...
git_dirty = true
```

Protocol da khoa:

1. Commit amendment + code instrument truoc.
2. Worktree tracked phai sach; CLI tu choi chay neu ban.
3. Chay lai tu parquet da ghim, khong build lai va khong doi threshold.
4. Artifact moi phai co `git_dirty=false`, `git_hash=HEAD` luc bat dau run.
5. So voi ban `08b6879`: ba cay `cells`, `metrics`,
   `live_definition_table` phai bit-exact; moi metadata/diagnostic moi duoc
   phep them, provenance timestamp/hash duoc phep doi.

Khong khop bat ky la so hoc nao -> G23-228 FAIL va dung dong lesson.

## 4. NC_H stress -- gioi han, khong doi gate sau khi xem

Eligibility da ky van la `calib_builder` voi `sigma=0.0096`; 4/4 PASS.
Nhanh stress dung `sigma_rho` cua SLA-regime FAIL 4/4:

```text
h2@.650  3.25x threshold       h2@.675   7.7x
p@.875  51.8x                 p@.900   63.3x
```

Delta headline duoc do tren parquet builder, nen noi suy dung cho phan phoi
builder. `sigma_rho` moi la bien thien cua che do van hanh ma artifact SLA
mo ta. Vi hai cell poisson lam M_47b MISS cung la hai stress nang nhat, khong
duoc ngoai suy MISS sang phan phoi SLA-regime neu chua chay sensitivity rieng.
Khong chay sensitivity trong dong lesson nay: dải/dau chua duoc tien dang ky
truoc khi review da thay nghi van.

## 5. L88 -- ten truong delta

`delta_system_vs_neo` la hieu risk cua he thong fallback (twin tren accept,
fallback tren reject) so voi neo (twin moi noi). Ve dai so no dung, nhung ten
de bi doc nham thanh phep tru truc tiep voi truong `err_neo`.

Giu khoa cu de tuong thich schema, them alias/metadata nghia ro:

```text
delta_fallback_vs_twin_weighted
  = reject_share * (err_F_given_reject - c_star_err_twin_given_reject)
```

Moi artifact headline phai khai `field_semantics`; tai lieu dung ten ro. Khong
doi mot gia tri so nao.

## 6. G23-229 -- family-selection positive control

Mau quan sat 12/12 `selected_minus_default=0` co hai giai thich: F6 trung F2
tren reject rows, hoac selected policy khong chay vao risk. Doi chung duong
ep mot family co action khac (`F2b`, constant P3) qua CUNG `_risk_summary` va
doi ket qua khac F2. PILOT da disclosure o muc 0; gate chi bao ve wiring.

Neu control khong doi delta, tat ca ket luan dung `calibration_selected` tu
Lesson 23.14 tro di phai audit lai. Neu control doi, ket luan hep la selection
duoc wired; viec F6=F2 o 12 cell nay la suy bien so, du lieu mo dau cho 23.22.

## 7. Output

```text
clean replay  results/LIVE/phase-23/live_region_sweep_slaB.json
comparison    results/RAW/phase-23/g23_228_clean_replay.json
figure        results/LIVE/phase-23/fig3_live_region_by_family.png
close doc     docs/phase-23/42-close-23-21.md
```
