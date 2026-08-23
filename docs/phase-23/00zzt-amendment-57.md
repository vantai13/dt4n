# AMENDMENT 23-57 -- Pha DEADLOCK so sach: noi truc SLA ngoai sinh vao duong ong

Ngay ky : 2026-08-23
Tag     : amendment-57
Lesson  : 23.21f
Loai    : PHA CHU TRINH CHO + TIEN DANG KY
Prereq  : amendment-56, Lesson 23.21 dong (`24db43e`)

## 1. Van de: DEADLOCK trong so no

Mot vong kiem toan doc lap phat hien Lesson 23.21 KHONG dong duoc, va ly do
la mot CHU TRINH CHO:

```text
G23-158 (bat buoc, 23.21)  "L40 va L41 dong; go nhan CONDITIONAL_ON_SLA_AXIS"
    can  ->  ket qua HA NGUON duoi SLA moi
    can  ->  dung lai calib_set
    tuc  ->  G23-141 / G23-142

G23-141 / G23-142 (DEBT, 23.20C)
    GATES.md ghi: "Bi chan boi S14 -- xem L41; mo lai SAU Lesson 23.21"
    tuc  ->  cho 23.21 dong
    tuc  ->  cho G23-158

    A cho B, B cho A.  DEADLOCK.
```

Khong lesson nao sai. Khong gate nao sai. Nhung he DUNG IM.

```text
NGUYEN NHAN KY THUAT: `S14` da duoc sua o tang MODULE
(`measurements/sla_exogenous.py`) nhung CHUA duoc noi vao tang DUONG ONG.
`cert/build_calib_set_v3.py` CLI khong co `--sla-spec`; `--calibration` mac
dinh van tro `results/LIVE/phase-20R/sla_calibration.json`, von mang nhan
`self_calibrated` / `DEPRECATED`.
Chinh comment o `build_calib_set_v3.py:127` da ghi truoc dieu nay tu
amendment 23-49c.
```

## 2. Hai loi so sach di kem, phat hien cung luc

```text
(a) `35-close-23-21.md` muc 6 ("No mang sang 23.22") liet ke `G23-174` va
    `G23-141`/`G23-142`, NHUNG BO SOT `G23-156` va `G23-158`.
    Do duoc: `grep -c "G23-156\|G23-158" 35-close-23-21.md` = 0.
    Ca hai deu con `NOT_RUN`, va `G23-158` la BAT BUOC.

    => Van ban dong lesson va `GATES.md` duoc cap nhat bang tay o HAI cho,
       khong co test nao buoc chung khop ve TAP GATE MANG SANG.
    => `L66`.

(b) Khong co co che nao chan mot chu trinh cho giua cac mon no. Moi `DEBT`
    duoc phep ghi "mo lai sau X" ma khong ai kiem `X` co phu thuoc nguoc
    vao chinh mon no do khong.
    => `L67`.
```

## 3. Canh bi CAT

```text
QUYET DINH: cat canh `G23-141`/`G23-142`.
LY DO     : chung KHONG can Mininet -- chi can chay lai code Python.
            `G23-158` thi can ket qua ha nguon, khong cat duoc.
```

## 4. Co che noi -- KHONG sua builder

```text
Cach A (BI LOAI): them `--sla-spec` vao `build_calib_set_v3.py`
    -> phai sua nhanh dieu kien TRONG builder
    -> doi chung am ("chay voi SLA cu phai ra ket qua cu") se di qua MOT
       DUONG CODE KHAC voi duong da sinh ra ket qua cu
    -> NC khong con la NC; no chi chung minh hai nhanh MOI giong nhau.

Cach B (CHON): sinh mot FILE cung schema, truyen qua `--calibration`
    -> builder KHONG DOI MOT DONG NAO
    -> doi chung am tro thanh TAM THUONG dung nghia: truyen file CU -> phai
       ra ket qua CU bit-exact, va di qua DUNG duong code cu.
```

Ba rang buoc thiet ke:

```text
(1) KHONG sua `build_calib_set_v3.py`. Diem nap `--calibration` da co san.
(2) GIU NGUYEN moi truong khac (`sigma_rho`, `tau_rho`, `a`, `dt`, `n`,
    `seed`, `mode`, `rho_bar`, `role`). CHI ba truong doi:
    `t_delay_ms`, `t_loss`, `w_loss`.
(3) XOA dau vet cua vong tu hieu chuan: `fixpoint_*`, `percentile`,
    `target_viol`. De lai thi sau nay se bi doc nham la nguong VAN noi sinh
    -- dung cai "nap nghia moi vao truong cu" da cam o amendment 23-52 muc 8.
```

## 5. Dang ky truc SLA moi

```text
docs/phase-23/axis_registry.json
  sla_axis["results/PENDING/phase-20R/sla_manifest_exogenous_S-B.json"]
      content_sha256 = <tinh TU FILE THAT, khong go tay>
      label  = "exogenous_g114_S-B"
      status = "ACTIVE"
  sla_axis[".../sla_calibration.json"].status -> GIU `DEPRECATED` (khong xoa)

  approved_for_live.sla_axis += ["exogenous_g114_S-B"]
  approved_for_live.aoi_axis += ["measured_v7_uniform"]
```

Thu tu BAT BUOC: sinh manifest TRUOC, roi moi dang ky. `sha256` phai duoc
tinh tu file that; go tay mot sha la cach chac chan nhat de tao ra mot cai
chan KHONG BAO GIO bat duoc gi.

## 6. Du doan -- DIEN TRUOC KHI CHAY

| id | dai luong | loai | dai da ky | do duoc | KQ |
|---|---|---|---|---|---|
| M-167 | NC muc DUONG ONG: truyen manifest CU -> max\|diff\| tren truong so | CO CHE | < 1e-9 | | |
| M-168 | so cell LIVE duoi SLA ngoai sinh tren luoi 8 cell goc | NGOAI SUY | 1 (dai 1..3) | | |
| M-169 | `err_neo(poisson@0.925)` MOI / CU | NGOAI SUY | thuoc [0.5, 2.0] | | |
| M-170 | dau cua `LS(poisson@0.925)` sau khi doi SLA | CO CHE | GIU nguyen | | |
| M-171 | so cell doi DAU cua `lift - swing` tren 8 cell | CO CHE | <= 2 | | |

Ghi chu:

```text
M-167  la doi chung QUAN TRONG NHAT. Neu no > 1e-3 thi ta da doi HAI thu
       chu khong phai mot, va phai dung lai truoc khi lam bat cu gi khac.
M-168  co so: `sla_exogenous_S-B_ci.json` cho 1 LIVE + 1 AMBIGUOUS tren luoi
       8 cell goc. Nhung do la `S_pivotal`, con day la `regime` cua
       `calib_set` -- hai dai luong khac nhau, nen dai de rong.
M-170  `LS` la dai luong GHEP CAP nen SLA phan lon triet tieu (`L40`).
       Da ky "GIU nguyen dau" -- neu no DOI dau thi `L40` sai va phai ghi lai.
```

## 7. Gate

| id | noi dung | nguong |
|---|---|---|
| G23-190 | SLA manifest ngoai sinh CUNG SCHEMA voi ban cu, validate duoc | bat buoc |
| G23-191 | NC muc DUONG ONG: truyen manifest CU -> tai tao report CU | max diff < 1e-9 |
| G23-192 | 12 build hoan tat, artifact mang truong `validity` day du | bat buoc |
| G23-193 | `approved_for_live` co CA HAI truc -> artifact len `LIVE/` | bat buoc |
| G23-194 | test moi: van ban dong lesson phai liet ke MOI gate `NOT_RUN` cua lesson do | bat buoc |
| G23-195 | test moi: do thi phu thuoc giua cac mon `DEBT` KHONG duoc co chu trinh | bat buoc |

`G23-194` va `G23-195` la hai cai chan cho hai loi o muc 2. Chung quan trong
hon ban than viec pha deadlock lan nay: chung lam lan sau KHONG XAY RA duoc.

## 8. Han che moi

```text
  L66  Van ban dong lesson (`NN-close-*.md`) va `GATES.md` duoc cap nhat bang
       tay o HAI cho. `35-close-23-21.md` BO SOT `G23-156` va `G23-158` khoi
       muc "No mang sang". Khong test nao buoc hai cho khop ve TAP gate.
  L67  So no khong co co che chan CHU TRINH CHO. Moi `DEBT` duoc phep ghi
       "mo lai sau X" ma khong ai kiem `X` co phu thuoc nguoc vao no khong.
       Hau qua: `G23-158` <-> `G23-141`/`G23-142` da deadlock tu 2026-08-23.
  L68  Artifact cua `sla_exogenous` dung schema rieng (`sla_axis_label` +
       `sla_spec_id`) thay vi truong `validity` chuan. `test_no_stale_axes`
       KHONG kiem duoc chung neu chung len `LIVE/`.
```

## 9. Dieu KHONG lam

```text
- KHONG sua `cert/build_calib_set_v3.py` (muc 4).
- KHONG xoa `sla_calibration.json` cu: doi chung am `G23-191` can no chay mai.
- KHONG them "23.21" vao `CLOSED_LESSONS` truoc khi `G23-156`/`158`/`174`
  duoc cham.
- KHONG sua ket qua da ky cua 23.21a..e.
```

So ke tiep: `L69`, gate so 196, `M-172`, `K08`.
