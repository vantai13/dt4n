# Phase 10 - Phan tich KHAM PHA: cau truc hai-timescale cua wrong_excess

**Ngay:** 2026-07-19
**Loai:** EXPLORATORY / POST-HOC (hau nghiem; khong thuoc pre-registration).
**Canh bao doc:** phan nay la gia thuyet moi nay sinh sau khi thay du lieu
confirmatory. Suc nang thap hon ket qua da dang ky trong `05-results.md`.
Can xac nhan doc lap truoc khi coi la ket luan.

---

## 1. Quan sat khoi phat

Tren dai da dang ky (`z <= 20`, `AoI <= 10s`), `wrong_excess` o diem cuoi
(`z=20`) van tang nhe. Dieu nay goi y dai dang ky co the chua phu het vung
bao hoa that.

## 2. Mo rong dai (kham pha) - Test 2

Quet them `z=30,40,60` (`AoI = 15,20,30s`), `N=800`:

| z | AoI(s) | wrong_excess |
|--:|-------:|-------------:|
| 20 | 10 | 0.2313 |
| 30 | 15 | 0.2433 |
| 40 | 20 | 0.2504 |
| 60 | 30 | 0.2488 |

`|z60 - z40| = 0.0017` -> duong phang theo heuristic `0.01 wrong_excess` o
AoI khoang `20-30s`. **Tran that xap xi `0.25`**, cao hon `A=0.218` ma fit
1-tau tren dai cu uoc luong.

## 3. So sanh mo hinh 1-pha vs 2-pha - Test 3

| Mo hinh | Tham so | R2 | BIC |
|---|---|---:|---:|
| 1-timescale | `A=0.236`, `tau=1.93s` | 0.967 | -89.0 |
| 2-timescale | `tau1=0.72s`, `tau2=5.78s` (ratio 8x) | 0.997 | -111.5 |

`delta_BIC = -22.5` -> ung ho manh cau truc 2-pha tren du lieu mo rong
(`|delta_BIC| > 10` la tin hieu rat manh theo heuristic thong dung).

## 4. Kiem do ben qua mau doc lap - Test 4

Fit lai tren 3 bo seed doc lap:

| Bo | 1tau tau | 2tau tau1 | 2tau tau2 | delta_BIC |
|---|---:|---:|---:|---:|
| 1 (`0-399`) | 2.48s | 1.34s | 7.61s | -8.3 |
| 2 (`400-799`) | 1.42s | 0.53s | 5.90s | -7.6 |
| 3 (`800-1199`) | 2.01s | 0.48s | 4.52s | -8.9 |

**Doc ket qua:**

- `delta_BIC` am o ca 3 bo -> cau truc 2-pha ton tai nhat quan ve mat dinh tinh.
- Nhung `tau1` nhay `0.48-1.34s`, `tau2` nhay `4.5-7.6s` -> gia tri tau
  cu the chua on dinh. Day co kha nang la parameter degeneracy khi fit 4 tham
  so tren 11 diem co nhieu.

## 5. Ket luan kham pha (gioi han dung muc bang chung)

- **Dang tin dinh tinh:** `wrong_excess` co cau truc hai-timescale, goi y hai
  co che: (a) sai lech nhanh o link gan nguong nghen/cliff, va (b) mat tuong
  quan cham cua toan anh khi thong tin cuc cu.
- **Chua tin dinh luong:** gia tri cu the `tau1`, `tau2` chua on dinh. Khong
  bao cao chung nhu hang so. Chi noi hai timescale cach nhau xap xi mot bac do lon.
- **Khong anh huong tru cot:** breaking point confirmatory (`~1.8-2.5s`) va ket
  luan "Ditto that du tuoi" trong `05-results.md` khong doi.

## 6. Viec tuong lai neu phat trien len

- Co dinh `A_total=0.25` tu Test 2, fit it tham so hon de giam degeneracy.
- Them diem o vung giao hai pha (`AoI 2-8s`) de rang buoc tach `tau1/tau2`.
- Bootstrap de co khoang tin cay chuan cho `tau1`, `tau2`.
- Xac nhan co che bang soi tay: pha nhanh co tap trung o link cliff khong.

**Du lieu:** `measurements/out/diagnose_saturation.txt`,
`measurements/out/diagnose_saturation_test2.csv`,
`measurements/out/diagnose_saturation_test4.csv`.
