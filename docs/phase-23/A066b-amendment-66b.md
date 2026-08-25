# AMENDMENT 23-66b -- sua `NC-3`: bat bien thang can UOC LUONG LAI `qhat`

Ngay ky : 2026-08-25       <-- van TRUOC khi viet `cert/transfer_matrix.py`
Lesson  : 23.22 Task B
Loai    : SUA MOT DOI CHUNG DA KY (truoc khi chay)
Moc     : sau `3b9870b` (`A066`)

## 0. Vi sao co amendment nay

`A066` muc 5 dinh nghia `NC-3` la "nhan doi thang (`m_hat`, `s`) x2 tren cell
TRIEN KHAI" voi du doan "acceptance cua C3 KHONG DOI". Khung code di kem
nhan thang cua `test_B` roi cham voi `qhat_A` GIU NGUYEN.

**Hai dieu do mau thuan nhau.** Voi `qhat` giu nguyen:

```text
chap nhan <=> lambda*m_hat >= kappa * qhat_A
```

ve trai nhan `lambda`, ve phai dung yen -> acceptance TANG. Do duoc tren mot
mo phong 1000 hang (`kappa = 0.5`, `alpha = 0.05`):

```text
acceptance goc                        0.326
(a) uoc luong lai qhat tren du lieu    0.326   TRUNG BIT   (qhat2 == 2*qhat)
    da nhan doi
(b) mang nguyen qhat cu sang           0.664   khong trung
```

`NC-3` nhu da ky chay theo (b), nen no se **TRUOT chinh du doan cua no vi ly
do LAP TRINH, khong phai vi co che**. Mot doi chung ma ket qua am cua no
khong noi gi ve gia thuyet thi khong phai doi chung.

Phat hien khi kiem so hoc TRUOC khi viet module, nen chua mot dai luong Task B
nao duoc sinh ra. Tinh mu cua `M-190`, `M-194`, `M-195`, `M-196` KHONG bi
anh huong.

## 1. Menh de duoc phat bieu chinh xac lai

Bat bien thang KHONG phai tinh chat cua "luat da hieu chuan mang nguyen sang".
No la tinh chat cua **THAM SO DUOC CHUYEN GIAO**:

```text
C3  tham so chuyen giao la `kappa`  -- KHONG THU NGUYEN.
    `qhat` khong duoc chuyen giao: no la mot THONG KE cua phan phoi trien
    khai, uoc luong lai tu chinh du lieu do. Khi thang gian lambda,
    `qhat -> lambda*qhat` TU DONG, va `kappa` van dung.

B2  tham so chuyen giao la `c`     -- CO THU NGUYEN (cost_ms).
    Khong co "thong ke nao do cua B" ma `c` la; muon co `c` moi phai giai
    lai bai toan tim kiem tren mot tieu chi, tuc phai biet dich.
```

Do la ly do menh de o `A066` muc 1.2 van dung, nhung no noi ve CACH mot luat
duoc mang di, khong phai ve mot phep bien doi tren dau ra.

## 2. `NC-3` duoc tach lam HAI nhanh

```text
NC-3a  BAT BIEN CO UOC LUONG LAI   (kiem CO CHE)
       Nhan CA calib va test cua cell duong cheo x2, roi HIEU CHUAN LAI C3
       tren calib da nhan. Tham so chuyen giao la `kappa`.
       Du doan: acceptance cua C3 TRUNG BIT voi ban goc (lambda = 2 la luy
       thua cua 2 nen phep nhan chinh xac trong dau phay dong; `conformal_level`
       chi phu thuoc `n_eff` va `alpha` nen KHONG doi; `empirical_qhat` la
       mot thong ke thu tu nen gian dung lambda).
       B2 mang nguyen `c` do tren cell CHUA nhan -> acceptance DOI nhieu.

NC-3b  MANG NGUYEN, KHONG HIEU CHUAN LAI   (kiem KY VONG)
       Nhan thang cua test x2, giu `qhat_A` va `c` nhu cu.
       Du doan: CA HAI deu doi. C3 KHONG bat bien o che do nay.
       Muc dich: chan chinh ta khoi doc `NC-3a` thanh "C3 mien nhiem voi doi
       che do". No khong mien nhiem; no chi CHUYEN GIAO DUOC bang mot tham
       so khong thu nguyen.
```

`NC-3b` la nhanh ma khung code goc thuc su thuc hien. No duoc giu lai, nhung
voi du doan DUNG.

## 3. Anh huong toi khoi chinh (30 o GIUA HO)

Ma tran chinh cham C3 voi `qhat_A` mang nguyen sang B (khong hieu chuan lai) --
tuc che do `NC-3b`. Nen:

```text
`M-194` KHONG duoc doc nhu "C3 bat bien con B2 thi khong".
        Ca hai tham so mang di deu co thu nguyen o che do nay. Cai `M-194`
        do la mot cau hoi THUC NGHIEM: cai nao troi it hon, va bao nhieu lan.
        Nhan [NGOAI SUY] cua no o `A066` muc 4 la DUNG va duoc giu.
```

`A066` muc 4 da ghi `M-194` la `[NGOAI SUY]`, khong phai `[CO CHE]`, nen
khong mot du doan da ky nao phai doi. Amendment nay chi cam mot CACH DOC.

## 4. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-255 | `NC-3a`: nhan doi CA calib va test roi hieu chuan lai -> acceptance C3 TRUNG BIT (sai khac dung bang 0.0); acceptance B2 doi > 0.05 | tat/bat |
| G23-256 | `NC-3b`: nhan doi rieng test, giu `qhat_A` va `c` -> CA HAI doi > 0.05. Chan cach doc "C3 mien nhiem voi doi che do" | tat/bat |

`G23-255` giu ma cu nhung noi dung duoc phat bieu lai (no dang `NOT_RUN`,
chua co bang chung nao de mau thuan). `G23-256` la ma moi.

## 5. Pham vi anh huong

```text
KHONG doi `M-190`, `M-193`, `M-194`, `M-195`, `M-196` -- van mu.
KHONG doi diem van hanh `kappa = 0.5`.
KHONG doi `NC-1`, `NC-2`.
Chua mot dong `cert/transfer_matrix.py` nao duoc viet khi ky.
```
