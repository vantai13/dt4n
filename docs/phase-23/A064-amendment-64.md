# AMENDMENT 23-64 -- Truc m-hat: do lai co so, va thay `none` bang `selective`

Ngay ky : 2026-08-24
Lesson  : 23.22 (Task A0 + Task A)
Loai    : TIEN DANG KY (PRE-REGISTRATION) -- chua chay mot dong nao cua
          cert/taxonomy_audit.py; chua mo mot parquet LIVE nao cho muc dich nay
Moc     : sau amendment 23-63, truoc commit dau tien cua Lesson 23.22

## 0. Disclosure

Bon dai luong duoi day DA duoc nhin truoc khi ky, va duoc khai o day de khong
bi dem hai lan:

  (a) `axis_remeasure_impact_wave1.json` (artifact LIVE, Lesson 23.20) chua
      `q_new` theo z_bin cho 8 cell. Ti so max/min cua bon so do da duoc doc
      va nam trong [1.5204, 1.6077]. Vi vay M-183 duoi day KHONG phai mot du
      doan mu -- no la mot XAC NHAN tren dai da xem. Nhan: [DA XEM].

  (b) `conditioning_audit_poisson_0.925.json` (SUPERSEDED, truc CU) chua bang
      qhat 4x4 tai `qhat_budget_ratio_M5.per_mondrian_cell`. Da doc. Vi vay
      M-185 mang nhan [CO CHE, DA XEM TREN TRUC CU] -- du doan la co che GIU
      NGUYEN khi doi truc, khong phai gia tri.

  (c) `calib_set_poisson_0.925_U3_measured_v7_report.json` chua
      `n_calib_blocks = 500`. Da doc va da xac minh lai truc tiep tren parquet:
      500 block calib, 500 block test, 999 495 hang, `z_bin`/`m_hat_bin` deu
      co dung bon muc {0,1,2,3}.

  (d) `docs/phase-22/05-selective-conformal.md` bang muc 2 va muc 3 da doc:
      tai kappa=1 tren poisson@0.925, `none` cho viol|acc = 0.1214,
      `mondrian` 0.0884, `selective` 0.0849, `fcr` 0.0160.

CHUA XEM: so block hieu dung cua tung o Mondrian tren parquet LIVE; do rong
CI cua qhat duoi hai taxonomy; bat ky ket qua nao cua ba bien the tren truc
`measured_v7_uniform`. M-181, M-182, M-184, M-186, M-187 la du doan THAT.

## 1. Van de -- hai lech giua ban ke hoach va trang thai repo

`PHASE_23_v3.md` muc "LESSON 23.22 / Co so" trich hai so:

    spread_z = 2.1232 ,  spread_m = 1.1188

Nguon da xac minh: `docs/phase-23/00zf-amendment-30.md` dong 176-177
(`M-1` = `spread_m` = 1.1188, `M-2` = `spread_z` = 2.1232, ca hai nhan
[TAT DINH]). Do tren `Z_EDGES_LEGACY = (0.055, 0.10, 0.20, 0.30, 0.5501)`.

Truc do da bi THAY THE o amendment 23-49c (`measured_v7_uniform`,
`Z_EDGES_V7 = (0.100, 0.241, 0.366, 0.491, 0.641)`), va
`measurements/aoi_model_v7.py` ghi ro luoi cu VO tren truc moi. Artifact goc
nam o `results/SUPERSEDED/`.

    LECH 1  Co so thiet ke cua 23.22 dung so tu truc DA BI THAY THE.

`PHASE_23_v3.md` muc "[A]" chi dinh:

    C3: z_bin x m_hat_bin (16 o)  ->  z_bin (4 o)

Da xac minh trong `cert/config_matrix.py:111`:

    def _keys(post): return ["z_bin","m_hat_bin"] if post=="mondrian" else ["z_bin"]

Nghia la bo truc `m_hat` khoi taxonomy = doi `post` sang BAT KY gia tri nao
khac `"mondrian"`. Bo truc ma KHONG doi thu tuc chinh la `post = "none"`. Thu
tuc do da duoc do o Lesson 22.4 va cho `violation_given_accept = 0.1214 >
alpha = 0.10` tai kappa=1 -- tuc FAIL G22-6.

    LECH 2  "[A]" nhu viet se dao nguoc ban va post-selection cua Phase 22.

## 2. Sua duoc ky

### 2.1. Task A0 -- do lai co so tren truc da duyet (BAT BUOC, truoc Task A)

Chay `cert/taxonomy_audit.py` tren ba cell da tien dang ky tu Lesson 23.7:

    poisson@0.925 (chinh) , poisson@0.850 , h2@0.700

doc tu `results/LIVE/phase-21R/calib_set_{mode}_{rho:.3f}_U3_measured_v7.parquet`
(truc AoI `measured_v7_uniform`, truc SLA `exogenous_g114_S-B`). Da xac minh
ca 12 parquet U3 co mat.

Khong cell nao duoc them vao sau khi thay so. Chin cell LIVE con lai
(`h2@{0.650,0.675,0.850,0.925,0.960}`, `poisson@{0.700,0.875,0.900,0.960}`)
duoc chay CUNG luc va bao cao lam ROBUSTNESS, khong duoc dung de chon ket
luan chinh.

### 2.2. Task A -- ba bien the, khong phai hai

    V-M  post = "mondrian"    keys = [z_bin, m_hat_bin]   <- hien hanh
    V-N  post = "none"        keys = [z_bin]              <- "[A]" nhu ke hoach viet
    V-S  post = "selective"   keys = [z_bin]              <- THAY THE duoc de xuat

V-N duoc chay va bao cao NHU MOT DOI CHUNG DUONG: no PHAI vo bao phu tren
tap accept. Neu no KHONG vo, gia thuyet co che cua muc 3 bi bac bo va
23.22 phai duoc thiet ke lai.

Moi bien the giu `simultaneous = True` va `multiplicity = "bonferroni"`, tuc
`alpha_each = alpha/3 = 0.0333...` (da xac minh bang
`CM._alpha_each(0.10, 3, True, "bonferroni")`). Khong doi mot tham so nao khac.

Luoi kappa ky truoc: `(0.0, 0.25, 0.50, 1.00, 2.00)`. Diem VAN HANH CHINH la
`kappa = 1.00`; `kappa = 0.0` va `2.00` la hai diem doi chung (muc 5).

## 3. Gia thuyet co che duoc ky

    H-A  Hieu ung cua truc `m_hat` KHONG deu tren bon o. No tap trung o
         o cao nhat `m_hat_bin = 3` -- dung o ma tap ACCEPT tap trung vao --
         VA no TUONG TAC voi z. Khi do `spread_m` DANH GIA THAP tam quan
         trong cua truc `m_hat`, vi

             spread_m = max_m mean_z q(z,m) / min_m mean_z q(z,m)   TI SO CUA TRUNG BINH
             M-185    = mean_z [ q(z,3) / mean_{m<3} q(z,m) ]       TRUNG BINH CUA TI SO

         `spread_m` bi CHI PHOI boi cac z_bin co `qhat` LON; neu hieu ung
         `m_hat` nam o cac z_bin co `qhat` NHO thi no bi PHA LOANG.

> ⚠️ SUA TRUOC KHI KY. Ban nhap dau (theo ban review) viet H-A la
> *"profile BIEN lam nhoe mot hieu ung don"*. **DIEU DO SAI, va da bi bac bo
> bang do truoc khi ky.** `spread_profiles` trung binh theo `(z, slot)` va
> GIU NGUYEN truc `m`, nen mot hieu ung 1.20x don o `m=3` hien ra DAY DU la
> 1.20 tren `spread_m` -- khong nhoe chut nao.
>
> Do duoc (`test_spread_m_and_M185_agree_when_effect_is_uniform_in_z`):
>
>     hieu ung 1.20x don o m=3, DEU tren moi z:  spread_m = 1.2000 = M-185
>
> Co che THAT la ti-so-cua-trung-binh vs trung-binh-cua-ti-so, va no chi lo ra
> khi CO TUONG TAC z x m. Do duoc
> (`test_M185_diverges_from_spread_m_under_z_by_m_interaction`):
>
>     base qhat [100,10,10,10], hieu ung 1.5x chi o ba z_bin nho:
>         spread_m = 1.1154   M-185 = 1.3750   -> lech 1.23 lan
>
> He qua cho viec doc ket qua: neu `M-185 ~ M-184` thi KHONG co tuong tac
> z x m, va M-185 khong them thong tin -- do la mot ket qua hop le, phai bao
> cao nhu vay chu khong duoc goi la "xac nhan H-A".

    H-B  Duoi chia block, don vi exchangeability la BLOCK -- da xac minh
         `_qhat` dung `n_eff = sub["block_id"].nunique()`. Vi mot block
         (b = 5*tau) trai qua nhieu gia tri z va m_hat, gan nhu moi block
         cham moi o Mondrian. Do do bo truc `m_hat` lam so HANG moi o tang
         ~4x nhung so BLOCK hieu dung chi tang vai phan tram.
         ==> Loi ich "4x du lieu" ma ban ke hoach neu la KHONG DUNG o tang
             MUC conformal; no chi con o tang uoc luong phan vi.

    H-C  Loi ich chac chan cua viec bo truc `m_hat` KHONG phai co mau, ma la
         doi mot XAP XI (Mondrian tren bien chon loc, gay tu kappa=2 theo
         bang Lesson 22.4) lay mot LAP LUAN CHAT (hieu chuan tren tap chon).

## 4. Bang du doan -- BAN KHOA

| ID | Dai luong (ba nhan) | Nhan | Cham o | Diem |
|---|---|---|---|:--:|
| M-181 | `n_blocks` trung binh moi o Mondrian (16 o), calib; **[440, 500]** | [CO CHE] | 3 cell | CO |
| M-182 | ti so `n_blocks(4 o) / n_blocks(16 o)`; **[1.00, 1.15]** | [CO CHE] | 3 cell | CO |
| M-183 | `spread_z` tren truc v7, taxonomy 16 o; **[1.45, 1.70]** | [DA XEM] | 3 cell | KHONG |
| M-184 | `spread_m` tren truc v7; **[1.05, 1.30]** | [NGOAI SUY] | 3 cell | CO |
| M-185 | `qhat[m3] / mean(qhat[m0..m2])` trung binh theo z_bin; **[1.10, 1.30]** | [CO CHE] | 3 cell | CO |
| M-186 | ti so do rong CI95 cua `qhat` slot-1, (4 o)/(16 o); **[0.50, 1.00]** | [NGOAI SUY] | 3 cell | CO |
| M-187 | tai kappa=1: `viol\|acc` cua V-N **> 0.10** VA cua V-S **<= 0.10** | [CO CHE] | 3 cell | CO |

Bay dong. Sau dong duoc cham diem (M-183 khai [DA XEM] nen khong cham).

### 4.1. Quy tac doc M-186

`M-186 <= 1.00` xac nhan 4x hang co mua duoc do on dinh. `M-186` gan 1.00
xac nhan H-B o dang manh: tuong quan noi block gan hoan toan, 4x hang khong
mua duoc gi. CA HAI ket qua deu hop le va deu duoc bao cao. Khong duoc doi
dai sau khi xem.

### 4.2. Quy tac doc M-187

Day la dong QUYET DINH. Neu V-N khong vo (`viol|acc <= 0.10`) thi H-A bi bac
bo tren truc moi, va phai ghi ro rang tuong quan `m_hat`--`s` da bien mat khi
doi truc AoI -- mot phat hien can dieu tra rieng, khong duoc lam ngo.

## 5. Gate

| Gate | Noi dung | Nguong |
|---|---|---|
| G23-230 | `taxonomy_audit` chay tren 3 cell chinh, artifact co `validity` block hop le va `git_dirty=false` | tat/bat |
| G23-231 | M-181 va M-182 trong dai | 3/3 cell |
| G23-232 | M-184 va M-185 trong dai | >= 2/3 cell |
| G23-233 | M-186 trong dai, CI tinh bang paired block bootstrap >= 2000 lan lay mau | 3/3 cell |
| G23-234 | M-187: V-N vo VA V-S khong vo, tai kappa=1 | 3/3 cell |
| G23-235 | Doi chung AM tai kappa=0: (a) `acceptance == 1.0` o ca ba bien the, (b) V-N va V-S TRUNG BIT (`viol\|acc` va `qhat_slot1_mean` lech < 1e-12). V-M KHAC chung la ky vong | 3/3 cell |
| G23-236 | Doi chung DUONG: V-M tai kappa=2 PHAI vo bao phu (tai lap ket qua Lesson 22.4 tren truc moi) | >= 2/3 cell |
| G23-237 | Cai gia cua V-S: `acceptance(V-S)/acceptance(V-M)` tai kappa=1 duoc BAO CAO kem CI, khong lam tron | tat/bat |
| G23-238 | 9 cell robustness chay va bao cao; khong cell nao duoc dung de chon ket luan chinh | tat/bat |

### 5.1. SUA `G23-235` TRUOC KHI CHAY THAT -- va cai gia phai tra

Ban nhap dau cua `G23-235` doi CA BA bien the cho `viol|acc` bang nhau den
1e-12 tai kappa=0. Mot lan CHAY NHAP (`--n-boot 20 --allow-dirty`, artifact
vut o `/tmp`, KHONG ghi vao `results/`) cho thay no FAIL 3/3 cell voi
`viol_spread` = 1.35e-03 / 6.00e-06 / 4.17e-03.

Truy nguyen: do la mot DOI CHUNG SAI THIET KE, khong phai loi code.

```text
_accept = (m_hat >= kappa*qhat);  tai kappa=0 -> (m_hat >= 0)
    -> doc lap taxonomy -> tap accept TRUNG NHAU -> acceptance = 1.0  (DUNG,
       da do: 1.0000000000 o ca ba bien the, ca ba cell)
viol|acc = P(score > qhat | accept);  qhat PHU THUOC taxonomy
    -> V-M (16 o) va V-N/V-S (4 o) co qhat khac -> viol PHAI khac
    -> bat chung bang nhau la bat mot dieu SAI
```

Thay bang hai khang dinh dung va SAC HON:

```text
(a) acceptance == 1.0 o ca ba          -- quy tac accept doc lap taxonomy
(b) V-N va V-S TRUNG BIT tai kappa=0   -- ca hai keys=[z_bin], va vong diem
                                          bat dong cua `selective` bat dau tu
                                          TOAN BO tap roi `_accept` nhan het
                                          nen no dung yen ngay vong dau
```

Da do o lan chay nhap: `|viol_N - viol_S| = 0.000e+00` va
`|qhat_N - qhat_S| = 0.000e+00` tren CA BA cell. (b) chat hon ban cu vi no
doi TRUNG BIT chu khong phai "trong dung sai".

> **Cai gia phai tra, khai ro:** sua nay duoc thuc hien SAU khi da chay nhap,
> tuc SAU khi nhin so. No la mot sua CHUAN DOAN (mot doi chung hoi mot dieu
> khong the dung), khong phai noi nguong cho mot du doan. Nhung de khong ai
> phai tin loi hua do:
>
>   * `G23-235` mang nhan **[SUA SAU KHI XEM]** va **KHONG duoc dem diem**.
>   * Bay dong `M-181..M-187` KHONG duoc dong vao. Chung giu nguyen dai da ky.
>   * Lan chay nhap dung `--allow-dirty`, ghi ra `/tmp`, khong tao artifact
>     nao trong `results/`.

## 6. Nhanh fail da dinh truoc

    Neu G23-234 FAIL vi V-S cung vo:
        -> khong quay ve V-M am tham. Chay them V-F (`post="fcr"`) va bao cao
           ca ba. Ket luan hep: tren truc moi, khong thu tuc 4-o nao du; truc
           `m_hat` la CAN THIET. Do la mot ket qua, khong phai that bai.

    Neu G23-236 FAIL (V-M khong vo o kappa=2):
        -> ket qua Lesson 22.4 khong chuyen sang truc moi. Dung 23.22, mo mot
           lesson kiem toan rieng. KHONG duoc di tiep.

    Toi da HAI vong. Moi vong sua dung mot thu.

## 7. L89 -- han che moi duoc ghi

L89  Co so thiet ke cua Lesson 23.22 trong `PHASE_23_v3.md` trich
     `spread_z=2.1232` / `spread_m=1.1188` tu `00zf-amendment-30.md` dong
     176-177, do tren `Z_EDGES_LEGACY`. Truc do da bi thay the o amendment
     23-49c. Ban ke hoach ngoai repo KHONG duoc sua; anh xa sang so do lai
     song o day va o
     `results/LIVE/phase-23/taxonomy_audit.json::superseded_basis`.

> Ghi chu cap ma: ban review de xuat `L90`. `LIMITS.md` dong 128 ghi
> *"So ke tiep duoc cap: **L89**"* va ma lon nhat da cap la `L88`. Dung
> `L90` se de trong `L89` va lam `test_limits_ledger` mat tinh lien tuc.
> Da cap `L89`.

## 8. `G23-216` -- khe da duoc truy nguon va dang ky

Review doc lap chi ra `G23-216` khong xuat hien o dau trong repo. DA TRUY:
day la mot khe do CHINH Lesson 23.21i tao ra. Ke hoach cap `G23-216` cho
*"Dot 1 dung lai: 16/16 job qua bon cong nhanh"*, nhung phep do do khong chay
duoc (`M-136` bi chan boi `L77`), va dai `G23-215/217/218` duoc cap bo qua no.

Da dang ky `| G23-216 | 23.21i | NOT_RUN | - |` de khong ai tai su dung ma.

> Ghi lai mot doi chung duong NGOAI Y MUON: ban nhap dau cua amendment nay
> viet *"vung 216 KHONG duoc dung"* -- va chinh cau do lam
> `test_every_gate_id_mentioned_in_repo_is_in_the_ledger` DO. Khong viet duoc
> cau "dung dung ma X" ma khong dang ky X. So gate cua repo tu dong bien mot
> ghi chu thanh mot muc so sach. Cung ho voi hai lan no bat loi cau tha cua
> 23.21i.

Dai moi bat dau tu `G23-230`.

## 9. Output

    code      cert/taxonomy_audit.py
    test      test/test_phase23_taxonomy_audit.py
    artifact  results/LIVE/phase-23/taxonomy_audit.json
    doc       docs/phase-23/43-taxonomy-audit.md   (viet SAU khi chay)
