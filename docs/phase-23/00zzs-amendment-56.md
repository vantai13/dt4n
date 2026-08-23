# AMENDMENT 23-56 -- dong Lesson 23.21: cao nguyen, bien kha thi, gioi han mat phang

Ngay ky : 2026-08-23
Tag     : amendment-56
Lesson  : 23.21e (dong)
Loai    : SUA PHEP KIEM + RUT PHAT BIEU + TIEN DANG KY
Prereq  : amendment-55 (`6df4c83`), Lesson 23.21d (`7a03dd4`)

## 1. `G23-173` phai duoc ap LAN THU BA va THU TU

```text
Lan 1  luoi T_loss tho: h2@0.925, h2@0.960 dinh o mut          DA AP
Lan 2  luoi cuc bo poisson@0.960 qua hep, dinh roi mut          DA AP (noi luoi)
Lan 3  h2@0.960 luoi cuc bo: CAO NGUYEN S = 1.0000 tren 9/16
       diem, trai T thuoc [0.21107, 0.31184] (he so 1.477),
       va cao nguyen CHAM MUT PHAI                              CHUA AP
Lan 4  dinh V nam TREN BIEN kha thi `sigma = sigma_max(rho)`
       o 13/14 gia tri `rho` do duoc                            CHUA AP
```

### Loi o cap PHEP KIEM, khong o cap du lieu

```python
# SAI -- hong khi co CAO NGUYEN
peak_at_grid_edge = int(np.argmax(curve)) in (0, len(curve) - 1)
#   `argmax` tra chi so DAU TIEN trong nhom bang nhau -> 7, khac 15 -> False
#   NHUNG gia tri cuc dai CO dat tai chi so 15 = mut phai.

# DUNG -- kiem GIA TRI o mut
mx = float(np.max(curve))
peak_at_grid_edge = (curve[0] == mx) or (curve[-1] == mx)
```

Co dang hoi *"chi so argmax co o mut khong"*; cau hoi dung la *"gia tri cuc dai
co dat tai mut khong"*. Khi co cao nguyen, hai cau cho hai cau tra loi khac nhau.

```text
QUYET DINH: sua co; them phat hien CAO NGUYEN:
  plateau      := so diem dat cuc dai > 1
  T_star       := None neu plateau HOAC peak_at_grid_edge
  T_star_range := [grid[dau], grid[cuoi]] neu plateau
```

Han che moi: `L63`.

## 2. Pham vi anh huong -- KHOANH CHINH XAC

```text
M-147  (do VI TRI)     : `h2@0.960` KHONG XAC DINH DUOC. `T*` nam dau do trong
                         [0.21107, >= 0.31184]; `log2` ty so dao dong tu -0.12
                         den -0.68. Loai khoi trung vi, bao cao RIENG.
                         `h2@0.925` chua co luoi cuc bo -> `G23-185`.

efficiency (do GIA TRI) : KHONG bi anh huong. Mau so cua `h2@0.960` la 1.0000 --
                         TRAN TUYET DOI cua `S_pivotal`, khong the cao hon.
                         `efficiency` khong can biet `T*` o DAU; no chi can
                         biet cuc dai BANG BAO NHIEU.
```

```text
=> Ket qua CHINH cua 23.21c/d (efficiency trung vi 0.9356, 7/8 >= 0.85)
   GIU NGUYEN. Chi phep do PHU (`M-147` tai mot cell) mat gia tri.
```

Phan biet dang nho: **cao nguyen pha VI TRI nhung khong pha GIA TRI.**

## 3. RUT phat bieu ve dinh `V`

```text
RUT : "V cuc dai o sigma TRUNG BINH (0.028-0.046)"
```

Do duoc tren mat phang:

```text
13/14 gia tri `rho` cho `V` DON DIEU TANG theo `sigma`, va `sigma*` luon
la gia tri `sigma` LON NHAT con kha thi:

  poisson@0.850   sigma* = 0.046   sigma_max = 0.05329
  h2@0.650        sigma* = 0.028   sigma_max = 0.03198
  poisson@0.800   sigma* = 0.072   sigma_max = 0.07267
  ...
Ngoai le DUY NHAT: h2@0.600, `V` GIAM theo `sigma` (0.2500 -> 0.2333).
```

`sigma = 0.046` trong nhu "trung binh" vi no nam giua luoi `[0.004, 0.072]`.
Nhung tai `rho` = 0.850 thi `sigma_max` = 0.0533, nen 0.046 la gia tri CUOI
CUNG con kha thi. Da nham *"giua LUOI sigma"* voi *"giua DAI sigma kha thi
tai rho do"*.

```text
THAY: "V tang DON DIEU theo `sigma` trong mien kha thi o 13/14 gia tri `rho`;
       cuc dai nam TREN BIEN `sigma = sigma_max(rho)`, tuc tai `a` = 1.0.
       VI TRI dinh `V` CHUA KEP DUOC."
```

Muon kep dinh `V` phai quet theo `a` (`a` thuoc {0.90, 0.95, 0.99}), khong
quet theo `sigma` -- vi bien di chuyen theo `rho`.

Han che moi: `L64`.

## 4. RUT phat bieu ve chieu truot cua mien song

```text
RUT : "khi sigma tang, mien song TRUOT sang rho cao hon o CA HAI ho"
```

Do duoc:

```text
h2       sigma 0.004 -> {0.600, 0.625, 0.650}    sigma 0.046 -> {0.700}   PHAI
poisson  sigma 0.004 -> {0.850}                  sigma 0.058 -> {0.750, 0.800} TRAI
```

Hai ho di NGUOC CHIEU nhau. Nhung mien KHA THI tu no la mot dai CHEO:

```text
sigma = 0.072  ->  CHI CON MOT gia tri rho kha thi trong luoi: 0.800
sigma = 0.058  ->  hai gia tri: 0.750, 0.800
sigma = 0.046  ->  bon gia tri
sigma <= 0.012 ->  ca muoi gia tri
```

```text
THAY: "Hai ho di NGUOC CHIEU. Nhung tai `sigma` cao chi con MOT DEN HAI cot
       `rho` kha thi, nen moi 'chieu truot' doc tu mat phang nay deu bi TRON
       voi hinh dang cua mien kha thi `sigma <= sigma_max(rho)`.
       KHONG tach duoc voi du lieu hien co."
```

```text
HE QUA BAT BUOC: HINH 2 phai ve duong `sigma_max(rho)` CHONG LEN mien song.
                 Khong co no, hinh noi doi mot cach thuyet phuc.
```

Han che moi: `L65`.

## 5. `S_pivotal` suy bien khi `sigma` -> 0 -- toa do cu the cua cam bay `L55`

Khi `sigma` -> 0, `rho` tat dinh => `loss` moi duong tat dinh =>

```text
S_pivotal -> 1  neu  loss_min(rho) <= T_loss < loss_max(rho)
S_pivotal -> 0  nguoc lai
```

Khong phai "tien toi 1". La **0 HOAC 1**, khong co gia tri giua. No suy bien
thanh mot HAM CHI BAO cua viec nguong co roi vao giua hai duong hay khong --
zero thong tin ve viec quyet dinh KHO hay DE.

Kiem duoc tu `V` tai `sigma` = 0.004:

```text
h2@0.600        S_pivotal = 1.0000   V = 0.25000  chinh xac = 1/4
poisson@0.850   S_pivotal = 1.0000   V = 0.25004
```

`V` = 1/4 chinh xac nghia la dung MOT trong bon duong vi pham, TAT DINH, moi
buoc thoi gian. Thu tu cac duong KHONG BAO GIO doi.

```text
=> `L55` khong con la mot canh bao ly thuyet. No co TOA DO: mien `sigma` -> 0.
   O do `S_pivotal` = 1.0 -- cao nhat co the -- va quyet dinh HOAN TOAN tam
   thuong. Ai chung nhan bang `S_pivotal` mot minh se chung nhan dung o do.
```

## 6. Du doan -- DIEN TRUOC KHI CHAY

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-161 | `h2@0.925` luoi cuc bo: `T*` co KEP DUOC khong | CO CHE | KHONG (cao nguyen hoac mut) | | |
| M-162 | `efficiency(h2@0.925)` sau luoi cuc bo | NGOAI SUY | thuoc [0.80, 0.95] | | |
| M-163 | do rong cao nguyen `S = 1.0` cua `h2@0.960` (he so `T`) | NGOAI SUY | >= 1.8 | | |
| M-164 | quet `a` thuoc {0.90, 0.95, 0.99}: `V` co tiep tuc tang toi `a` = 0.99 | CO CHE | CO | | |
| M-165 | so cell doi nhan `regime` khi `a`: 0.90 -> 0.99 | NGOAI SUY | <= 4 | | |
| M-166 | `M-147` trung vi sau khi loai cell KHONG XAC DINH | CO CHE | <= 0.30 | | |

Ghi chu:

```text
M-161  da ky "KHONG" co chu dich: neu no KEP DUOC thi cao nguyen cua
       `h2@0.960` la ngoai le chu khong phai quy luat, va `L63` yeu di.
M-163  cao nguyen hien tai trai he so 1.477 NHUNG cham mut phai, nen 1.477
       la CAN DUOI. Da ky >= 1.8 tuc du doan no con rong hon khi noi luoi.
M-164  neu `V` KHONG con tang toi `a` = 0.99 thi dinh `V` nam TRONG mien,
       va muc 3 phai viet lai.
```

## 7. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-183 | co `peak_at_grid_edge` kiem GIA TRI o mut, khong kiem chi so `argmax` | bat buoc |
| G23-184 | phat hien CAO NGUYEN -> `T_star = None` + `T_star_range` | bat buoc |
| G23-185 | luoi cuc bo cho `h2@0.925` (cell cuoi cung con o mut) | bat buoc |
| G23-186 | quet `a` thuoc {0.90, 0.95, 0.99} de kep dinh `V` tren bien kha thi | bat buoc |
| G23-187 | HINH 2 phai ve duong `sigma_max(rho)` chong len mien song | bat buoc |
| G23-188 | `M-147` bao cao KEM so cell tham gia va so cell KHONG XAC DINH | bat buoc |
| G23-189 | doi chung duong: gia mot cao nguyen -> `G23-183`/`G23-184` phai DO | do it nhat 1 lan |

## 8. Han che moi

```text
  L63  Co `peak_at_grid_edge` kiem chi so `argmax` nen MU voi CAO NGUYEN:
       `h2@0.960` co 9/16 diem cung dat 1.0000 va cao nguyen cham mut phai,
       nhung co bao `false`. Loi o cap PHEP KIEM, khong o cap du lieu.
  L64  Dinh `V` nam TREN BIEN kha thi `sigma = sigma_max(rho)` o 13/14 gia tri
       `rho`; chua kep duoc. Phat bieu ve VI TRI dinh `V` bi RUT cho toi khi
       co quet theo `a`.
  L65  Chieu truot cua mien song theo `sigma` bi TRON voi hinh dang mien kha
       thi: tai `sigma` = 0.072 chi con MOT cot `rho` kha thi (0.800).
       Khong tach duoc voi du lieu hien co.
```

## 9. Dieu KHONG lam

```text
- KHONG rut ket qua chinh (efficiency): cao nguyen pha VI TRI, khong pha GIA TRI.
- KHONG doi `PIVOTAL_MIN`, `VIOL_OPT_BAND`, hay bat ky nguong da ky nao.
- KHONG tinh lai `M-135`, `M-138`, `M-147` cho cac cell KHONG bi anh huong.
```

So ke tiep: `L66`, gate so 190, `M-167`, `K08`.
