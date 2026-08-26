# AMENDMENT 23-69c -- PILOT A069 phai dung SLA S-B, khong dung self-calibration

Ngay ky : 2026-08-26

Trang thai: ky SAU lan pilot INVALID, TRUOC khi chay lai.

## 0. Loi bi test custody bat

A069 S-2 noi manifest SLA "chi la provenance pointer". Dieu nay SAI trong
builder that:

```text
build_calib_set_v3._load_cell(calibration_path)
    -> doc sigma_rho VA w_loss tu chinh file do

build_one_v3(... w_loss=cell["w_loss"])
    -> `wrong`, m_hat, score deu phu thuoc w_loss
```

Sidecar lan dau ke thua `self_calibrated` w_loss theo cell (~1.8k o cell da
lo), trong khi truc S-B da duyet co w_loss=5000. `test_no_stale_axes` bat 6
report `sla_axis=UNREGISTERED` va sidecar thieu validity. Vi vay toan bo pilot
lan dau mang nhan `INVALID_SELF_CALIBRATED_SLA`; khong cham stop-rule va
khong doi G23-270.

## 1. Phep sua duy nhat

Tao manifest S-B 20 cell MOI:

```text
14 cell cu: copy bit noi dung cell tu sla_manifest_exogenous_S-B_14cells.json
 6 cell moi: chi muon (mode,rho,sigma,seed,n,...) tu extra_calibrated_cells;
             thay TOAN BO SLA bang S-B: T_delay=50 ms, T_loss=0.01,
             w_loss=5000, sla_source=exogenous_g114_S-B.
```

File moi co source/sha rieng va duoc dang ky trong `axis_registry.json` qua
amendment nay. KHONG sua/ghi de manifest 14 cell. Runner A069 chi nhan manifest
20 cell da dang ky va tu them validity block vao summary.

## 2. Tai sao duoc chay lai ma khong HARK

Phep sua bi ep boi invariant custody va hop dong S-B da dong tu Lesson 23.21,
khong boi dau pilot. Giu nguyen lưới rho, seed, n, U3, threshold err=0.05,
stop-rule, allowlist va moi M-209..M-214. Sau khi thay so INVALID, khong them
rho, khong doi dai, khong loai cell.

## 3. Artifact invalid duoc bao toan

Toan bo lan dau chuyen sang:

```text
results/SMOKE/phase-23/a069-invalid-selfcal/
```

Khong xoa. File `48-a069-pilot.md` bao cao tach INVALID va lan S-B hop le.
