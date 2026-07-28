# AMENDMENT 4 - Phase 21, truoc Lesson 21.4

Ngay: 2026-07-28
Trang thai truoc sua: Lesson 21.3, commit `af8dd6e`

## Muc Dich

Lesson 21.3 da cho thay trust gate conformal co duong risk-coverage OOS tot.
Tuy nhien reviewer co the hoi: neu gate chi la threshold tren `gap_twin`, phan
`q_hat(z)` co dong gop gi?

Amendment nay ghi truoc ablation `B2` de tra loi cau hoi do truoc khi do ket
qua Lesson 21.4.

## B2. Ablation Duoc Ghi Truoc

So sanh hai cong tren cung split `D_CALIB` / `D_TEST` cua Lesson 21.3:

```text
adaptive gate : gap_twin >= q_hat(z) - epsilon
constant gate : gap_twin >= c
```

Quy trinh cong bang:

```text
1. Voi moi epsilon da ghi truoc, tinh coverage cua adaptive gate tren D_CALIB.
2. Chon c la phan vi cua gap_twin tren D_CALIB de constant gate khop coverage do.
3. Danh gia ca adaptive va constant gate tren D_TEST.
4. So sanh err|accept bang paired block bootstrap tren D_TEST.
```

Tuyet doi khong chon `c` tren `D_TEST`.

## Bon Duong Co So

```text
B0 always trust      : anchor, coverage = 1.0
B1 random accept     : accept ngau nhien voi xac suat p*
B2 constant threshold: gap_twin >= c, ablation chinh
B3 oracle            : accept cac diem twin dung truoc, chan tren ly thuyet
```

## Du Doan Ghi Truoc

Chung toi du doan adaptive gate thang constant gate vi `err(z)` tang don dieu
da duoc do trong Lesson 21.2: `q_hat(z)` tang theo tuoi, va `err(z)` cung tang
don dieu voi Spearman = 1.0. Cac hieu lien tiep cua `q_hat(z)` deu co CI da
hieu chinh loai tru 0 tren offered va sensitivity scores.

Co che du kien:

```text
constant threshold se accept qua nhieu o bin tuoi gia, noi err(z) cao hon,
va accept qua it o bin tuoi tre, noi twin dang tin hon.
```

Tieu chi doc ket qua:

```text
adaptive_better = CI95 cua (err_const - err_adaptive) nam hoan toan tren 0.
```

Neu adaptive khong thang o bat ky muc epsilon nao, ket luan se duoc viet lai:
conformal gate van cung cap bao dam bao phu/tu choi hanh dong, nhung chua chung
minh duoc dong gop hieu nang cua dieu kien-theo-tuoi.

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-28
