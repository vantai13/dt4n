# AMENDMENT 23-61 -- Ba trang thai digest, custody test, va khoa evidence

Ngay ky : 2026-08-24
Lesson  : 23.21j (custody truoc Viec 3)
Loai    : PHAN QUYET XAC MINH + CHAN GHI DE + TACH SUITE
Prereq  : amendment-60, `df9cd68`

## 1. Tien dang ky

```text
G23-221  `results/RAW` va `results/SUPERSEDED` khong con BAT KY write bit
         nao (user/group/other), de MAP.md muc 4 duoc thi hanh boi OS.
G23-222  test phu thuoc su CO MAT cua du lieu ngoai git mang mark `custody`;
         suite portable va CI loai marker nay. Test digest DOI NOI DUNG van
         portable va van do o moi noi file co mat.
G23-223  ghi mtime cua 7 parquet Phase 22, nhung KHONG nang trang thai
         UNKNOWN len ORIGINAL neu khong co digest lich su doc lap.
```

## 2. Backup truoc khi khoa

Da sao 23/23 parquet (7 Phase 22 + 16 Phase-21R), 16 sidecar Phase-21R va
`SURVIVING_CALIB_DIGESTS.json` sang filesystem Windows nam ngoai filesystem
WSL:

```text
C:\Users\VAN TAI\dt4n-evidence-backup-2026-08-24
parquet       23/23
bytes         1,562,807,704 (gom parquet + sidecar + digest ledger)
sha mismatch  0
```

Day la ban sao ngoai `/dev/sdd` cua WSL. Khong co o roi nao duoc mount, nen
khong tuyen bo no nam tren MOT THIET BI VAT LY khac.

## 3. L82 -- ba trang thai, khong phai hai

Bay parquet Phase 22 dang co tren dia tach thanh:

```text
VERIFIED_ORIGINAL       3  digest o artifact git_hash cu, khop file hom nay
NOT_ORIGINAL            1  digest o artifact cu KHAC file hom nay
UNKNOWN                 3  chi co digest bam hom nay, khong co moc doc lap
```

Ba file UNKNOWN (`cbr_0.700`, `poisson_0.925`, `poisson_0.925_V3`) bi CAM tai
dung ngang file NOT_ORIGINAL. `g23_174_reuse_verdict.json` khong phai moc
lich su: no bam chinh file hom nay, nen dung no de "xac minh" la vong tron.

## 4. G23-223 -- mtime khong phan xu duoc UNKNOWN

Ca bay mtime nam trong 13--15/08, truoc cua so digest 21--24/08. Nhung
`poisson_0.700`, file DA duoc digest doc lap chung minh la KHAC ban goc, cung
co mtime 13/08. Mot thao tac copy/restore co the bao toan mtime.

```text
KET LUAN: mtime la chung cu custody YEU va co phan vi duong ngay trong tap.
          Ba file L82 giu UNKNOWN; khong duoc nang thanh ORIGINAL.
```

## 5. L83 -- luat khong co co che

Digest `poisson_0.700` doi giua artifact `05b597f5` va ban kiem ke tai
`dcd6e53` ma khong co ban ghi ghi de. `results/` truoc amendment nay van co
write bit; MAP.md muc 4 chi la quy uoc. Sau khi backup, ap
`chmod -R a-w results/SUPERSEDED results/RAW` va ghim bang custody test.

## 6. L84 -- vang mat khac doi noi dung

Test cu gop hai tin hieu:

```text
VANG MAT       binh thuong tren clone sach; bao dong tren may custody
DOI NOI DUNG  bao dong o moi noi file co mat
```

Da tach thanh `test_pinned_files_still_present` (custody) va
`test_pinned_digests_have_not_changed` (portable). Lint hardcoded theo dia
`test_no_hardcoded_missing_parquet` cung mang custody. Meta-test buoc moi
test goi helper that bai vi VANG MAT phai mang marker.

## 7. Pham vi cua G23-212a

`G23-212a` chung minh patch thay `prepare_sla()` bang nap manifest khong lam
doi 2340 truong ha nguon tren 8 cell. No KHONG chung minh manifest tu no la
dung: hai ve co the cung sai theo mot cach. Tinh dung cua manifest/nhan che
do phai do boi gate NOI DUNG rieng; parity nay chi la gate TUONG DUONG CODE.

## 8. Khong lam trong amendment nay

- KHONG dung mtime de nang UNKNOWN thanh ORIGINAL.
- KHONG dua custody vao CI/portable suite.
- KHONG xoa test exists(); giu no de bao ve may tac gia, nhung gan dung mark.
- KHONG bat dau Viec 3/23.21h trong cung amendment custody.
