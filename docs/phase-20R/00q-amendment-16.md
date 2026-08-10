# AMENDMENT 16 -- Lesson 20R.7: sua estimator cua ban do do cong

Ngay ky: 2026-08-10
Trang thai: KY SAU KHI CHAY PILOT CHAN DOAN. Xem sec.0.
Quan he: BO SUNG cho Amendment 15 sec.3-sec.7. Khong sua bat ky artifact nao
cua Lesson 20R.6, va khong sua ket qua K4 closed-form cua commit a1b264a.

---

## 0. Khai bao trung thuc -- pilot da chay truoc khi ky

Amendment nay KHONG phai preregistration thuan. Mot pilot chan doan da duoc
chay tren `results/phase-20R/truth_table.parquet` da commit, TRUOC khi van ban
nay duoc ky, de xac dinh estimator cu co hong hay khong.

Pilot da lo ba dieu:

```text
a. h = 0.01 cho d2 la artifact luoi (bang chung o sec.1).
b. Voi h = buoc luoi, argmax |d2 loss| on dinh cho poisson (2/2 cell),
   khong on dinh cho h2 (2/3 cell).
c. poisson bw=4.0 q=10 khong co node nao vuot nguong y nghia.
```

Do do moi lua chon trong van ban nay la lua chon CO NHIN SO LIEU. Chung duoc
ghi lai de nguoi doc tu danh trong so, khong duoc trinh bay nhu du doan mu.

Cai KHONG duoc phep, va da khong lam:

```text
- Khong ha SIG_K sau khi thay so cell "significant" it.
- Khong doi tu argmax sang mot thong ke khac de cuu ket luan.
- Khong bo cell h2 bw=4.0 q=10 khoi bao cao.
```

## 1. Ly do sua -- bang chung so

`TruthTable.delay_loss` dung `np.interp`, tuc noi suy tuyen tinh. Dao ham bac
hai cua ham tuyen tinh tung khuc bang 0 gan khap noi va la delta tai nut; no
khong ton tai nhu mot ham.

Luoi rho cua moi curve `poisson`/`h2` deu tuyet doi voi buoc `0.02`:

```text
bw=8.0 q=18  n=24  rho in [0.50, 0.96]
bw=6.0 q=13  n=28  rho in [0.50, 1.04]
bw=4.0 q=10  n=23  rho in [0.60, 1.04]
```

`mechanism_map.H = 0.01` la DUNG MOT NUA buoc luoi. Tren curve
`poisson/8.0/18`, sai phan bac hai voi `h = 0.01` cho:

```text
rho    d2_loss(h=0.01)
0.840  0.3981
0.850  0.0000   <- diem giua doan thang
0.855  0.6012
0.860  1.2025   <- nut
0.870  0.0000   <- diem giua doan thang
0.900  6.4801
0.930  0.0000
0.940  9.3213
0.950  0.0000
```

Day la ban do vi tri nut, khong phai vat ly. Ket qua `argmax_rho |d2 loss|`
tinh theo cach nay khong co y nghia.

## 2. Estimator moi

```text
Danh gia CHI TAI NUT LUOI.
h = stride * buoc luoi. stride = 1 la chinh, stride = 2 la kiem ben vung.
Stencil ba diem, cong thuc luoi khong deu (tu suy bien ve cong thuc deu).

d1:  w = ( -hp/(hm(hm+hp)),  (hp-hm)/(hm hp),   hm/(hp(hm+hp)) )
d2:  w = ( 2/(hm(hm+hp)),   -2/(hm hp),         2/(hp(hm+hp)) )
```

`d1` cua estimator cu (`grad_cost`) van hop le va khong bi thu hoi.
`curvature_cost` voi `h < buoc luoi` bi THU HOI cho moi muc dich ban do.

## 3. Mien hop le

Node cach mep duoi `stride` buoc bi bo. Do do truth table khong bao gio bi hoi
ngoai mien do va khong bao gio bi clip. Guard: `crosscheck_truth_table` phai
cho `max_abs_diff == 0`.

## 4. Thanh sai so

```text
loss  : Agresti-Coull, z = 1.959963984540054
        p_tilde = (x + z^2/2) / (n_pkt + z^2)
        se_ac   = sqrt(p_tilde (1 - p_tilde) / (n_pkt + z^2))
        Ly do khong dung Wald: x = 0 cho se = 0, tuc tuyen bo do chinh xac
        vo han tren mot o chi don gian la chua thay goi nao rot.
delay : cot `se_mean_ms` (batch SE).
lan truyen: se(sum w_i f_i) = sqrt(sum (w_i se_i)^2), gia dinh ba node doc lap.
        Neu ba node dung chung seed thi tuong quan duong, va gia tri nay la
        can tren cua SE that. Ghi la pham vi hieu luc.

Nguong y nghia (KY TRUOC KHI XEM BAN DO CUOI):
        SIG_K = 2.0.  Node duoc goi la co y nghia khi |d2| > 2 * se(d2).
Che do dem goi:
        LOW_COUNT_MIN = 10. Node co loss * n_pkt < 10 duoc gan co `low_count`.
```

## 5. Kiem ben vung va luat cong bo argmax

```text
Chay lai voi stride = 2 (h = 0.04).
argmax_rho |d2 loss| chi duoc cong bo khi no dich khong qua MOT buoc luoi
giua stride 1 va stride 2, tren MOI cell duoc quyet dinh cua family do.

Verdict duoc bao cao THEO FAMILY va gop. Tach theo family la tach cau truc,
khong phai tach nhom theo so lieu: w_loss va san nhieu loss khac nhau giua
poisson va h2 nen mot that bai gop co the che mot family da phan giai tot.

Neu mot family khong dat: KHONG cong bo argmax cho family do. Ghi:
"do phan giai luoi khong du de dinh vi dinh do cong cho <family>."
Khong duoc lam min bang spline roi lay argmax de cuu.
```

## 6. He qua cho du doan Amendment 15 sec.7

```text
Du doan #2 ("argmax_rho |d2 loss| trung hoac lech <= 1 buoc luoi voi
argmax_rho err, o it nhat 3 o non-cbr") chi duoc kiem tren family co
argmax_publishable = true. Neu tong so o kha kiem < 3 thi du doan #2 duoc
ghi la KHONG KIEM DUOC o do phan giai hien tai, khong phai FAIL.

Du doan #1 (Spearman(median r(s), err) < 0) va #3 (tach dong gop kenh)
khong phu thuoc argmax va van giu nguyen dieu kien Amendment 15.
```

## 7. Dai luong bo sung -- diem chuyen kenh

Ban do 3 sinh them mot dai luong khong co trong Amendment 15:

```text
R(rho) = |w_loss * d(loss)/d(rho)| / |d(delay)/d(rho)|
rho_cross = rho tai R = 1, lay LAN CAT LEN CUOI CUNG trong mien do.
```

`rho_cross` la ranh gioi che do: duoi no gradient chi phi do delay chi phoi,
tren no do loss chi phoi. Lan cat dau tien duoc giu lam chan doan vi loss o
rho thap la nhieu dem goi va co the cat gia.

Day la dai luong MOI, phat hien tu pilot. No duoc bao cao nhu quan sat mo ta,
KHONG duoc bao cao nhu gia thuyet da tien dang ky va da xac nhan.

## 8. Pham vi khong bi anh huong

```text
mechanism_map.py (so it) va results/phase-20R/mechanism_k4_closed_form.json
KHONG bi sua. Chung lay dao ham theo delta, tuc dich common-mode tren loss,
la da thuc tron 1 - prod(1 - p_i). Loi luoi chi cham dao ham theo rho.
Test test_phase20r7_mechanism.py giu nguyen.
```

## 9. Ghi chu thu tu thuc hien

Amendment 15 sec.8 (nguong gay khep kin K4) da duoc lam TRUOC sec.3-sec.7
(ban do co che). Ly do: sec.8 bit lo hong `safety_published = 0.868750` cua
Lesson 20R.6 cascade, la muc uu tien cao hon. Ghi lai de nguoi doc khong hieu
nham la sec.3 bi bo qua.
