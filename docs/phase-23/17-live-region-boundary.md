# 17 -- Lesson 23.16: vung song va bien loi ich

Prereg chinh: `docs/phase-23/00zq-amendment-40.md` tai tag
`lesson-23.16-pre` (`d3d1645`)  
Sua domain estimand truoc outcome: `docs/phase-23/00zr-amendment-41.md` tai
tag `lesson-23.16-domain-pre` (`7ece9fc`)  
Artifact: `results/phase-23/live_region_sweep.json`  
SLA/domain: `results/phase-23/sla_calibration_lesson23_16.json`  
Figure: `results/phase-23/fig1_live_region.png`

## 1. Ket qua headline

Hai diem Poisson moi lam hep bien quan sat cua `lift-swing` tu
`(0.850,0.925)` thanh:

```text
rho_bar       0.850       0.875       0.900       0.925
lift-swing   -0.014183   -0.016501   -0.024447   +0.058495
Delta F2     +0.003120   +0.003630   +0.005378   -0.012869
```

Endpoint luoi dau tien co loi van la `rho_hit=0.925`; bracket doi dau nam
trong `(0.900,0.925)`. M-53 va M-54 HIT theo dinh nghia khoa. Day la bracket
tren luoi roi rac, khong phai mot zero crossing lien tuc da uoc luong.

Ca hai diem moi deu o vung song:

```text
err_neo(poisson@0.875) = 0.227415
err_neo(poisson@0.900) = 0.229301
```

M-55 HIT. Nhu vay viec chua co loi tai hai diem khong the quy cho bai toan
suy bien: twin sai khoang 23% va certificate/fallback thuc su co co hoi thay
doi risk.

## 2. Severe test H2

`h2@0.650` qua truth-domain gate va la cell song:

```text
err_neo       = 0.161445
lift          - swing = +0.021710
Delta F2      = -0.004776
Delta selected= -0.004696
```

M-56 HIT nhung M-57 MISS: dau du doan la am, quan sat la duong. Vi vay quy
luat dau theo tai cua Poisson khong duoc tong quat hoa sang H2. Tren H2,
`rho=0.650` co loi, `rho=0.700` co hai, sau do cac cell tai cao suy bien;
bon diem hien tai khong tao mot bien don dieu cung kieu voi Poisson.

Day la mot severe-test co ich: no giu ket qua Poisson nhung bac bo phat bieu
rong hon ve mot quy luat tai chung cho moi ho traffic.

## 3. Objective confirmation M-47b

M-47b cung MISS. Tai ratio khoa `0.8352557797157567`, cac cell song giu kin:

| Cell | Delta selected tai ratio | KQ `<=0` |
|---|---:|:--:|
| poisson@0.960 | -0.007254 | dat |
| poisson@0.875 | -0.000334 | dat |
| poisson@0.900 | +0.002836 | truot |
| h2@0.650 | -0.012785 | dat |

Tieu chi yeu da sua dung nghia khong-co-hai, nhung van bi bac bo boi mot
cell song. Do do khong the cong bo mot exchange-rate ratio chung bao dam
non-inferiority tren moi cell song giu kin.

## 4. M-48b va chan doan S9

Tai tinh tren bon cell song cua Lesson 23.15:

```text
twin_deg spread  = 1.059170x   HIT [TAI TINH, khong prediction-hit]
prior_deg spread = 4.111317x   readout cu
```

M-48b xac nhan cach doc dung cua M-48: spread vo han tren 8 cell la artifact
mau so 0; tren mien bai toan co noi dung, `twin_deg` on dinh trong khi
fallback `prior_deg` bien thien manh. Verdict M-48 cu van MISS.

## 5. Domain control va Amendment 41

Lan domain-only dau tien ap dong thoi hai distribution va loai ca Poisson.
Khong outcome nao duoc tinh. Amendment 41 sua control truoc builder: gate
phai dung distribution thuc su duoc cham (`calib_builder`, `sigma=0.0096`),
con SLA-regime la stress diagnostic.

| Cell | builder max clip | SLA-regime max clip | Eligibility |
|---|---:|---:|:--:|
| poisson@0.875 | 0.000000 | 0.005180 | PASS |
| poisson@0.900 | 0.000000 | 0.006330 | PASS |
| h2@0.650 | 0.000000 | 0.000325 | PASS |

Fallback `h2@0.675` khong duoc kich hoat va khong duoc build. Stress result
cho thay khong nen ngoai suy ket qua sang bien do SLA-regime ma khong mo rong
truth-table domain, nhung khong lam vo nghia dataset sigma=0.0096 da cham.

## 6. Cham metric

| ID | Gia tri | Dai khoa | KQ |
|---|---:|---:|:--:|
| M-53 `rho_hit` | 0.925; bracket `(0.900,0.925)` | 0.860--0.925 | HIT |
| M-54 chuoi dau Poisson khong dao nguoc | am, am, am, duong | CO | HIT |
| M-55 err_neo hai Poisson moi | 0.2274 / 0.2293 | 0.15--0.26 | HIT |
| M-56 H2 candidate song | true, 0.161445 | CO | HIT |
| M-57 H2 `lift-swing<0` | +0.021710 | CO | MISS |
| M-47b nonpositive moi live heldout | 3/4 | CO | MISS |
| M-48b live twin_deg spread | 1.059170 | 1.00--1.30 | HIT [TAI TINH] |

## 7. Controls, tests va ket luan

```text
NC-G old-cell parity max gap       : 0.0      PASS
NC-H domain-before-builder         : true     PASS
NC-I lift-swing identity           : true     PASS
NC-J row/seed disjoint             : true     PASS
NC-K requested/passed/excluded     : 3/3/0    PASS
Golden tests Lesson 23.16          : 7 passed
Artifact git_dirty                 : false
```

Ket qua duoc phep cho paper:

1. `poisson@0.960` van la xac nhan ngoai mau dau tien co loi;
2. bien loi ich Poisson duoc thu hep ve `(0.900,0.925)` va ca hai diem bo
   sung deu khong suy bien;
3. vung song do bang `err_neo` tach suy bien khoi hieu ung nguoc;
4. severe test bac bo viec tong quat hoa duong bien Poisson sang H2;
5. khong co objective ratio chung da xac nhan cho moi cell song giu kin.

Khong retune sau MISS. Campaign Mininet Amendment 36 van tam dung o 5 row;
artifact AoI van chua duoc doc.
