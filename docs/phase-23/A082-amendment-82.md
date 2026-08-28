# AMENDMENT 23-82 -- SNR o cell bao hoa: that hay artifact?

Ngay ky : 2026-08-28
Moc     : sau A081/23.25e, TRUOC khi chay T12
Loai    : TIEN DANG KY. Chi them artifact moi; T0..T11 KHONG doi.

## 1. Cau hoi

`SNR_dec` do tren `rho_measured` tai `clean@0.960` la 0.78..0.97, cao nhat
trong 5 cell. Cung cell do co 49% mau dung tran cung cua bo dem TX.
Cau hoi: SNR cao la TIN HIEU QUYET DINH, hay la HE QUA cua viec censoring
nen `sd(m)` manh hon nen `E[m]`?

## 2. Thiet ke

Tinh SNR tren HAI dau vao, cung `CostV2`, cung `mode=poisson`, cung
`w_loss=5000`, cung cell, cung run:

    (a) rho_measured  -- bo dem TX, BI chan tai tran cung 1.0094
    (b) rho_offered   -- so sach generator 10 ms, aggregate ve 200 ms,
                         KHONG bi chan boi hang doi

Dai luong quyet dinh: `R = median(SNR_measured / SNR_offered)` theo cell.

## 3. Du doan bang so (khoa truoc khi chay)

| ID | Dai luong | Dai ky |
|---|---|---:|
| M-275 | R tai clean@0.960 | 0.85 .. 1.30 |
| M-276 | R tai clean@0.700 (DOI CHUNG AM, khong censoring) | 0.95 .. 1.05 |
| M-277 | share mau bi clip tai RHO_MAX=1.05 tren nhanh offered, cell 0.960 | bao cao; khong cham |
| M-278 | Spearman(p_censored theo cell, R theo cell), n=5 | bao cao; khong cham |

## 4. Nhanh phu kin

M-276 MISS -> `load_offered()` aggregate SAI. DUNG TAT. Moi ket luan T11
              cua A081 phai treo cho den khi sua. Day la doi chung am; no
              hong thi khong doc duoc gi tu M-275.
M-275 HIT (R <= 1.30) -> SNR khong phai artifact censoring. D3 duoc thi hanh
              tren cell 0.960. Ghi G23-334 PASS.
M-275 MISS cao (R > 1.30) -> ★ SNR LA ARTIFACT. D3 KHONG duoc thi hanh tren
              cell 0.960. Chon cell theo quy tac muc 5.
M-275 MISS thap (R < 0.85) -> censoring dang GIAU tin hieu. Cell 0.960 con
              tot hon tuong, nhung `rho_measured` khong dung lam dau vao
              duoc; 23.26 phai doi dau vao (offered hoac OWD).

## 5. Quy tac chon cell cho 23.26 (khoa truoc)

Chon cell co `SNR_offered` CAO NHAT trong so cac cell co
`p_censored <= 0.20`. Neu khong cell nao dat, chon `clean@0.850`
va ghi ro rang thi nghiem chay o vung SNR thap.
KHONG duoc chon cell sau khi xem bang R.

## 6. Gate

G23-334  R tai 0.960 va doi chung am tai 0.700
G23-335  tran cung do duoc, ghi vao CONSTANTS.md, tinh lai p_censored
G23-336  NC: T0..T11 canonical hash khong doi
