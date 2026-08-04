# Phase 20R.4 -- Campaign Log

## Pre-Full Smoke And Continuity

Ngay ghi: 2026-08-04

Smoke state hien co: `results/phase-20R/smoke_state.json`.

```text
smoke rows      : 10/10
smoke gate fail : 0
sentinel smoke  : z = +0.53 sigma so voi Phase L ref
```

Continuity state hien co: `results/phase-20R/continuity_state.json`.
Check: `results/phase-20R/continuity_check.json`.

```text
continuity: 8/8 pass
max |diff|/tol_2se < 0.50
```

Chi tiet dang ghi nho: ca 3 diem `cbr` trong continuity deu lech cung dau
am, co -0.003 ms so voi Phase L. Day la khoang 0.6% san nhieu 0.4646 ms va
khong co y nghia vat chat cho bai toan quyet dinh. Neu sau nay thay pattern
nay lap lai, xem nhu ghi chu drift nho can theo doi, khong phai blocker.

## Provenance Freeze

Smoke va continuity dau tien duoc chay tren commit
`ef7a778d4559dbcb7f5ed3de9c88df44392002e9`, nhung row provenance co
`git_dirty=true` vi state/log/output chua duoc freeze. Khong dung cac row do
lam bang chung final ve reproducibility.

Truoc full campaign, runner da duoc sua de:

```text
- chup git/environment fingerprint mot lan dau phien
- loai campaign output khoi dirty signal cua provenance
- van ghi git_dirty_raw va git_status_raw de minh bach
- dung neu git_status_relevant con bat ky thay doi code/config nao
```

Sau commit freeze, phai chay mot diem smoke rieng bang `--limit 1` va xac minh
`env.git_dirty == false` truoc khi bam full.
