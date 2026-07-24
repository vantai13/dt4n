# PRE-REGISTRATION — Phase 14 (RQ0)

**Ngay ky: 2026-07-23**
**Nguoi ky: vantai13**
**Commit hash tai thoi diem ky: (dien sau khi commit)**

> Van ban nay duoc viet TRUOC khi chay bat ky do dac nao tren topology moi.
> Moi nguong duoi day duoc chot TIEN NGHIEM. Neu ket qua khong dat, ket qua
> do la KET QUA THAT va se duoc bao cao nguyen ven. KHONG duoc sua nguong
> sau khi nhin so. Vi pham dieu nay = HARKing = gate mat y nghia.

---

## Cau hoi nghien cuu RQ0

Khi nao thong tin ve do tre (Age of Information) mang gia tri quyet dinh
cho mot tac nhan hoc tang cuong?

## Gia thuyet

Thong tin AoI chi mang gia tri khi bien do tre z DOC LAP voi noi dung
quan sat. Neu noi dung quan sat tiet lo z, tac nhan suy ra rui ro tu
prior va AoI tro nen DU THUA.

---

## NAM DIEU KIEN + NGUONG (chot tien nghiem)

### (1) DRIFT — the gioi phai DONG
    Do:      E[|rho(t) - rho(t-z)|] voi z in {0,1,3,5,8,12}
    Nguong:  > 0 va TANG DON DIEU theo z
    Ly do:   z=0 va z=12 phai cho ra hai the gioi khac nhau, neu khong
             thi khong co gi de biet. Chet o lan 1, 2.

### (2) NO-DOMINANT — khong duong nao TROI
    Do:      max_a P(a toi uu | du lieu tuoi),  a in {P1, P2, P3}
    Nguong:  < 0.45
    Ly do:   chance = 1/3 = 0.333. Neu mot hanh dong toi uu > 45% ngay ca
             khi du lieu TUOI, policy suy bien ve hang so.
             Neo: lan 3 chet o 0.665 voi 2 duong (chance 0.5, vuot 0.165).
             Bien tuong duong voi 3 duong: 0.333 + 0.12 ~ 0.45.

### (3) * INDEPENDENCE — z DOC LAP voi obs        [MOI — cai giet lan 4]
    Do A:    adversarial probe accuracy (classifier: obs -> z)
    Nguong A: < 0.25   (chance = 1/6 = 0.167, cho bien 0.083)
    Do B:    I(obs; z) uoc luong truc tiep
    Nguong B: < 0.05 bit
    Ly do:   neu obs tiet lo z, agent suy ra rui ro tu prior, AoI du thua.
             Day la chan doan cuoi cung cua 4 lan am.

### (4) COSTLY — hau qua sai phai DAT
    Do:      regret trung binh khi chon sai duong
    Nguong:  > 0.045  (= std_agent do o Phase 9)
    Ly do:   neu chon sai chi mat it hon nhieu giua cac seed,
             tin hieu chim trong nhieu. Bai hoc A2.

### (5) * HEADROOM — thuoc DUNG                    [MOI — thuoc thay the]
    Do:      gap_marginalized
             = Bayes(obs + z) - Bayes(obs, marginalize z)
             KHONG phai fresh - stale
    Nguong:  mean - ci95 >= 0.10        (CAN DUOI CI, khong phai mean)
    Ly do:   std_agent ~ 0.045. Phat hien duoc voi 5 seed can bien do
             >= 2 x nhieu = 0.09. Lam tron len 0.10 cho bien an toan.

---

## GATE

    CA 5 DIEU KIEN PASS  =>  duoc phep viet code train (Phase 15+)
    THIEU 1 DIEU KIEN    =>  DUNG. Sua topology. Do lai. KHONG train.

Toi da 3 vong lap. Sau 3 vong van FAIL => dung lai, mang so lieu gap GVHD.
Ket luan "cau truc routing khong phai san khau dung cho cau hoi nay"
CUNG LA MOT KET QUA hop le, va se co bang chung dinh luong kem theo.

Moi vong lap chi duoc sua MOT THU (nguyen tac OFAT — One Factor At a Time),
de biet chinh xac thu nao co tac dung.

---

## THIET KE SAN KHAU (chot truoc)

Topology: 3 duong SONG SONG, DOI XUNG
    SRC -> {P1 | P2 | P3} -> DST
    cung so hop, base delay/bw tuong duong.

Co che su kien (VO HUONG — day la diem khac biet cot loi so voi lan 4):
    t_event   ~ Uniform(0, T)             ngau nhien, doc lap voi obs
    duong sap ~ Uniform{P1, P2, P3}       ngau nhien DEU
    duong giai phong ~ Uniform{con lai}

    TUYET DOI KHONG dung trend co huong (*_trend_range).
    TUYET DOI KHONG dung scenario_weights lech.

State: 11-D, Action: Discrete(3)
z_choices = {0, 1, 3, 5, 8, 12}, P(z) uniform
STEP_DURATION_S = 0.5  (KHOA — neo Muc 3 voi Ditto that)

---

## NEGATIVE CONTROL (bat buoc)

Truoc khi tin thuoc gap_marginalized tren topology moi, phai chay no tren
topology CU 2-duong (rl/routing_2path/).

    Ky vong:  gap_marginalized ~ 0 (< 0.05), GATE = FAIL

Neu thuoc moi bao PASS tren topology cu => THUOC MOI CUNG SAI,
phai sua thuoc truoc khi di tiep.

---

## PHU LUC - Dieu kien bo sung sau negative control (exploratory)

Muc nay duoc them ngay 2026-07-23, SAU khi quan sat ket qua negative control
tren `routing_2path`. No KHONG phai tieu chi tien nghiem da ky o tren.

Dieu kien bo sung 6:

    q_margin phai GIAM theo z
    Chan doan toi thieu: q_margin(z=12) < q_margin(z=0)

Ly do: negative control cho thay voi trend don dieu, q_margin tang manh theo
z. Khi do staleness lam bai toan ro rang hon, khong phai kho hon, va
`gap_marginalized` suy sup ve gan 0. Gia tri AoI chi con nam o truong hop
z=0, noi agent biet minh co anh tuoi va co the bo hedge.

Cach dung trung thuc:

    Dieu kien 5 (`gap_marginalized`, mean - ci95 >= 0.10) GIU NGUYEN la gate
    chinh.

    Dieu kien bo sung 6 chi la chan doan ho tro de thiet ke topology moi va
    giai thich vi sao mot topology FAIL. Khong duoc viet nhu the no da duoc
    chot truoc negative control.

He qua cho topology moi: drift nen la khuech tan/su kien ngau nhien vo huong,
khong phai trend co huong don dieu.

---

Ky: ________________    Ngay: 2026-07-23

## PHU LUC B - Hieu chuan lai nguong (ghi TRUOC khi do, 2026-07-24)

Nguong 0.10 = 2 x std_agent, voi std_agent = 0.045 do o Phase 9 tren:

- topology 2-duong
- reward cu
- objective ky vong

Ba thu do deu da doi trong exploratory routing3/CVaR. Ap nguong cu truc tiep
la so hai don vi khac nhau, giong loi da phat hien o vong reward-audit.

Cam ket truoc khi do:

- dung nguong = 2 x san_nhieu(routing3), bat ke con so do la bao nhieu;
- giu nguyen cong thuc 2x nhu da ky;
- chi cap nhat tham so san_nhieu theo san khau moi;
- khong doi cong thuc thanh 1.5x hay mot he so khac sau khi nhin so.

San nhieu se duoc do bang Bayes-marginalized policy tren nhieu seed, khong can
train, de giu nguyen tac Phase 14 khong train.

Kiem dinh cong cu: chay tren `routing_2path` voi objective `mean` truoc. Neu
ket qua lech xa neo Phase 9 hoac khong giai thich duoc, khong duoc dung ket
qua routing3 de doi nguong.
