# results/RAW/ -- du lieu DO THO. CHI DOC.

Tang nay chua **Hang 1: khong tai tao duoc**. Moi file o day la dau ra cua
mot phep do tren mot he vat ly tai mot thoi diem cu the -- server do, tai nen
do, phien ban Ditto do. Khong quay lai duoc.

```text
QUY TAC
    KHONG ghi de.     KHONG xoa.     KHONG sua.
    Chi doc, va chi sinh ra dan xuat MOI o tang khac.
```

## Noi dung

| Cay | File | Do gi |
|---|---:|---|
| `phase-L/raw/` | 1.767 | trace probe link Phase L |
| `phase-L/golden/` | 1 | snapshot vang L2 |
| `phase-T/raw/` | 792 | campaign Phase T |
| `phase-T/sealed/` | 375 | Phase T da niem phong |
| `phase-20R/raw_additivity*` | 696 | TAM bien the additivity 20R (xem duoi) |
| `phase-23/aoi_v7_campaign/` | 1.141 | 427 MiB AoI tren topology_v7, 30 run |
| `phase-23/raw_differential*` | 1.070 | campaign differential |
| `phase-23/differential_live*` | 6 | do differential truc tiep |

## Tam thu muc `raw_additivity_*`: vi sao GIU ca tam

```text
raw_additivity                      120 file
raw_additivity_budgetfix            120
raw_additivity_fixed_pilot3         192
raw_additivity_fixed_preflight120    64
raw_additivity_inband                96
raw_additivity_inband_FAILED_race     8
raw_additivity_tmux_preflight        32
raw_additivity_tmux_preflight120     32
raw_additivity_v2_smoke              32
                                  ─────
                                    696
```

Xoa bay bien the pilot trong "sach" hon, nhung no **pha bang chung cho chinh
su trung thuc cua ban**. Neu chi con mot lan chay duoc bao cao, reviewer
khong co cach nao phan biet "bay lan kia la pilot ky thuat" voi "bay lan kia
cho ket qua xau nen toi giau". Khong phai vi ho nghi ban -- ma vi cau truc
repo khong cho phep ho loai tru kha nang do.

Giu ca tam va dan nhan la manh hon nhieu.

## Sao luu ngoai may

```text
~/archive/dt4n-raw-measurements-20260822.tar.gz     105 MB, 5.888 muc
SHA256  a97fa0a5ebecb21ed90f85b35be14175c18f68e5181d41e8b2885c631167eceb
DOI     CHUA CO -- gate G23-74 con MO
```

DOI chung minh *file ton tai tu ngay do*; SHA256 chung minh *file ban dang
dung chinh la file do*. Can ca hai. Xem `docs/phase-23/00zx-amendment-44.md`
muc 8.

## Luu y ky thuat

Campaign Mininet chay duoi `sudo`, nen 2.247 file tung thuoc `root:root`.
Chung da duoc `chown` ve `ubuntu` o Lesson 23.17 de co the phan tang; noi
dung khong doi (kiem chung bang tar + sha256 o tren).
