# AMENDMENT 4 - Phase 20 Pre-Registration

Ngay: 2026-07-27
Trang thai: sau lan do 20.1b thu 2. KET LUAN: dat C1-C6, C7 dien giai duoc.

Khong sua `00-preregistration.md` hay cac amendment cu. Amendment nay ghi
ket qua do duoc, ba hien vat cua thuoc da sua, va viec phai lam truoc
Lesson 20.2.

## A4.1 Ket Qua Do Duoc

Bang nay chot dac trung san khau tu trace 240 s sau warm-up:

| link | mu | sigma | tau(s) | so chu ky tuong quan trong 240 s |
|---|---:|---:|---:|---:|
| uA | 0.8166 | 0.0239 | 15.09 | 16 (THIEU, can >= 30) |
| uB | 0.8344 | 0.0197 | 21.86 | 11 (THIEU) |
| ac | 0.9451 | 0.0889 | 1.982 | 121 OK |
| ad | 0.9442 | 0.0928 | 3.092 | 78 OK |
| bc | 0.9289 | 0.0995 | 2.509 | 96 OK |
| bd | 0.8918 | 0.1000 | 2.714 | 88 OK |
| vC | 0.7958 | 0.0264 | 19.81 | 12 (THIEU) |
| vD | 0.8492 | 0.0217 | 12.58 | 19 (THIEU) |

Bat bien phan giai tren 4 link loi:

```text
ac: tau(10ms)=1.9820 s, tau(2ms)=1.9818 s
ad: tau(10ms)=3.0916 s, tau(2ms)=3.0915 s
bc: tau(10ms)=2.5092 s, tau(2ms)=2.5083 s
bd: tau(10ms)=2.7142 s, tau(2ms)=2.7132 s
```

Giam chu ky lay mau 5 lan nhung tau gan nhu khong doi. Day la bang chung
rang phep do dang do he thong, khong do thang do.

Mo hinh M/G/inf duoc kiem chung: 7/8 link co tau trong he so 1.35 so voi du
doan, `vD` lech 2.1x; sigma khop 8/8. `vD` duoc coi la threat to validity
cho toi khi trace 1800 s xac nhan hoac bac bo.

## A4.2 Ba Hien Vat Cua Thuoc - Da Sua

T1. `n/a` o `dt=2ms` cho link bien la do cap cung `max_lag=3000`.

```text
3000 * 2 ms  =  6 s  <  tau_bien 12-22 s
3000 * 10 ms = 30 s  >= tau_bien 12-22 s
```

Sua: cua so ACF mac dinh duoc dat theo thoi gian vat ly:

```text
ACF_WINDOW_S = 60.0
max_lag = min(len(x)//4, int(ACF_WINDOW_S / dt_s))
```

T2. `EXP`/`POWER` lat giua hai `dt` vi hai lan fit khong cung cua so thoi
gian. Sua: bao cao fit tren cac cua so vat ly co dinh, mac dinh `6 s` va
`60 s`, va in ro khoang lag thuc su duoc fit.

Dien giai dung: ACF co than mu ngan va duoi luy thua dai. Day la chu ky mong
doi cua traffic co kich thuoc flow Pareto. Tai diem van hanh
`z* = 0.298 s << 6 s`, phan ra cuc bo la mu, nen tau co y nghia cuc bo; khong
duoc dung tau de ngoai suy toi cua so dai nhu `30 s`.

T3. `NOT STATIONARY` trong output cu la bao dong gia. SE cu dung
`n^(H-1)` va phu thuoc vao H uoc luong tu fit ACF khong on dinh. Sua:

```text
T_half = (n/2) * dt_s
SE_hieu = 2 * sqrt(tau_s / T_half)
n_corr = T_total / tau_s
stationary neu drift <= 3 * SE_hieu
```

Cong thuc nay suy tu:

```text
Var(mean tren T) ~= (2*tau/T) * sigma^2
```

Tinh lai trace 240 s: 8/8 link dung theo drift test, nhung 4 link bien van
thieu so chu ky tuong quan de tin tau/sigma.

## A4.3 Viec Phai Lam Truoc Lesson 20.2

V1. Chay lai 1800 s, khong doi cau hinh nao, chi tang `--duration`.

Muc tieu: 4 link bien dat it nhat 30 chu ky tuong quan va kiem tra `vD` co
hoi tu ve du doan M/G/inf khong.

V2. Dung analyzer da sua T1-T3 de phan tich trace 1800 s.

V3. Bao cao ACF tren ca hai cua so `6 s` va `60 s` cho ca 8 link.

## A4.4 Q2 Chot

`link_model.py` la ham bac thang, nen ti le vi pham nhay coc theo `T_delay`:

```text
T_delay = 13.5 ms -> 60.8%
T_delay = 14.5 ms -> 17.1%
T_delay = 15.0 ms -> 10.1%
T_delay >= 16.0 ms -> 5.7% gan nhu phang
```

Chot Q2:

```text
T_delay = p85 cua delay duoi chinh sach toi uu tren trace 1800 s
T_loss  = 0.010
w_loss  = T_delay / T_loss
```

`w_loss` khong con la gia tri tam `2500`. Chay vong hoi tu `w_loss` theo Q1,
toi da 2 lan lap, va khong sua sau khi da thay `err(z)` hay `Delta_sla(z)`.

## A4.5 z* Chot Bang Giay

```text
z* = A = E[AoI] = 0.298 s
```

Ly do giu nguyen tu A2.2: trong vong dieu khien dong that, controller hanh
dong tren snapshot twin moi nhat.

Bin quet exploratory:

```text
z in {0, 0.10, 0.20, 0.298, 0.50, 1.00, 2.00, 4.00} seconds
```

Bo don vi `buoc env` trong Phase 20; moi so tuoi duoc tinh bang giay vi tau
da do duoc bang giay.

## A4.6 CI95 Phai Hieu Chinh Tuong Quan

Moi ti le trong Phase 20 phai dung co mau hieu dung:

```text
n_eff = T_total / (2 * tau_core)
```

Khong dung so mau raw `n = T/dt`. Voi trace 2400 s va `tau_core = 2.57 s`,
`n_eff = 467`, khong phai `240000`. Bo qua tuong quan lam CI95 hep gia khoang
22 lan.

Ap dung cho `err`, `Delta_sla`, ti le tie, va ti le vi pham.

## A4.7 Sai So Telemetry La Future Work

So sanh `rho_offered` voi `rho_measured` cho thay hai hieu ung rieng:

1. Link loi co `sigma_measured < sigma_offered`. Day khong phai bug ma la
   bao hoa: `rho_offered` co the vuot 1, nhung throughput do duoc bi cat boi
   dung luong link. No xac nhan cau truc `rho_measured_from_offered()` da duoc
   hieu chuan o Phase 9.
2. Link bien `uA/uB` co `noise_var_share = 0.51/0.63`; nhieu telemetry chiem
   hon nua phuong sai quan sat duoc tren link tai nhe.

Phase 20 dung `rho_offered` cho ca twin lan oracle de co lap mot bien duy
nhat: do cu. Tach sai so do-luong khoi sai so do-cu de danh cho future work.

## A4.8 Du Doan Gate 20

Day la du doan rui ro, khong phai ket qua confirmatory, va khong duoc trich
dan nhu evidence:

```text
z* = 0.298 s
err = 0.258 +- 0.040
Delta_sla_lower = 0.091
K_eff = 3.36 / 4
```

Du doan dung AR(1) xap xi tren than mu ngan, trong khi he that co duoi luy
thua dai. Ket qua that phai den tu `decision_error.py` chay tren trace that.
