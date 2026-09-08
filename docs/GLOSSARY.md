# GLOSSARY -- so dang ky ESTIMAND cua DT4N

Sinh o Lesson T2.2. Ly do ton tai: trong Phase T2 da hai lan mot CAI TEN
che HAI DAI LUONG hop le khac nhau.

```text
F1  (T2.0)  tau_load = 1.0 s  vs  tau_core = 2.87 s
T2.2        sigma_z cua `u` (co dieu kien)  vs  `sat` cua rms (hieu)
```

Hai lan khong phai trung hop. Do la trieu chung: repo thieu mot noi khai
bao MOI DAI LUONG bang toan, doc lap voi code. File nay la noi do.

Luat dung: mot nghi van CHI tro thanh loi SAU KHI grep xac nhan khong co
muc nao o day (va khong co tai lieu nao khac) giai thich no.

Moi muc: ky hieu - cong thuc - vai tro - dinh nghia goc (file:dong).

---

## tau_load

```text
Ky hieu   tau, tau_rho
Gia tri   THAM SO THIET KE, do nguoi dat. Legacy = 1.0 s.
Cong thuc phi = exp(-dt/tau)  -- he so AR(1) mot buoc
Vai tro   thoi gian tuong quan cua qua trinh tai TONG HOP (AR(1) sinh ra)
Goc       measurements/sla_calib_v2.py  (ar1_matrix, TAU_LOAD_LEGACY_S)
Tai lieu  docs/phase-21R/00-preregistration.md:441  (R9)
```

KHONG duoc co mac dinh im lang. `DEFAULT_TAU = 1.0` cu da len vao bon phase
ma khong ai ky, va sinh ra F4: chien dich 20R quet tau nhung giu z/tau co
dinh, khien err(tau) "gan phang" la mot TAUTOLOGY chu khong phai ket qua.

## tau_core

```text
Ky hieu   TAU_CORE_MEASURED_S
Gia tri   2.87 s -- DO DUOC, khong phai dat
Cong thuc uoc luong tu trace v7 that (tai loi Mininet)
DIA CHI   = tau do duoc cua link `ac` tren trace v7: 2.869 s
          docs/phase-20/00f-amendment-5.md muc A5.1 (bang tam link)
          Bay link con lai KHONG bang no, va trai rat rong:
              bc 2.441 | bd 2.605 | ac 2.869 | ad 3.958
              vC 17.38 | uB 21.70 | uA 22.87 | vD 32.00     (giay)
          => mot sigma_z dung CHUNG 2.87 cho ca TAM link la mot XAP XI,
             lech manh nhat o vD (32.00, gap 11 lan). Day KHONG pha bao
             dam bao phu (Mondrian hop le voi moi taxonomy co dinh truoc)
             nhung no lam bin KEM HIEU QUA -- va do chinh la ly do ton tai
             cua nhanh nhay cam `u_cond` (prereg T2 muc QD-1).
             Phai viet vao Threats to Validity, khong duoc "dong bo" thanh
             tau rieng tung link: doi dinh nghia u sau khi nhin du lieu la
             pha dieu kien "taxonomy co dinh TRUOC hieu chuan".
Vai tro   chuan hoa bien dieu kien u; B_BLOCK_S = 5*tau_core = 14.35 s
Goc       cert/build_calib_set.py:46          TAU_CORE_MEASURED_S
          measurements/decision_error.py:40    DEFAULT_TAU_CORE_S   <- CUNG MOT
                                               dai luong, ten khac, file khac
Tai lieu  docs/phase-21/99-erratum.md:76-80  (E4)
```

CANH BAO: 2.87 dang mang HAI TEN o hai file (lan thu BA trong phase nay mot
dai luong co nhieu ten). Chung KHONG mau thuan -- deu la thoi gian tuong quan
DO DUOC cua tai loi. Truoc khi "dong bo" hay "sua" mot trong hai, doc muc nay.
`DEFAULT_TAU_CORE_S` co mac dinh la HOP LE vi no la mot hang so DO DUOC (mac
dinh chinh la gia tri do duoc); khac han `tau_load` von la mot TRUC quet.

Khac `tau_load` ve BAN CHAT: mot cai do duoc tren tai that, mot cai dat ra
cho qua trinh tong hop. Khong phai mau thuan, khong duoc "dong bo" chung.

## sigma_z  (bien DIEU KIEN, truc u)

```text
Cong thuc sigma_z = sigma * sqrt(1 - exp(-2z/tau))
Hoi       "rho(t) co VUOT NGUONG khong, BIET rho(t-z)?"
Estimand  do lech chuan CO DIEU KIEN cua rho(t) | rho(t-z)
          Var[rho(t) | rho(t-z)] = sigma^2 (1 - phi_z^2),  phi_z = exp(-z/tau)
Vai tro   chia bin Mondrian: u = |rho_hat - nguong| / sigma_z
Goc       cert/build_calib_set.py:179
Tai lieu  docs/phase-21/00-preregistration.md:199-201  (P4b, TIEN DANG KY)
```

CANH BAO da biet: tu so dung `rho_hat = rho(t-z)` nhung mau so la do lech
CO DIEU KIEN -- tuc bo qua phan hoi quy ve trung binh `(1-phi_z)*|rho_hat-mu|`.
Sai sot ~5% o z/tau=0.05, ~63% o z/tau=1.0.
Day KHONG lam mat tinh hop le cua Mondrian conformal (bao phu van duoc bao
dam voi moi ham chia bin do duoc, mien la chon TRUOC khi nhin diem hieu
chuan); no chi lam bin KEM HIEU QUA. La van de SUC MANH, khong phai DUNG SAI.

## sat  (hoi quy SAI SO, luat rms)

```text
Cong thuc sat = sqrt(1 - exp(-z/tau))          -- KHONG co he so 2
          rms_pred = sqrt(em^2 + c*A^2*(1 - exp(-z/tau)))
Hoi       "twin sai bao nhieu khi giu nguyen gia tri cu?"
Estimand  phuong sai cua HIEU rho(t) - rho(t-z)
          Var[rho(t) - rho(t-z)] = 2 sigma^2 (1 - phi_z),  bien do A tu do
Vai tro   fit luat AR(1) cho rms_e_stale; sinh ratio(tau)
Goc       cert/tau_sweep.py:203,218
Khop voi  measurements/decision_error_v2.py:402
          e_stale = d_fresh[t] - d_fresh[t-z]   <- dung la HIEU
```

## Quan he giua hai cong thuc tren -- doc ky truoc khi thiet ke T2.6

```text
sigma_z (co dieu kien) va sat (hieu) LECH NHAU HE SO 2 trong so mu:
      convA(tau) == convB(tau/2)   (kiem bang so, tools/t2_0_tau_audit.py)
```

Ca hai deu DUNG cho vai tro cua minh. Nhung truc tau cua hai kenh KHONG so
sanh truc tiep duoc. T2.6 phai ghi ro moi hinh dung estimand nao, neu khong
doi chung noi tai (tau=1.0, z=0.10) se lech co he thong.

## Cac dai luong khac can nho

```text
z          tuoi telemetry (giay). Trong van hanh that do SYNC PERIOD quyet
           dinh (DEFAULT_SYNC_PERIOD_S = 0.5 s, measurements/decision_error.py:37),
           KHONG co gian theo tau. Day la nhanh B.
z/tau      ti so chuan hoa. Giu no co dinh lam sigma_z BAT BIEN theo dinh
           nghia -- nguon goc cua tautology F4. Day la nhanh A.
block_s    kich thuoc block conformal = 5*tau, KHONG phai 5 giay.
           measurements/decision_error_v2.py:block_s_for_tau
MIN_BLOCKS ceil(1/alpha) - 1 = 9 voi alpha = 0.10. Ap cho MOI SEED.
tau_hat    uoc luong cua tau tu chuoi. CHI phuc vu gate V-T2-2. Do chech cua
           no theo T_sim/tau (so chu ky doc lap), KHONG theo tau. Nen so voi
           KY VONG HUU HAN MAU, khong voi gia tri thiet ke (nguyen tac T-G2).
