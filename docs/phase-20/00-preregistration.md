# PRE-REGISTRATION - Phase 20: Kill-test kha thi (RQ-A)

Ngay ky    : 2026-07-26
Git tag    : phase-20-start
Nguoi ky   : vantai13
Trang thai : CHOT. Moi sua doi sau ngay ky phai tao file
             `00b-amendment-N.md`, ghi ro SUA GI, VI SAO, va DA THAY SO
             NAO truoc khi sua.

## 0. Chuyen Huong Tu Phase 14B

14B tra loi: tren twin don / cac duong doi xung, periodic la toi uu, va
periodic cung la AoI-optimal.

Phase 20 khong co chinh sach, khong co ngan sach, khong co RL. Phase nay chi
la phep do mo ta: khi twin sai, controller co chon sai khong, va sai do dat
bao nhieu theo SLA.

Khong dung `reward3.py` tu Phase 20 tro di. Ly do: `R_ARRIVED` va
`DELAY_CLIP` la hien vat cua bai toan RL. `DELAY_CLIP` cat o 20 ms trong khi
vung qua tai do duoc cua `twin.link_model` la 21.608-29.208 ms, nen no lam
phang dung vung can do.

## 1. Co Che Da Phan Tich Truoc Khi Do

`twin/link_model.py` la ham bac thang, khong phai ham doc lien tuc. Tu
`twin.link_model` voi link co chai `base_delay=3.0 ms`, `bw=6 Mbps`,
`queue=13 pkts`:

| rho offered | delay ms | loss |
|---:|---:|---:|
| 0.8000 | 5.590 | 0.0000 |
| 0.8800 | 5.849 | 0.0000 |
| 0.9200 | 5.978 | 0.0000 |
| 0.9250 | 5.994 | 0.0000 |
| 0.9255 | 21.608 | 0.0000 |
| 0.9300 | 21.608 | 0.0035 |
| 0.9325 | 29.208 | 0.0061 |
| 0.9600 | 29.208 | 0.0346 |
| 0.9900 | 29.208 | 0.0639 |
| 1.0400 | 29.208 | 0.1089 |

Nguong nhay:

```text
J = {0.9250, 0.9325}
queue_ceiling(6 Mbps, 13 pkts) = 26.208 ms
delay jump tai 0.9250: +15.6 ms
delay jump tai 0.9325: +7.6 ms
```

He qua: cong thuc cu

```text
r(s) ~= (cost_2nd - cost_best) / (2 * |d cost / d rho|)
```

khong dung duoc cho Phase 20, vi dao ham bang 3.2 hoac 0 o hau het moi noi,
va vo cuc chi tai hai diem co do do bang khong.

Dinh nghia duoc dung thay the:

```text
r_jump(s)   = min over path a, over j in J of |rho_a - j|
r_smooth(s) = (cost_2nd - cost_best) / (2 * 3.2)
r(s)        = min(r_jump(s), r_smooth(s))
```

Du doan co che, ky truoc khi do:

```text
P1 err(z) tang don dieu theo z.
P2 err(z) bao hoa khi z lon.
P3 >= 70% loi quyet dinh xay ra khi r_jump(s) < 0.01.
P4 ti le tie |delta cost| < EPS nho hon 20%.
```

Neu P1 sai, kiem tra thuoc do va dai tai truoc khi dien giai. Neu P3 sai,
co che trong paper phai viet lai; day van la ket qua co gia tri.

## 2. Gia Thuyet

H1, kiem dinh chinh tai bin tuoi da chot:

```text
err(z*) in [0.05, 0.40] va Delta_sla_lower(z*) >= 0.03
```

H2, kiem dinh co che tren toan duong cong:

```text
err(z) tang theo z: Spearman rho_s > 0 voi p < 0.05
```

Moi `z != z*` duoc bao cao la exploratory, khong dung de quyet gate. Ly do:
"ton tai mot z trong 7 bin" la lay max tren nhieu bin, dung loi winner's curse
ma Phase 14C da phat hien.

## 3. Chin Quyet Dinh Q1-Q9

### Q1. Cost

```text
cost(a) = delay_e2e(a) + w_loss * loss_e2e(a)
delay_e2e = tong total_delay_ms tren cac link cua path
loss_e2e  = 1 - product(1 - loss_rate(rho_link))
w_loss    = T_delay / T_loss
```

Trong buoc hieu chuan dau, dung `w_loss_temp = 2500 ms per unit loss`, neo vao
SLA sach vo `25 ms / 1% loss`.

Quy trinh hoi tu `w_loss`:

1. Dung `w_loss_temp = 2500` de tinh policy toi uu tam va phan phoi delay/loss.
2. Chot `T_delay`, `T_loss` bang quy tac Q2.
3. Dat `w_loss = T_delay / T_loss`, tinh lai policy toi uu.
4. Neu ti le action doi > 10%, lap mot lan nua, toi da 2 lan.
5. Neu van khong hoi tu, bao cao va chot `w_loss = 2500`.

Khong sua `w_loss` sau khi da thay `err(z)` hay `Delta_sla(z)`.

### Q2. SLA Thresholds

Vi pham SLA neu:

```text
delay_e2e > T_delay OR loss_e2e > T_loss
```

`T_delay` va `T_loss` de trong tai Lesson 20.0, chot o Lesson 20.1 bang quy
tac sau:

```text
chon (T_delay, T_loss) sao cho chinh sach toi uu vi pham 10-20%
```

Bien minh: ngoai dai nay, moi chinh sach deu dat hoac deu fail, nen
`Delta_sla` mat do phan giai. Neu nhieu cap thoa 10-20%, chon cap co
`T_loss = 0.01` roi giai `T_delay`.

### Q3. Fallback

Fallback Phase 20 la F2: shortest-hop tinh, co dinh, khong phu thuoc twin.
Neu cac path bang so hop, pha tie bang chi so path nho nhat.

F3 minimax dung conformal interval de danh cho Phase 23, khong dung o Phase 20.

### Q4. So Hanh Dong K

`K = 4`.

Bien minh: `topology3` co K=3 tren giay nhung K thuc te xap xi 1. Voi
profile `cliffband`, primary `rho in (0.80, 0.88)` cho delay 5.590-5.849 ms,
trong khi backup vung cliff cho 21.608-29.208 ms. Hai action con lai gan nhu
la action chet.

### Q5. Bin Tuoi

```text
z in {0, 1, 2, 4, 8, 16, 32}
z* = 8
```

`z* = 8` la bin kiem dinh chinh. Cac bin khac chi exploratory. Quy doi sang
ms/s thuc hien o Phase 21.

### Q6. Chia Calib/Test

Chia theo block episode, khong chia ngau nhien theo sample. Ly do: `rho(t)` co
tuong quan thoi gian; chia ngau nhien theo sample lam calib va test ro ri cung
episode, thoi phong coverage.

### Q7. Topology

Chon B: da duong khong dong nhat, co link dung chung, `K = 4`.

Thong so chot cho Lesson 20.0:

```text
topology_choice = B
K = 4
shared_links >= 1
```

Ly do vat ly: mang that thuong co aggregation/core bottleneck duoc nhieu path
chia se; loi tren link dung chung lam cost cac path tuong quan, khac voi san
khau ba duong doc lap. Day la cach tang do kho co bien minh vat ly, khong phai
tinh chinh tham so de co ket qua dep.

Rang buoc bat buoc cho topology moi:

1. Dai `rho` cua moi path phai phu quanh `J = {0.9250, 0.9325}`.
2. Chenh cost tot-nhi trong che do binh thuong phai cung bac do lon voi nhieu
   cua twin.
3. Co it nhat mot link dung chung giua >= 2 path.
4. Khong path nao nam hoan toan trong plateau `rho > 0.9325`.

Q7=A bi loai truoc khi do vi `topology3` cho K thuc te xap xi 1. Q7=C de danh
cho Phase 24/paper neu B pass kill-test.

### Q8. Mo Hinh Luu Luong

Chot o Lesson 20.1/20.1b, truoc khi do `err(z)`:

```text
flow arrival: Poisson
flow size: Pareto
lambda = TBD
mean flow size = TBD
kappa = TBD
mice/elephant mix = TBD
```

Muc tieu da chot: `rho` phai di qua ca hai phia cua moi nguong trong `J`.
Histogram `rho` phai co khoi luong >= 10% o moi phia cua `0.9250`.

### Q9. Khop Thang Thoi Gian

Chot o Lesson 20.1b:

```text
tau = thoi gian mat tuong quan cua rho(t)
A   = E[AoI] cua twin
rang buoc: 0.5 <= A/tau <= 2.0
```

Can gat uu tien: chu ky sync, vi re hon va phu hop thuc te digital twin cong
nghiep. Khong sua sau khi thay `err(z)`.

## 4. Quy Tac So Hoc

```text
EPS        = 1e-9
EPS_regret = 1e-9
```

Pha tie: neu `|cost_a - cost_b| < EPS`, chon path co chi so nho nhat. Ap dung
giong nhau cho twin va oracle.

Dem loi:

```text
err chi dem khi:
  a_twin != a_star
  va cost_true(a_twin) - cost_true(a_star) > EPS_regret
```

Chon khac mot path co cost bang nhau khong tinh la loi, vi regret bang 0.

Tie phai duoc bao cao. Neu ti le tie > 20%, san khau co qua nhieu trang thai
ma quyet dinh khong quan trong; day la tin hieu som cua fail nhanh (b).

## 5. Gate 20

PASS neu tat ca dieu kien sau dung:

```text
G1 err(z*) in [0.05, 0.40], z* = 8,
   va CI95 cua err(z*) nam tron trong [0.05, 0.40]

G2 Delta_sla_lower(z*) >= 0.03
   dung lower bound CI95, khong dung point estimate

G3 Spearman(err, z): rho_s > 0, p < 0.05

G4 NC1 z=0 co jitter do: err nho nhung > 0

G5 NC2 twin hoan hao: err = 0.000000 tuyet doi
   sau khi ap dung quy tac pha tie muc 4

G6 Sim vs real Lesson 20.3: khop dinh tinh
   cung dau, cung thu tu do lon, cung vi tri dinh cua err(z)
```

Fail duoc dien giai theo bon nhanh cua Lesson 20.4.

## 6. Ngan Sach Lap

Toi da 2 vong. Moi vong sua dung mot thu o cap kien truc. Truoc khi chay lai,
commit amendment moi: `docs/phase-20/00b-amendment-N.md`.

Quyet dinh truoc cho vong 2:

```text
Neu fail nhanh (b), err qua nho:
  sua Q8, tang khoi luong traffic gan J va tang xac suat crossing quanh J.

Neu fail nhanh (c), sai re:
  sua topology B, tang anh huong cua shared bottleneck / path coupling,
  khong sua w_loss sau khi thay so.
```

Het 2 vong chua pass thi dung, bao cao, va chon lai huong.

## 7. Rui Ro Da Biet

R1 `err(z)` qua nho: decision qua de. RQ nay co xac suat cao neu Q7=A, nen da
chon Q7=B.

R2 `err(z)` lon nhung `Delta_sla` nho: sai re, dung bay Phase 14A.

R3 Nguong SLA duoc chon cho ket qua dep: chan boi Q2, chi chot bang quy tac
10-20% cua policy toi uu.

R4 Chon bin `z` thang: chan boi `z* = 8` va Spearman trend.

R5 Tie lam NC2 fail gia: chan boi EPS, EPS_regret, va tie-breaking rule.

R6 `w_loss` chon cho ket qua dep: chan boi `w_loss = T_delay / T_loss`.

R7 `A/tau` lech qua xa: chan boi Q9 va Lesson 20.1b.

## 8. Confirmatory Vs Exploratory

Confirmatory:

```text
H1 tai z* = 8
H2 Spearman trend
G1-G6
NC1/NC2
```

Exploratory:

```text
cac z != 8
cac topology candidate khac Q7=B
bat ky threshold SLA nao khong sinh ra tu quy tac Q2
```

Exploratory co the bao cao, nhung khong dung de ket luan PASS Gate 20.
