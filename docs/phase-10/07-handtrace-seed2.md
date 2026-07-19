# Phase 10.4 - Episode xem tay (seed=2): co che lo ra bang mat

**Loai:** bang chung dinh tinh bo tro cho co che (`05-results.md` muc 5b).
**Regime:** `LOAD_PRESETS['bottleneck_E'] + drift_sigma=0.30` (E co the nghen,
co dynamics de lo dao ngoi). `z=3` (`AoI=1.5s`, gan vung breaking point).

---

## Tinh huong

Router toi node **D**, phai chon next-hop **E** hay **F**. Day la diem dao ngoi
E/F, trai tim cua bai toan routing.

## Su that vs anh cu tai thoi diem quyet dinh

| Link | Blind thay (anh cu 1.5s) | Su that | Chenh |
|---|---:|---:|---:|
| `D->E` | 0.698 (co ve on) | **1.300** (qua tai, loss 0.287) | +0.602 |
| `D->F` | 0.871 (co ve dong) | **0.280** (thong, loss 0) | -0.590 |

Trong `1.5s`, tinh hinh dao nguoc: E tu thong thanh nghen, F tu dong thanh
thong. Twin chua cap nhat nen giu anh cu "E thong, F dong".

## Quyet dinh va hau qua

| Policy | Re tai D | Duong di | Reward |
|---|---|---|---:|
| clairvoyant (thay that) | **F** | `SRC->A->D->F->DST` | **2.754** |
| blind (tin anh cu) | **E** | `SRC->B->D->E->F->DST` | 1.577 |

**Chenh lech: 1.18 diem reward** cho mot quyet dinh dinh tuyen sai. Blind dam
vao E nghen, phai vong `E->F` de sua, nen duong dai hon va reward thap hon.

## Dien giai co che

`AoI=1.5s` -> anh twin (`E:0.698`, `F:0.871`) khac su that
(`E:1.300`, `F:0.280`) -> blind re `E` trong khi clair re `F` -> luong vao link
nghen -> tang delay/loss, path dai hon -> mat `1.18` reward.

Day la chuoi nhan-qua hoan chinh cua RQ2, minh hoa bang mot episode cu the:
**thong tin cu trong twin dan toi chon next-hop sai khi mang thay doi nhanh hon
chu ky dong bo.**

## Doan dung cho luan van

> Co che suy giam duoc minh hoa o episode seed=2 (AoI=1.5s). Tai node D, tinh
> hinh mang dao nguoc trong khoang staleness: D->E chuyen tu rho=0.698 (anh cu)
> len rho=1.300 (that, qua tai), D->F giam tu 0.871 xuong 0.280. Clairvoyant re
> F (reward 2.75); blind tuong E con thong nen re vao E da nghen, phai vong de
> sua (reward 1.58). Chenh 1.18 reward cho mot quyet dinh minh hoa: thong tin cu
> dan den chon next-hop sai khi mang thay doi nhanh hon chu ky dong bo.

**Du lieu:** `measurements/out/mechanism_10_4.txt` (PART 2).
