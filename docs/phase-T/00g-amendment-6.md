# AMENDMENT 6 -- Phase T

Ngay: 2026-07-31
Trang thai truoc sua: Phase T chua chay do song; T.4 da dong validation va
mutation tests. Tai lieu kem: `docs/phase-T/05-campaign-runbook.md`.

## Da Thay Gi Truoc Khi Sua

T.1/Amendment 2 da chot step response de do `T_relax`, nhung estimator area
cu dung cua so hold day du va lay bien do tu bin dau. Synthetic test o dung
muc nhieu that cho thay estimator do co the am hoac lech lon, va fit exponential
con lech nang hon khi hoi phuc la tong nhieu mode.

## Sua Gi

A6.1. Thay estimator step response bang `T_area_v2`.

Estimator moi:

```text
T = integral_window [qbar(t)-qinf] dt / amp_plateau
```

`amp_plateau` lay tu hai binh on A va B cua chu ky `A -> B -> A`, khong lay tu
`qbar[0] - qinf`. Cua so tich phan dung khi `M >= c*T_hat(M)`, voi `c=8`, de
khong cho nhieu duoi hold lan at tin hieu ngan.

A6.2. Thay tham so step response.

```text
h2/poisson: hold=2.0 s, N=120, binw=0.010 s, 3 seed
cbr edge : 0.95 -> 0.98, hold=30 s, N=20
cbr cliff: 0.98 -> 1.00, hold=60 s, N=10
S-1      : A -> A, hold=2.0 s, N=120, bat buoc
```

Tong plan co 21 diem. Thoi gian raw la 11520 s = 192 phut ~= 3.2 gio; tinh
overhead Mininet thi du tru 3.3-3.5 gio.

Ghi chu sau Amendment 8: plan 21 diem nay bi thay bang step v2 vi bug nhan
A/B va thieu SNR o cac buoc rho ke nhau. Khong dung `step_state.json` v1 de
fit truc hoanh.

A6.3. Them runner T.5 va tach vong phat goi dung chung.

```text
measurements/packet_player.py
measurements/rho_gen.py
measurements/t5_step.py
measurements/t5_campaign.py
```

`measurements/load_gen.py` goi lai `packet_player.play_events()` de Phase L va
Phase T dung cung vong socket/dong ho/ghi TX.

A6.4. Chot thu tu van hanh T.5.

```text
G0 smoke       : 6 diem, khoang 12-15 phut
G1 step        : 21 diem, khoang 3.3-3.5 gio
G2 controls    : 45 diem sigma_rho=0, khoang 1.4-1.6 gio
G3 main        : 270 diem + 9 sentinel = 279 diem, khoang 8.4-9.1 gio
G4 unblind     : chi sau khi state/log da niem phong
```

A6.5. Blind discipline.

Runner T.5 chi duoc tinh gate ha tang va diagnostic van hanh. Khong tinh cac
metric niem phong cua campaign chinh trong luc chay:

```text
err_qs
err_jensen
d_sampling
err_total
err_mol
gain_mol
```

Cac thao tac bat dau/dung/mo niem phong phai ghi vao
`results/phase-T/RUNLOG.md` va `results/phase-T/UNBLINDING_LOG.txt`.

## Code/Test Them

```text
mininet/rho_spec.py: step_trajectory()
measurements/packet_player.py
measurements/rho_gen.py
measurements/t5_step.py
measurements/t5_campaign.py
test/test_phase_t_t5.py
```

`test/test_phase_t_no_v1_import.py` duoc mo rong de canh cac module T.5.

Kiem tra tai thoi diem amendment:

```text
pytest test/test_phase_t_t5.py -q  -> 7 passed
pytest -q                          -> 309 passed, 4 skipped
```

## Khong Sua

```text
Grid chinh Phase T giu theo Amendment 2/3.
bw=6 Mbps, q=13, warm-up=15 s, duration=105 s.
Probe van Poisson 20 pps.
Phan tich niem phong T.6 chua duoc them trong T.5.
Chua chay do song Mininet cho campaign T.5 trong amendment nay.
```

Ky: Codex theo yeu cau owner repo DT4N
Ngay: 2026-07-31
