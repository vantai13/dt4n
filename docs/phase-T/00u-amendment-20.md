# AMENDMENT 20 -- Phase T / T.6g mechanism attribution

Ngay viet: 2026-08-03
Trang thai: T.6f da chay xong. Viet truoc khi chay T.6g Jensen check.

## Boi Canh

T.6f script tra ve `khong_phan_biet_duoc` vi quy tac AND yeu cau ca cot `a`
lan cot `tau_rho` cung ung ho co che dong luc. Danh gia lai cho thay quy tac
nay qua chat: cot `tau_rho` khong co luc thong ke de phu quyet cot `a`.

Ket qua T.6f:

```text
a=0.2  mean=-0.003380 +/- 0.017197 ms
a=0.9  mean=-0.062066 +/- 0.018067 ms
ratio |a=0.9|/|a=0.2| = 18.36

tau=0.2 mean=-0.018929 +/- 0.021678 ms
tau=1   mean=-0.029593 +/- 0.021705 ms
tau=5   mean=-0.049647 +/- 0.022164 ms
max pairwise tau |z| = 0.991
```

## Tinh Lai Cot `a`

Vi `sigma_rho` ty le voi `a`, ti so bien do giua hai nhom la:

```text
a_low / a_high = 0.2 / 0.9
```

Dung `a=0.9` lam moc du doan tai `a=0.2`:

```text
THIET BI sigma^0 : pred(a=0.2) = -0.06207 ms  -> bi bac bo boi a=0.2 ~ 0
DONG LUC sigma^1 : pred(a=0.2) = -0.01379 ms
JENSEN   sigma^2 : pred(a=0.2) = -0.00306 ms
```

Cot `a` bac bo offset thiet bi: mot chi phi moi goi cua bo sinh tai khong the
bien mat khi bien do `a` nho, vi vong lap van tra cuu `rho(t)`.

## Tinh Lai Cot `tau_rho`

Khac biet lon nhat theo `tau_rho` chi co `|z| = 0.991`. Do do cot `tau_rho`
khong du luc de ket luan theo bat ky chieu nao. Mot phep kiem khong du luc
khong duoc dung de phu quyet mot phep kiem co y nghia tren cot `a`.

## Quy Ket Tam Thoi

Hieu ung phu thuoc bien do `sigma_rho` nhung khong co phu thuoc `tau_rho` co
y nghia. Day phu hop voi so hang Jensen do do loi cua `f(rho)`, hon la sai so
tre hoi phuc theo `Lambda`.

Dieu nay nhat quan voi:

```text
D-T3 phang theo Lambda
I2 = 9.2% dong nhat qua 8 o
D-T4 dau am 8/8 o
D-T5 err_jensen dung dau 7/8 o
```

## T.6g -- Jensen Check

T.6g se so truc tiep `err_dyn` voi `err_jensen_ms` da tinh trong T.6.

Primary:

```text
group = (mode, rho_bar, a, tau_rho), cbr excluded
x = err_jensen_ms
y = err_dyn_ms
report corr(x,y), OLS y = alpha + beta*x, va slope qua goc.
```

Secondary sign-convention diagnostics:

```text
x = -err_jensen_ms
x = -(err_jensen_ms + d_sampling_ms)
```

Ly do: T.0 co cac thanh phan cong duoc, va dau cua dai luong Jensen co the
duoc dien giai theo phuong trinh `err_total = err_qs + err_jensen + d_sampling`.
Bao cao ca ba de tranh an chon quy uoc dau sau khi nhin ket qua.

## Du Doan Truoc Khi Chay

```text
G1. Primary corr(err_dyn, err_jensen) tren group se manh: |corr| >= 0.7.
G2. Mot trong ba quy uoc dau se co |slope| trong [0.5, 1.5].
G3. Quy uoc dau tot nhat se la quy uoc co |corr| lon nhat va slope cung bac 1.
G4. Neu primary fail nhung secondary pass, ket luan la "khop Jensen theo quy
    uoc dau/phan ra dai so", khong duoc goi primary la pass.
G5. Neu ca ba fail, ket luan T.6f chi duoc ghi la scaling theo `a`, chua quy
    ket Jensen dinh luong.
```

## Nguyen Tac Moi

NT-L23. Quy tac AND giua hai phep kiem chi hop le khi ca hai phep kiem co luc
thong ke du. Phep kiem duoi luc phai tra "khong ket luan", khong duoc phu quyet.

NT-L24. Khi kiem mot co che co nhieu quy uoc dau dai so, phai dang ky va bao
cao tat ca quy uoc dau truoc khi chay; khong chon dau dep sau khi thay ket qua.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-08-03
