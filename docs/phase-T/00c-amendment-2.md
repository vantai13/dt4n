# AMENDMENT 2 -- Phase T

Ngay: 2026-07-30
Trang thai truoc sua: `00-preregistration.md` + `00b-amendment-1.md`,
Phase T chua chay do.

Tai lieu kem: `docs/phase-T/01-two-timescales.md`.

## Da Thay So Nao Truoc Khi Sua

Audit T.1 doi chieu cong thuc RBM voi du lieu Phase L cho `bw=6,q=13`.
Ket qua:

```text
poisson: T_relax do / T_RBM = 1.06 .. 2.59
h2     : T_relax do / T_RBM = 1.13 .. 4.06
onoff  : T_relax do / T_RBM = 18.43 .. 24.97
cbr    : duoi nguong, inflation chu yeu do jitter phan mem;
         tai rho=1.00 do duoc 4.8..10.7 s va khong hoi tu sach
```

He qua: `inflation` khong du tin cay de lam `T_relax` cho truc hoanh
`Lambda = tau_rho/T_relax`.

Kiem thu luoi T.0 cho thay giai `sigma_rho` tu muc `J` tao nhieu o khong dat
o tai cao:

```text
9/27 o J-target khong dat vi sigma_rho vuot gioi han clamp
```

Kiem tra roi rac hoa OU:

```text
dt cu = 0.100 s
tau_rho_min = 0.2 s
T_relax_min ~= 0.020 s
```

`dt=0.100 s` cho canh bac thang cung bac voi thoi gian hang doi, nen co nguy
co do artefact roi rac hoa thay vi do OU lien tuc.

## Sua Gi

### A2.1. Doi `dt` OU

Cu:

```text
dt = 0.100 s
```

Moi:

```text
dt = 0.005 s
```

Ly do: quy tac thiet ke `dt <= min(tau_rho,T_relax_min)/5`. Chon 5 ms de co
do phan giai du so voi `T_relax_min ~= 20 ms` ma van lon hon thang gap goi
trung binh khoang 2.2 ms.

### A2.2. Doi cach chon `sigma_rho`

Cu:

```text
giai sigma_rho rieng cho J target in {0.1,0.5,2.0}
```

Moi:

```text
sigma_max = (1.05-rho_bar)/2.58
sigma_rho = a * sigma_max
a in {0.20, 0.90}
```

Ly do: cach cu tao lo hong luoi. Cach moi luon kha thi, khong co o bi clamp qua
1%, va van tao dai `J` rong khoang `0.07 -> 46`. `J` duoc tinh va ve lam truc
hinh, khong phai truc thiet ke.

### A2.3. Bo `tau_rho = 20 s`

Cu:

```text
tau_rho co the gom 20 s trong y tuong ban dau
```

Moi:

```text
tau_rho in {0.2, 1.0, 5.0} s
```

Ly do: cua so do 90 s khong du de gate sigma/tau pass co nghia o `tau=20 s`.
Luoi moi van phu `Lambda ~= 0.2 -> 55`, di qua vung chuyen tiep `1..10`.

### A2.4. Tach nhanh `cbr`

Cu:

```text
cbr co the quet nhieu rho_bar nhu h2/poisson
```

Moi:

```text
cbr chi chay rho_bar = 0.98 trong luoi chinh
```

Ly do: Phase L cho `cbr` duoi nguong gan phang o 0.14 ms; khong co tin hieu
Jensen/dynamic huu ich. Vung 0.98 moi co the cham transition quanh rho 1.0.

### A2.5. Them step response de do `T_relax`

Cu:

```text
T_relax suy tu inflation / batch means
```

Moi:

```text
do T_relax truc tiep bang step response
```

Thiet ke chot:

```text
h2/poisson: 0.70->0.85, 0.85->0.925, 0.925->0.98
T_hold=3 s, N=60 cycles, bin=20 ms, 3 seed
cbr: 0.95->0.98 voi T_hold=30 s; 0.98->1.00 voi T_hold=60 s, N=10
budget ~= 3.1 gio
```

Doc `T_relax` bang area method, fit exponential chi la kiem cheo.

### A2.6. Them `err_mol` vao T3

Cu:

```text
neu PSA fail thi Phase 20R chuyen MOL, nhung chua do MOL trong campaign
```

Moi:

```text
q_mol_load_ms = integral lambda(t) f(rho_tilde(t)) dt / integral lambda(t) dt
err_mol_ms    = q_bg_load_ms - q_mol_load_ms
gain_mol      = |err_qs| / |err_mol|
rho_tilde     = EWMA(rho, T_relax)
```

Ly do: `err_mol` la hau xu ly thuan, khong ton them Mininet. Neu PSA fail,
Phase T van ban giao duoc ban sua cu the cho Phase 20R.

## Bang Tien Doan Bo Sung

Them vao T5 cua `00-preregistration.md`:

```text
D-T10 MOL vuot PSA o vung dong: gain_mol > 2 khi Lambda < 3;
      gain_mol ~= 1 khi Lambda > 10; err_mol nguoc dau err_qs.

D-T11 T_relax step response: poisson khop RBM trong 3x; h2 lon hon RBM
      khoang 2-4x; cbr@rho=1.00 khong doc duoc trong 60 s.

D-T12 Hai co che tu phan tach theo rho_bar:
      rho_bar <= 0.85  -> err_jensen + d_sampling chi phoi
      rho_bar >= 0.925 -> err_qs dong chi phoi, J < 0.8
```

## Khong Sua

```text
bw=6 Mbps
q=13
mode chinh {h2, poisson}; cbr la nhanh rieng
seed chinh {11,12,13,14,15}
warm-up 15 s
cua so do 90 s
payload_bg=1470 B, frame_bg=1512 B
probe 64 B @ 20 pps, frame_probe=106 B
cam import twin.link_model v1 cho Phase T
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-30
