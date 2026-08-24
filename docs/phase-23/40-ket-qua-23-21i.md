# 40 -- Lesson 23.21i: ket qua do duoc, va bon du doan bi bac bo

Ngay     : 2026-08-24
Amendment: `A060-amendment-60.md`
Pham vi  : Viec 1 (truc SLA cho `decision_error`), Viec 2 (tang `PENDING`),
           Viec 4 (phan quyet `L51`). Viec 3 KHONG lam -- xem muc 6.

## 1. Moi truong

```text
python3           -> KHONG co numpy  (moi lenh se that bai ngay)
.venv/bin/python  -> numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1
```

## 2. Ket qua CHINH -- ba con so dung duoc ngay

### 2.1. Hinh phan ra sai so MIEN NHIEM voi S14 (`G23-203`)

```text
cot            max|diff| qua doi truc SLA
rms_e_model     0.00000000     <- dung bang khong
rms_e_stale     0.00000000     <- dung bang khong
cov_e           0.00000000     <- dung bang khong
```

450/450 hang ghep cap; `w_loss` doi tu 9 gia tri noi sinh (1245.6 .. 4722.7)
sang 5000 ngoai sinh. Co che CAU TRUC: `e_model`/`e_stale` tinh tren delay
thuan, khong qua ham chi phi.

**Con so thu tu trong abstract viet duoc ngay.**

### 2.2. Doi chung cheo hai duong code doc lap (`G23-204`, dang sua lai)

```text
max|d_sla|  <=  S_pivotal        10/10 cell, tren moi z
```

`decision_error_v2` (Phase 20R) va `sla_exogenous` (23.21) dong y tren mot
BAT DANG THUC DINH LUONG. Phan tach LIVE vs KHONG-LIVE hoan toan:

```text
min max|d_sla| tren LIVE       = 0.077299
max max|d_sla| tren KHONG-LIVE = 0.003007      -> cach nhau 25.7 lan
```

### 2.3. Cai chan co suc phan biet (`G23-206`)

```text
16 failed, 30 passed, 5 skipped
```

Dung 16 -- bang so file `PENDING/` khong co `validity`.

## 3. Bon du doan cua ke hoach BI BAC BO bang do

Muc nay la phan dang gia nhat cua lesson. Ca bon deu duoc phat hien bang cach
DO, khong phai bang cach doc.

### 3.1. "`G23-202` se PASS"  ->  **FAIL theo van ban da ky**

Nguong da ky `equals == True`. Thuc te `False`. Nhung:

```text
19/22 cot BIT-EXACT (gom TAT CA cot muc quyet dinh)
 3/22 cot lech <= 3.11e-15  (rms_e_model, rms_e_stale, cov_e)
```

Va ban LIVE cu KHOP digest tien dang ky 21R (`5e4d4797...`) -> khong phai
nham file. Day dung la `L71`. Ghi `L74`, khong noi nguong.

### 3.2. "`d_sla ~ 0` trung tap `COLLAPSED`, >= 5/5"  ->  **4/5, gia thuyet sai**

Hai cho gia thuyet quen:

```text
(a) ba cell TRIVIAL cung cho d_sla = 0   (0 - 0, cung co che voi 1 - 1)
(b) poisson@0.925 co S_collapsed = 0.9913 != 1  ->  d_sla = 3.0e-03
```

Dang dung khong phai phep so tap ma la bat dang thuc -- va no PASS 10/10.

### 3.3. "parquet khong mang duoc metadata"  ->  **chi dung mot nua**

```text
truth_table.parquet  ->  ['pandas', 'phase', 'truth_field', 'truth_field_note']
```

`build_truth_table.py` DA ghi metadata tuy y qua `pyarrow`. Sidecar VAN la
lua chon dung (khop mau Phase 21R, khong bat moi builder doi sang pyarrow)
nhung ly do la NHAT QUAN chu khong phai BAT KHA THI.

### 3.4. "`M-136` giai phong ngay, 15 phut may"  ->  **BI CHAN, ly do MOI**

```text
w_loss =  1250  ->  objective ratio=1 parity fail: 2.815e-02
w_loss =  5000  ->  chay duoc
w_loss = 20000  ->  objective ratio=1 parity fail: 8.347e-03
```

`w_loss` DA BI NUONG vao calib parquet (`calib_set_*_report.json` ghi
`w_loss = 5000.0`; cac cot `a_twin`, `a_star`, `regret`, `gap_true` deu suy
tu ham chi phi). No la tham so SINH, khong phai tham so CHAM DIEM.

`L51` van duoc tach dung khoi `M-136` -- `M-136` khong can parquet LICH SU.
Nhung no can calib set DUNG LAI o TUNG `w_loss`. Ghi `L77`.

> Cai chan `parity > 1e-12` da TU CHOI sinh ra ba con so sai mot cach im lang.
> Neu no khong co, `M-136` da "xong" voi ba so vo nghia.

## 4. Phan quyet artifact

```text
LIVE/phase-20R/   + decision_error_by_age_by_regime_slaB.parquet   (+ sidecar)
                  + truth_table_report.json                        (sidecar, MEASURES)
                  - decision_error_by_age_by_regime.parquet        -> SUPERSEDED

LIVE/phase-23/    + 7 artifact promote (nhan SUY RA = exogenous_g114_S-B)
                      rho_grid_main / _sigma_fixed / _sigma_low
                      sigma_rho_plane
                      sla_exogenous_S-B / _S-B_ci / _wave4

SUPERSEDED/       + eight_cell_sweep_U3_measured_v7.json  (w_loss noi sinh, S14)

PENDING/          9 file con lai -- va do la DUNG, xem `G23-209`
SMOKE/            bo lam viec cua M-136 (khong phai ket qua)
```

**7 promote, khong phai 15.** `S-A`/`S-C` la canh tay do nhay (bo ba SLA khac
han) va nam quet SPAN truc (`a_sweep`, ba `t_loss_*`, `w_loss_sensitivity`)
khong dung tren MOT truc nao -- phep doi chieu noi dung phat hien tu dong.

## 5. Loi ma nguon da sua

```text
L75  cert/eight_cell_sweep.py ghi provenance.inputs va NC_F_w_loss_source
     bang HANG SO SLA_ARTIFACT thay vi tham so `sla_artifact`.
     -> artifact `_slaB` co w_loss = 5000 o moi cell (da doc manifest ngoai
        sinh) nhung KHAI doc sla_calibration.json (truc S14). DA SUA ca hai cho.

L73  he ten file amendment `00z*` con 4 cho -> doi sang `A0NN-`.

L76  h9_separability / plot_decision_error_v2 van dung tren truc DEPRECATED;
     duong da doi theo file de chung chay NGUYEN.
```

## 6. KHONG LAM: Viec 3 (`live_region_sweep`, Lesson 23.21h)

Da xac minh ca bon khiem khuyet ton tai dung nhu mo ta:

```text
(1) cert/live_region_sweep.py:115  _calibrate() goi SLA.calibrate_cell  (S14)
(2) dong 51-54  bon parquet Dot 4 KHONG co tren dia
(3) dong ~324   --calib-template la co CHET (run_sweep() khong nhan tham so)
(4) dong 42-43  SLA_OUTPUT/OUTPUT ghi thang vao SUPERSEDED/
```

KHONG bat dau, va co chu y:

- No can amendment `23-61` rieng (chua ky).
- Gate bat buoc `G23-212` (NC am: nap manifest 10 cell cu -> tai tao
  `eight_cell_sweep_..._slaB.json` bit-exact) KHONG chay duoc: artifact doi
  chung do chinh la file dang bi grandfather vi `L75`, va sinh lai no bi chan
  boi `L51` (thieu 4/8 parquet phase-22).
- Lam Viec 3 ma bo qua `G23-212` la tin con so 12 cell ma khong co doi chung
  am -- dung dieu ma ke hoach canh bao la "de bo nhat va can nhat".

**Thu tu dung: mo `L51` (dung lai calib set) -> sinh lai `_slaB` -> `G23-212`
-> roi moi Viec 3.**

> ⚠️ **MUC 6 DA LAC HAU -- xem muc 9.4.** Thu tu vua neu la mot DEADLOCK THU
> HAI cung dang `L67`: mat dau ("mo `L51`") khong bao gio giai duoc, vi 5/9
> dau vao mat vinh vien. `G23-212a` (do sau vong review) di vong duoc: no
> khang dinh TUONG DUONG DUONG CODE tren bo calib phase-21R co digest ghim,
> thay vi tai tao artifact LICH SU. Da PASS 8/8 cell.
> **Viec 3 KHONG con bi chan.** Van chua lam -- can amendment `23-61`.

## 7. Trang thai test

```text
test_no_stale_axes + test_no_dangling_parquet_refs + test_phase23_gate_ledger
+ test_limits_ledger + test_cli_flags_are_wired      201 passed, 37 skipped

bo day du:  pytest test/ -q -m "not live"            5 failed, 1389 passed,
                                                     42 skipped  (38 phut)
```

### 7.1. Hai fail LA CUA LESSON NAY -- da sua

```text
test_phase23_gate_ledger::test_every_status_is_in_locked_vocabulary
    -> toi da viet 'FAIL→PASS', 'PASS (7/7, KHAC du doan 15)', 'KHONG DO DUOC'.
       Ba chuoi nay KHONG nam trong tu vung KHOA. Da sua ve
       ADJUDICATED / PASS / NOT_RUN. Sac thai chuyen vao cot evidence.
test_phase23_gate_ledger::test_every_gate_id_mentioned_in_repo_is_in_the_ledger
    -> `G23-212` duoc vien dan trong doc nhung chua co dong trong GATES.md.
       Da them (NOT_RUN, bang chung '-' theo `test_evidence_absent_when_not_run`).
```

So gate cua repo bat dung hai loi cau tha cua chinh lesson nay. Ghi lai vi do
la mot doi chung duong ngoai y muon: cai chan hoat dong tren nguoi viet no.

### 7.2. Ba fail con lai KHONG PHAI cua lesson nay -- da chung minh

```text
test_phase23_lesson237_structure::test_refactor_khong_doi_mot_con_so_nao
    [lesson23_7_range_calibration], [lesson23_7_feasibility]
test_phase23_lesson237_feasibility::test_end_to_end_tai_lap_duoc
    ("assert out['M12_M15_feasible'] is True" -> False)
```

Ca ba deu mang mark `slow`, nen `pytest` mac dinh (`-m "not slow"`) BO QUA
chung; chi lo ra khi chay `-m "not live"` (co CI dung). Doi chung co kiem soat:

```text
co thay doi cua lesson nay :  3 failed, 34 passed  (528.59 s)
STASH 6 file ma nguon      :  3 failed, 34 passed  (531.52 s)   <- Y HET
```

=> **CO TRUOC lesson nay.** Khong sua o day (khong thuoc pham vi da ky), chi
bao cao.

> Bay da vap phai va dang ghi lai: lan doi chieu DAU TIEN chay bang `pytest`
> mac dinh, nen ca hai ve deu DESELECT dung ba test do va deu "34 passed".
> Ket luan rut ra luc do ("ba fail la cua toi") la SAI. Phai lap lai voi
> `-m "not live"` moi so sanh dung. Mot phep doi chieu ma ca hai ve khong
> chay dieu can do thi khong phan biet duoc gi -- dung lop loi voi PASS RONG
> o muc 2 cua `37-pending-tier-adjudication.md`.

## 8. Bon cau hoi tu kiem -- tra loi

1. **`rms_e_model` lech 0 con `err_model` lech 0.0250?** `err_model` la ti le
   QUYET DINH SAI (`a_now != a_truth`), di qua `argmin` cua ham chi phi nen
   `w_loss` doi thi no doi. `rms_e_model` la sai so DELAY (`d_true - d_fresh`),
   khong qua ham chi phi. Cung ten "model", hai dai luong khac han.
2. **Sinh `validity` truoc roi sua test thi mat gi?** Mat DOI CHUNG DUONG cua
   chinh bo test: khong con dau vao nao lam cai chan moi DO, nen khong biet no
   co kich hoat duoc khong. Test se xanh, va cai xanh do vo nghia y het cai
   xanh cu.
3. **Vi sao `M-136` khong can du lieu goc con `G23-212` thi can?** `G23-212`
   khang dinh mot menh de ve mot GIA TRI ("so moi trung so cu") -> can chinh
   gia tri cu. `M-136` khang dinh mot menh de ve QUAN HE giua ba lan chay ->
   moi hang so dung chung triet tieu. **Nhung** (do duoc trong lan nay) dieu
   do chi dung voi tham so CHAM DIEM; `w_loss` la tham so SINH nen van phai
   sinh lai (`L77`).
4. **Neu `G23-204` FAIL thi ket luan gi?** No DA FAIL. Hai giai thich thay the:
   (a) mot trong hai script tinh sai, (b) gia thuyet sai. Doi chung giet (a):
   neu mot script sai thi bat dang thuc `d_sla <= S_pivotal` phai bi vi pham o
   dau do -- no khong bi vi pham o 10/10 cell tren 9 muc `z`. Con lai (b), va
   (b) duoc xac nhan bang co che: `TRIVIAL` cung cho hieu 0 vi cung ly do cau
   truc voi `COLLAPSED`.

---

# 9. Vong review doc lap (cung ngay) -- 5 muc, va MOT phat hien lat nguoc phan quyet

## 9.1. Xac nhan tu review

`G23-203` (= 0 tren numpy 2.4.4 lan 2.2.6 -> bat bien KHONG phu thuoc moi
truong), `G23-204` (10/10, 25.7 lan, khop tung chu so), `L75`, `L77`. Review
con bo sung co che cho `G23-204`: bat dang thuc co CHUNG MINH (twin chi gay
them vi pham o buoc PIVOTAL; buoc TRIVIAL/COLLAPSED triet tieu), nen no nen la
mot BO DE trong paper chu khong phai mot bang so.

## 9.2. `G23-202` KHONG TAI LAP DUOC tren may khac -- tieu chi da ky la SAI

```text
             numpy    ket qua
toi (WSL2)   2.2.6    3 cot lech 3.11e-15  -> FAIL
review       2.4.4    22/22 bit-exact      -> PASS
```

Cung commit, cung artifact, hai phan quyet trai nguoc. Mot tieu chi cho hai
phan quyet khong phai mot tieu chi.

Co che: review de xuat "thu tu thu gon". Toi thu tai hien tren mang 1-D:
**KHONG lech** (np.mean == math.fsum == ban xao tron). Thu lai tren dung dang
that `(200000, 4)`:

```text
mean() toan mang       lech 0
mean axis=1 roi mean   lech 4.441e-16
mean axis=0 roi mean   lech 8.438e-15
Fortran-order          lech 4.441e-16
```

=> co che DUNG, nhung chi lo ra o mang 2-D. Dai 4.4e-16..8.4e-15 bao tron
3.11e-15 da quan sat. `G23-219` mo voi hai nhom:

```text
NHOM A  so nguyen/bool (.mean() cua 0/1)      -> bit-exact KHA CHUYEN, ky == 0
NHOM B  float qua PHEP THU GON                -> ky 32*eps*sqrt(n)*|v| = 1.18e-11
```

`G23-202` GIU nguyen phan quyet FAIL. Khong sua thanh PASS -- so ghi lai rang
mot tieu chi sai da ton tai va bi thay the.

## 9.3. ★ `L51` bi LAT: digest lich su KHONG mat

Khi ghim digest theo yeu cau cua review, toi doi chieu voi artifact cu va phat
hien `provenance.inputs` cua `eight_cell_sweep_U3_measured_v7.json` (git_hash
`05b597f5`) DA LUU sha256 cua ca 9 dau vao.

```text
3 file con song   KHOP digest goc      -> BAN GOC
1 file con song   KHAC digest goc      -> KHONG PHAI BAN GOC  ★
5 file            mat                  -> khong doi chieu duoc
```

**Bay suyt roi vao:** review de xuat dung BON cell cho `G23-212a`, trong do co
`poisson@0.700`. File do tren dia KHONG phai ban goc (`ec49deb8...` ->
`2267423d...`). Dung no lam moc doi chung se rot dung cai bay `L51` canh bao.
Chi phat hien duoc vi co digest de doi chieu.

`L51` tach thanh `L51a` (digest: khong mat), `L51b` (du lieu: mat 5/9, vinh
vien), `L51c` (xac minh: 3 goc / 1 khong / cam tai dung). Ket luan cuoi khong
doi, nhung LY DO doi han -- va van ban Threats to Validity da phai viet lai
(`39-l51-adjudication.md` muc 6.3).

## 9.4. `G23-212a`: 8/8 cell, khong phai 3 hay 4

Ke ca 3 file GOC cung khong dung duoc: chung o SAI TRUC (`w_loss` noi sinh),
nen ghep voi manifest S-B lam parity fail 6.312e-03 -- co che `L77`. Duong
dung la bo phase-21R (`w_loss = 5000`, 8/8 co digest ghim trong sidecar).

```text
G23-212a  8/8 cell, 2340 truong, NHOM A lech 0, NHOM B lech 0  -> PASS
doi chung duong: nhieu 1e-15 vao mot truong NHOM A -> bat duoc
ve A: results/RAW/phase-23/g23_212a_before.json
```

**Viec 3 khong con bi chan.**

## 9.5. Cai chan cua toi QUA tren may toi, DO tren clone sach (`L79`)

Review chay tren clone sach: `1 failed` thay vi `201 passed`. Nguyen nhan:
`os.path.exists` hoi "co tren MAY TOI" chu khong "co tren CLONE SACH", va file
rac local LAM IM cai chan. Da sua sang `git ls-files`. Do lai:

```text
20 tham chieu tren 9 script se chet tren clone sach   (review uoc 5)
```

Cung lop loi voi PASS RONG toi vua vach o Viec 2 -- lan nay nan nhan la nguoi
viet cai chan.

## 9.6. `L78` -- `pin()` fail quiet

`pin()` nuot `OSError`, tra `sha256: None`, lam DUNG NGUOC docstring cua chinh
no. Da sua: mac dinh NEM; `pin(p, allow_missing=True)` de tuong minh tai diem
goi. 191 test lien quan van xanh sau khi sua.

## 9.7. Trang thai GAP con lai -- chi ban lam duoc

```text
7 parquet Phase 22 (468 MB)  git_tracked = 0/7
16 parquet phase-21R          git_tracked = 0/16
```

Digest DA ghim (`results/RAW/phase-22/SURVIVING_CALIB_DIGESTS.json`), nhung
**digest khong thay the duoc DU LIEU**. Sao luu ra ngoai o dia. Neu o dia hong
truoc do: `L51b` tu 5/9 thanh 9/9, `G23-212a` mat ve A, Viec 3 khong bao gio
lam dung duoc.
