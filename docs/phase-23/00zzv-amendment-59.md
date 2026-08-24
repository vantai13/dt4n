# AMENDMENT 23-59 -- Phan quyet G23-174 va ghi no co CLI chet

Ngay ky : 2026-08-24
Lesson  : 23.21c / dong 23.21
Loai    : PHAN QUYET ARTIFACT + CHAN TAI DIEN
Prereq  : amendment-58 (`813b5f0`), ket qua (`e2d4efe`)

## 1. Ky truoc khi chay

`G23-174` khong chi hoi co LUu duoc digest hay khong (`G23-198/199` da tra
phan do). No con hoi co calib parquet nao da BI TAI DUNG truoc khi doi chieu
duoc digest hay khong.

```text
PASS  = bon parquet Dot 4 khong bi tai dung; 16 build LIVE hien hanh la ban
        sinh lai tu seed, co output digest va digest khop byte tren dia; moi
        parquet legacy khac neu tim thay phai bi CAM tai dung khi chua ghep
        duoc voi digest cu.
FAIL  = mot build LIVE khai hoac tham chieu parquet legacy khong xac minh;
        hoac mot output LIVE thieu/sai digest.
```

Artifact phan quyet do `tools/g23_174_reuse_verdict.py` sinh ra tai
`results/LIVE/phase-23/g23_174_reuse_verdict.json`.

## 2. Sai khac phai bao cao, khong ep ve du doan

Snapshot trong huong dan ngoai repo du doan glob
`results/**/calib_set_v3_*.parquet` rong. Checkout `e2d4efe` thuc te co sau
file local o `results/phase-22/`. Vi vay phep do phai tach hai cau hoi:

1. Bon parquet Dot 4 ma `live_region_sweep.py` tro toi co ton tai khong?
2. Moi file legacy khac co bi 16 build LIVE hien tai khai lam input/output
   khong?

Su ton tai cua file cu KHONG cho phep tai dung. File cu chi duoc dua vao lan
do sau khi ghep duoc voi digest da luu; neu khong thi cam dung.

## 3. L72 -- `--calib-template` cua `live_region_sweep` la co chet

`cert/live_region_sweep.py` khai bao `--calib-template`, nhung `run_sweep()`
khong nhan tham so va `main()` khong doc `args.calib_template`. Co bi bo qua
im lang, cung lop loi voi `R1`.

Them `test/test_cli_flags_are_wired.py` de quet CLI trong `cert/`,
`measurements/`, `tools/`. Danh sach `KNOWN_DEAD` chi duoc ngan di. DC33 la
doi chung duong synthetic: mot `--calib-template` khong duoc doc phai bi bat.

Lan quet dau tien tim them NAM co no-op that:

```text
cert/abstain_cost.py                 --calib-template
measurements/decision_error_v2.py   --boot-metrics
measurements/l6_campaign.py         --resume
measurements/l6_campaign_fine.py    --resume
measurements/t5_campaign.py         --resume
```

`additivity_live.py --probe-inband` duoc doc qua `getattr`; `--limit` va
`--dry-run` cua `l6_campaign_fine.py` dung `dest` alias; chung la false
positive cua regex dau tien. Hai co controller cua
`calib_aoi_routing_auto.py` duoc forward bang ca Namespace toi
`calib_composition.start_controller`; test moi ghim ca loi goi va cho doc ha
nguon. Khong muc nao trong ba nhom nay bi ghi nham la debt.

## 4. Pham vi dong sach

`L41`, `L57`, `L68`, `L71`, `L72`, viec chuyen luoi chinh 8 cell sang 6 cell
co nghia, va `G23-141/142` van mo/debt. Chung co ma, noi dinh nghia, lesson
23.22 so huu, va cai chan de khong bi quen. `G23-174` PASS khong dong `L51`:
co che moi ngan mat/tai dung khong xac minh tai dien, nhung khong hoi sinh
digest lich su da mat.

Khong lam `L57` trong amendment nay: M-176..M-178 chua duoc tac gia ky du
doan, va viec dien giai lai nguong duoi `L61` la lesson-size.
