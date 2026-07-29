# PRE-REGISTRATION -- Phase L: Dac trung hoa link bang do that

Ngay ky : ____              Git tag: phase-L-start
Commit  : ____
Tien de : Phase 20/21 (v7) dong bang. Ba loi cau truc S1/S2/S3.
          Erratum E6/E7/E8 tai docs/phase-20/99b-erratum.md
Trang thai: CHOT. Sua doi sau ngay ky -> docs/phase-L/00b-amendment-N.md,
            ghi ro DA THAY SO NAO truoc khi sua.

## L0  KIEM TOAN TIEN DE  (ghi TRUOC, la co so cua toan bo phase)

A1. Phep do backlog cu la TAUTOLOGY, khong phai phep do.
    Bang chung tu results/calib/raw_sweep_2node.csv:
        backlog(rho<=0.9) = BDP x rho_measured, khop trong 2%
        bw=4 d=2.0ms: BDP=1000B, do 986-1035B
        bw=6 d=3.0ms: BDP=2250B, do 2214-2237B
        bw=8 d=1.5ms: BDP=1500B, do 1471-1560B
        VA: khong doi khi q = 4,5,7,10,13,20,26
    Ly do toan hoc (luat Little): netem giu moi goi dung `delay` giay,
        toc do den = rho*C  =>  so bit bi giu = rho*C*delay = rho*BDP
    => q_delay_do = delay_ms x rho. Day la DANG THUC, khong phai do luong.
    => NETEM_OCCUPANCY_COEF=1.0 trong link_model.py chi la viet lai dinh nghia.

A2. link_model v1 gan DO DOC gia cho mot HANG SO.
        model  : d(delay)/d(rho) = base_delay_ms  (3.0 ms/don vi rho tren link ac)
        vat ly : d(delay)/d(rho) ~ 0 o che do CBR
    Muc tuyet doi tinh co gan dung (base*rho ~ serialization);
    DO DOC sai hoan toan. Do doc la thu quyet dinh argmin.

A3. "Vach da" = rho_measured cham 1.0. Tu cliff_fine_0718_0212.csv:
        rho_off 0.925 -> rho_meas 0.9953 -> hang doi 0-1 goi
        rho_off 0.930 -> rho_meas 0.9976 -> random walk 4-13 goi
        rho_off 0.935 -> rho_meas 0.9975 -> 12-13 goi
    CLIFF_RHO_OFFERED=0.9275 vs 1/OVERHEAD_FACTOR=0.9268. Cung mot thu.
    Day la hinh dang bat buoc cua D/D/1/K, khong phai phat hien ve mang.

A4. OVERHEAD_FACTOR=1.0790 tron VAT LY voi SAI SO DUNG CU.
        khung Ethernet 1512/1470 = 1.0286   <- vat ly
        phan du        1.0790/1.0286 = 1.049 <- iperf gui nhanh hon nhan -b
    => Phase L KHONG dung so danh nghia. Dung toc do gui THUC TE tu
       /proc/net/dev phia gui lam rho.

A5. flow_engine KHONG bursty o tang goi. Doc code:
        payload_bytes = 1400 co dinh          => c_s = 0
        kappa = 2.5 (khong phai 1.5)          => phuong sai HUU HAN
        t_next_send = now + L/rate_sum_bps    => nhip TAT DINH
    Mo phong voi tham so that (cap=6M, rho=0.925, sigma=0.010, kappa=2.5):
        n_concurrent = 8556 luong
        c_a do duoc  = 0.072
        Kingman E[Wq] tai rho=0.925 = 0.062 ms
    => Che do trien khai that su la c_a ~ 0.07, KHONG phai 1.5.
    => Loi S2 khong phai "hieu chuan CBR nhung chay bursty".
       Loi that: HE THONG CHUA BAO GIO VAO CHE DO CO HANG DOI.
    => LUA CHON DA CHOT: (alpha) chap nhan CBR la che do van hanh CHINH,
       tuyen bo ro trong Abstract, dung 3 che do de DINH LUONG do nhay
       cua bao dam theo c_a. Sua flow_engine la cau hoi mo cua Phase T.

## L1  HA TANG DO -- CHOT

Qdisc dung bang TAY (KHONG dung TCLink params).
Ly do: TCLink dat HTB `burst 15k` = 9.9 goi MTU ~ ca buffer 13 goi,
       se HAP THU chinh hieu ung c_a ma ta dang do; va max_queue_size
       tro thanh `netem limit` (goi) thay vi buffer theo byte.

Chieu DO   s1->s2 :
    tc qdisc add dev <if> root handle 1: htb default 10
    tc class add dev <if> parent 1: classid 1:10 htb \
            rate {4|6|8}mbit burst 1600b cburst 1600b
    tc qdisc add dev <if> parent 1:10 handle 10: bfifo limit {q*1512}
Chieu VE   s2->s1 :
    tc qdisc add dev <if> root handle 1: netem delay 3ms

RANG BUOC: throughput bao hoa do duoc phai >= 0.98 x rate danh nghia.
    Neu khong dat -> tang burst theo bac 1600/2400/3000/4000 b,
    dung o gia tri NHO NHAT dat nguong, GHI vao provenance.

## L2  DAI LUONG VA CACH DO -- CHOT   (ba phep do doc lap, NT 39)

(1) PHEP DO CHINH -- goi nen TU MANG timestamp
    goi nen: 1470 B payload (1512 B tren day), mang seq(8B)+t_send(8B)
    => OWD theo TUNG GOI => PACKET-AVERAGE  (dai luong SLA quan tam)
    => loss tu seq thieu
    => XAM LAN = 0 (no chinh la tai)
    => n ~ 446 goi/s x 60 s = 26,760 mau tai bw=6, rho=0.9

(2) PHEP DO PHU 1 -- probe Poisson thua
    64 B, khoang cach Poisson trung binh 50 ms (20 goi/s)
    => TIME-AVERAGE (virtual waiting time), chuan RFC 2330 / OWAMP
    => BAT/TAT duoc, de chay V-L7

(3) PHEP DO PHU 2 -- tc -s qdisc backlog, poll 20 ms
    => doi chieu doc lap thu ba

Dong ho : time.monotonic() ca hai dau (Mininet netns dung chung kernel
          => chung CLOCK_MONOTONIC => khong co sai so dong bo)

## L3  DAI LUONG BAO CAO -- CHOT

Moi diem ghi:
    owd_pkt_p50, p90, p95, p99, mean, sd      <- tu (1), CHINH
    owd_probe_p50, p95, mean                  <- tu (2)
    delta_pasta = owd_pkt_mean - owd_probe_mean   <- * dai luong MOI
    loss_pkt        (tu seq thieu, phep do (1))
    loss_qdisc      (tu counter drops, phep do (3))
    backlog_mean, backlog_p95                 <- tu (3)
    c_a_do_duoc, c_s_do_duoc                  <- BAT BUOC (NT 36)
    rho_danh_nghia, rho_thuc_te_gui, rho_thuc_te_nhan
    n_goi_gui, n_goi_nhan, n_probe_gui, n_probe_nhan
    burst_htb_da_dung, tc_command_string      <- provenance cau hinh

DAI LUONG CHINH cho link_model_v2: owd_pkt_p50
DAI LUONG PHU (bao cao ca)       : owd_pkt_p95, owd_pkt_p99
Ly do chon p50: on dinh nhat. p99 gan SLA hon nhung nhieu hon.
BAO CAO CA HAI. KHONG chon sau khi thay so.  (tra loi Q9 master plan)

## L4  LUOI DO -- CHOT TRUOC KHI CHAY

TRUC 1  rho  : 0.50 0.60 0.70 0.80 0.85 0.90 0.925 0.95 0.98
               1.00 1.02 1.05                                -> 12 diem
TRUC 2  che do: cbr (c_a=0) | poisson (c_a=1) | bursty (c_a muc tieu 2.0)
                                                             ->  3 muc
TRUC 3  cau hinh: (bw=8,q=18) (bw=6,q=13) (bw=4,q=10)        ->  3 muc
LAP     : 5 seed
TONG    : 12 x 3 x 3 x 5 = 540 diem

Moi diem: warm-up 10 s (BO), do 60 s.  =>  540 x 70 s = 10.5 gio
Chia 4 phien ~2.6 gio, moi phien ghi checkpoint.

THU TU CHAY: NGAU NHIEN TOAN PHAN (seed thu tu = 9000).
    Kha thi vi doi cau hinh chi can `tc change`, khong restart Mininet.
    Ly do: chong confounder nhiet do CPU / tai may theo thoi gian.

TINH GON HON so voi ban v8 goc (22 diem, 990 diem, 19.3 gio):
    Ly do: mo phong cho thay duong cong TRON o vung 0.88-0.98
    (khong con "vach da" khi da bo netem khoi chieu do),
    nen luoi min 0.01 khong con can thiet.
    LUAT MO RONG DA CHOT TRUOC: sau giai doan 1, neu ton tai cap
    (rho_i, rho_{i+1}) lien tiep co |q_p50 chenh| > 5 ms, THEM 3 diem
    chia deu trong khoang do, cho MOI (mode, config). Luat nay ap dung
    may moc, KHONG phu thuoc vao viec ket qua co dep hay khong.

## L5  * BANG DU DOAN -- DIEN TRUOC, KHONG SUA SAU

Nguon: mo phong GI/D/1/K (khong phai Kingman buffer vo han -- buffer
huu han lam delay THAP HON NHIEU va sinh loss SOM HON).
Gia dinh: goi nen 1512 B tren day, K goi tail-drop, probe 106 B.

--- bw=6 Mbps, K=13, E[S]=2.016 ms, tran ly thuyet 26.2 ms ---
 rho   | CBR p50 | POIS p50 | BURSTY p50 | CBR loss | POIS loss | BURSTY loss
 0.50  |  0.14   |   0.14   |    0.14    |  0.000   |   0.000   |   0.000
 0.70  |  0.71   |   1.63   |    3.19    |  0.000   |   0.000   |   0.014
 0.80  |  0.90   |   2.70   |    5.88    |  0.000   |   0.001   |   0.039
 0.90  |  1.03   |   5.61   |    9.44    |  0.000   |   0.009   |   0.078
 0.95  |  1.10   |   8.50   |   11.18    |  0.000   |   0.020   |   0.101
 1.00  |  1.15   |  12.52   |   12.88    |  0.000   |   0.040   |   0.126
 1.05  | 24.36   |  16.40   |   14.31    |  0.048   |   0.067   |   0.150

--- bw=8 Mbps, K=18, E[S]=1.512 ms, tran 27.2 ms ---
 rho   | CBR p50 | POIS p50 | BURSTY p50
 0.70  |  0.54   |   1.22   |    2.56
 0.90  |  0.78   |   4.50   |    8.89
 0.95  |  0.82   |   7.67   |   11.20

--- bw=4 Mbps, K=10, E[S]=3.024 ms, tran 30.2 ms ---
 rho   | CBR p50 | POIS p50 | BURSTY p50
 0.70  |  1.08   |   2.44   |    4.40
 0.90  |  1.56   |   7.51   |   11.11
 0.95  |  1.64   |  10.39   |   12.93

DU DOAN DINH TINH -- neu SAI thi PHAI dieu tra TRUOC khi tin du lieu:

D1  * CBR: p50 khop CONG THUC DONG (khong phai "gan 0"):
        p50 = S_probe + E[S] * max(0, 0.50 - (1-rho)) / rho
        p95 = S_probe + E[S] * max(0, 0.95 - (1-rho)) / rho
    Sai so cho phep: 10%. Day la GOLDEN TEST manh nhat cua Phase L.

D2  * POISSON: khop Pollaczek-Khinchine (CHINH XAC, khong phai xap xi)
        E[Wq] = rho * E[S] / (2(1-rho))     [M/D/1, buffer vo han]
    Chi ap dung o rho <= 0.85 (tren do hieu ung buffer huu han > 5%).
    Sai so cho phep: 15%.

D3  THU TU: q_delay(cbr) < q_delay(poisson) < q_delay(bursty),
    o MOI rho >= 0.7, khoang cach > 2 x SE.

D4  DELAY TRUNG BINH KHONG BAO GIO CHAM TRAN khi rho < 1.
    Gia tri bao hoa du kien ~45-55% cua tran. Neu do duoc >= 90% tran
    o rho < 1 -> co loi cau hinh (buffer khong dung nhu khai bao).

D5  LOSS xuat hien SOM VA MANH o che do bursty:
    bursty co loss >= 1% tu rho ~ 0.65-0.70
    poisson co loss >= 1% tu rho ~ 0.90-0.92
    cbr KHONG co loss cho toi rho > 1.0

D6  * THIEN LECH PASTA (delta_pasta = pkt_mean - probe_mean):
        cbr    : AM (probe doc CAO hon, do residual service time)
        poisson: ~0 (dinh ly PASTA)
        bursty : DUONG, khoang +8% den +15%
    Neu D6 sai o che do poisson -> mot trong hai phep do sai.

D7  RHO THUC TE / RHO DANH NGHIA nam trong [0.97, 1.00] cho moi diem.
    (Python pacing chi co the gui THIEU, khong the gui THUA.)

NEU D1 SAI  -> DUNG LAI. Thiet bi do hong. Khong chay chien dich.
NEU D2 SAI  -> DUNG LAI. Thiet bi do hong.
NEU D3 SAI  -> xem nhanh (b) o Lesson L.8. Kiem HTB burst truoc tien.
NEU D4 SAI  -> kiem bfifo limit bang `tc -s qdisc show`.

## L6  TIEU CHI FIT -- CHOT TRUOC KHI NHIN DU LIEU

Mo hinh (A) co tham so -- Kingman co tran, de GIAI THICH:
    W(rho) = min( rho/(1-rho) * C * E[S] , W_max )
    C     : fit, MOT gia tri cho moi (che do, cau hinh)
    W_max : fit, rang buoc <= 1.2 x tran buffer ly thuyet
Mo hinh (B) noi suy don dieu PCHIP -- de DU DOAN.

HELD-OUT: giu lai moi diem rho THU BA (index 2,5,8,11) -> 4 diem
    fit tren 8 diem, cham diem tren 4 diem giu lai.
TIEU CHI: R2 held-out >= 0.90 cho mo hinh (B).
    Mo hinh (A) BAO CAO R2, KHONG dat nguong.
BAND DU: bao cao SD va p95 cua r = do - fit, THEO rho.
    KHONG lam phang. KHONG loai ngoai lai.
    (r la e_model -- dau vao truc tiep cua conformal Phase 21R)

## L7  DOI CHUNG BAT BUOC  (Lesson L.3 -- KHONG sang L.4 neu con 1 cai fail)

V-L0  SAN NHIEU: link 1 Gbps khong shaping, tai 0
      -> ghi lai mean va SD cua OWD. Neu SD > 0.2 ms -> nang cap
         sang SO_TIMESTAMPNS truoc khi di tiep.
V-L1  netem delay 10 ms dat o CHIEU DI (topology kiem dinh rieng), tai ~0
      -> OWD do duoc trong [9.5, 11.0] ms. Sau do GO netem.
V-L2  tai ~0, khong netem -> OWD ~ S_probe = 106*8/bw
      bw=4: 0.212 | bw=6: 0.141 | bw=8: 0.106 ms
      VA: OWD(tai 0) phai TI LE NGHICH voi bw qua ba cau hinh
V-L3  DOI CHUNG AM: tat tai nen hoan toan -> q_delay ~ 0, loss = 0
V-L4  DOI CHUNG DUONG: doi bfifo limit tu q=13 xuong q=5
      -> tran do duoc PHAI giam theo ti le. Neu KHONG -> DUNG LAI.
V-L5  ba phep do dong thuan: |owd_probe_p50 - backlog_mean/rate| / owd_probe_p50
      <= 0.20 o rho <= 0.9
V-L6  * GOLDEN TEST LY THUYET: che do cbr khop cong thuc dong D1 trong 10%,
      che do poisson khop P-K trong 15% o rho <= 0.85
V-L7  * KIEM SOAT XAM LAN CUA PROBE: tai rho=0.90 che do cbr, quet
      toc do probe 0 / 10 / 20 / 40 goi/s
      -> owd_pkt_p50 phai PHANG trong +-10%.
      Neu tang theo toc do probe -> probe dang tu tao hang doi -> giam
         toc do probe va ghi amendment.

## L8  NEU FAIL THI SUA GI  (dien TRUOC, khong duoc de trong)

nhanh (a) V-L5 fail, ba phep do khong dong thuan
    -> kiem theo THU TU: (1) `tc -s qdisc show` xac nhan cau truc dung
       thiet ke; (2) warm-up du chua (tang len 20 s); (3) rho_thuc_te
       co khop danh nghia khong; (4) probe co di cung hang doi khong.
       KHONG chon phep do cho so dep. Sua loi, do lai.

nhanh (b) D3 fail, ba che do trung nhau
    -> KIEM HTB burst TRUOC TIEN (`tc class show`). burst lon hap thu
       burstiness. Neu burst da toi thieu ma van trung
       -> DAY LA KET QUA, khong phai loi. Ghi lai, BO TRUC 2 khoi cac
       phase sau (tiet kiem 2/3 thoi gian may), va ghi vao paper:
       "at this buffer scale, queueing is dominated by finite-buffer
        saturation rather than arrival burstiness".

nhanh (c) khong don dieu theo rho, hoac R2 < 0.90
    -> kiem: thu tu chay da ngau nhien chua; rho_thuc_te co khop khong;
       co diem nao chua o trang thai dung khong (chia 60 s thanh 6 khoi
       10 s, so trung binh cac khoi). Neu tat ca sach ma van khong don
       dieu -> co hien tuong that, dieu tra va GHI.

nhanh (d) band du qua rong (SD(r) > 10 ms)
    -> KHONG phai loi, la CANH BAO SOM: q_hat cua Phase 21R se rong.
       Hai lua chon, chon (d1): them bien vao mo hinh (c_a tuc thoi,
       do dai hang doi hien tai). Neu (d1) khong cai thien >20%,
       chuyen sang (d2): chap nhan va BAO CAO TRUOC rang bao dam se long.

NGAN SACH: toi da 2 vong. Moi vong sua DUNG MOT thu, va phai commit
amendment ghi ro DA THAY SO NAO truoc khi sua.

## L9  RUI RO DA BIET

RL1  Python sender khong dat duoc toc do chinh xac (pacing drift).
     Giam nhe: do toc do THUC TE tu /proc/net/dev, dung so THUC TE lam rho.
     Ky vong: thieu 0-3% (D7).
RL2  HTB burst nho co the lam khong dat rate danh nghia.
     Giam nhe: quet burst, chon gia tri nho nhat dat >= 98%, ghi provenance.
RL3  Chay nhieu gio lien tuc co the gap trang thai la cua may.
     Giam nhe: 4 phien ~2.6 gio, checkpoint, thu tu ngau nhien.
RL4  Timestamp userspace co jitter lap lich. Giam nhe: V-L0 do san nhieu.
RL5  26,760 mau/diem x 540 diem = 14.5 trieu ban ghi.
     Giam nhe: ghi RAW day du cho pilot + 20 diem ngau nhien;
     cac diem con lai ghi thong ke tom tat + histogram + reservoir 2000 mau.

## L10  CHU KY

Toi xac nhan da dien BANG DU DOAN (L5) va BON NHANH (L8) TRUOC khi
thuc hien bat ky phep do nao cua Phase L.

Ky: ______________   Ngay: __________
