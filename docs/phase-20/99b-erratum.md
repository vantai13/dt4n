# ERRATUM - Phase 20

Ngay: 2026-07-28
Trang thai: Phase 20 da dong bang tai tag `phase-20-complete`; khong sua nguoc.

Tai lieu nay ghi cac sai lech phat hien sau khi dong bang Gate 20. Cac muc nay
khong thay doi ket luan Gate 20, nhung phai duoc bao cao de Phase 21 tro di
khong ke thua tham chieu mo ho.

## E6. Kich Thuoc Goi Hieu Chuan Khac Kich Thuoc Goi Thi Nghiem

Phat hien:

```text
measurements/calib_link_sweep.py dung iperf -l 1470
mininet/flow_engine.py mac dinh --payload-bytes 1400
OVERHEAD_FACTOR = 1.0790 duoc fit o 1470 B
```

Dinh luong:

```text
overhead co dinh X = 1470 * 0.0790 = 116.1 byte/goi
gia tri dung cho 1400 B: F' = (1400 + 116.1) / 1400 = 1.0829
vi tri bao hoa: 1 / 1.0790 = 0.92678 -> 1 / 1.0829 = 0.92341
lech = 0.00337 = 0.34 sigma
MTU_BYTES: 1512 (=1470+42) -> 1442 (=1400+42)
tran hang doi bi thoi phong 4.85%
```

Phan loai: threat to external validity, vi cau hoi la mo hinh co dai dien dung
testbed hay khong. Khong lam mat internal validity cua phep do decision error:

```text
err = P(argmin c_hat != argmin c)
```

Trong Phase 20/21, `c_hat` va `c` duoc ve bang cung `link_model`, nen sai lech
hang so payload la common-mode doi voi phep do noi bo.

Hanh dong:

```text
Khong chay lai Phase 20.
Ghi quy tac sensitivity truoc khi chay tai docs/phase-21/05-sensitivity.md.
Phase 24 tro di: dat --payload-bytes 1470 neu muon khop truc tiep voi hieu chuan.
```

## E7. `CRITICAL_CEILING_FRACTION = 0.71` Do O Dung Mot Diem

Phat hien: hang so nay duoc suy tu mot diem:

```text
bw = 4 Mbps, q = 13, rho = 0.930
X/Q = 8.91 / 13 = 0.685
```

Mo hinh hien tai ap dung no cho toan bo dai:

```text
rho in (0.9250, 0.9325)
```

Ba cau hinh `(bw, q)` dung trong `topology_v7` chua tung do truc tiep:

```text
(8,18), (6,13), (4,10)
```

Dinh luong tu du lieu da co: chiem dung that trong dai toi han la mot duong
cong doc, khong phai bang phang. Luat random-walk phan xa:

```text
E[X]/Q = 1 / (1 - exp(-theta)) - 1 / theta
theta = 3753 * (rho - 0.93006)
R2 = 0.9852 tren 3 diem do
```

Sai so cua xap xi hang so 0.71 theo ngoai suy luat tren:

```text
rho ~ 0.925-0.929: co the thoi phong delay toi +25.8 ms
rho ~ 0.932      : co the thieu khoang -6 ms
```

Day khong phai common-mode: cac link o `rho` khac nhau nhan sai so khac nhau,
nen co the lat `argmin` va anh huong truc tiep `err`, `q_hat`, va duong bien.

Luu y trung thuc: vung `rho in [0.925, 0.929]` chua co diem do nao; cac con so
tren la ngoai suy, nen can chien dich do rieng.

Hanh dong:

```text
Buoc 2 se do quet dai toi han. Khung tai lieu: docs/phase-21/06-critical-band.md.
Khong thay doi link_model trong erratum nay.
```

## E8. HTB Va Netem Tren Cung Interface

Mininet `TCLink` mac dinh dat shaping HTB va delay/queue netem tren cung
interface. Tai lieu IPMininet canh bao cach nay co the lam nhieu tinh toan
shaping cua HTB.

Anh huong quan sat duoc da duoc `link_model` dien giai dung:

```text
backlog o tai thap bang BDP/netem occupancy, khong phai hang cho that
NETEM_OCCUPANCY_COEF duoc ghi vao rev5
```

Huong anh huong con lai chua danh gia. Thiet ke sach hon cho do lai sau nay la
tach shaping va netem sang hai interface.
