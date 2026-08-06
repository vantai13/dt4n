# AMENDMENT 11 -- Phase 20R.6 Tandem Additivity Live Design

Ngay: 2026-08-06
Trang thai: ky truoc khi chay Mininet live A'/B/C.

## Ly Do Sua Thiet Ke

Thiet ke ba nhanh cu tron hai hieu ung trong `B - A`: chuyen tu
`SplitQdiscTopo` mot link sang topology ba link, va them tai dong thoi tren ba
link. Reviewer co the hoi truth table mot-link co chuyen duoc sang path ba
link hay khong. Vi vay bo sung nhanh A'.

Khong dung `RoutingTopo8` cho G6 vi no dung topology/controller/qdisc khac
Phase L. G6 chi duoc do tren `TandemTopo`, trong do moi link do duoc cai bang
`setup_measure_qdisc` va `setup_return_qdisc` cua Phase L.

## Bon Nhanh

```text
A  = truth_table da co, SplitQdiscTopo, mot link
A' = TandemTopo, chi link i co tai, probe link i
B  = TandemTopo, ca ba link co tai, probe link i
C  = TandemTopo, ca ba link co tai, probe ca path T123
```

Doi chieu:

```text
A' - A       = topology transfer
B  - A'      = CPU contention
C  - sum(B)  = cascade/G6
```

## Thiet Ke Khoa

```text
modes       = poisson,h2
seeds       = 101,102,103,104,105
A' rho_bar  = 0.925
B rho_bar   = 0.925
C rho_bar   = 0.85,0.925
Delta       = 0.44 ms
TOST        = CI90 nam trong [-0.44,+0.44]
power       = 1.645 * se < 0.44
probe gate  = probe intrusion <= 2%
schedule    = paired; digest phai khop theo mode/rho_bar/seed
```

So run:

```text
A' = 30
B  = 30
C  = 20
```

## Du Doan Truoc Live

```text
A' - A       ~ 0
B  - A'      ~ 0
C  - sum(B)  < 0
```

Neu `C - sum(B)` khac 0, dau tien nghiem la am: queue smoothing tren cascade
lam path cost nho hon tong ba phep do link rieng. Neu dau duong, dieu tra
artifact truoc khi tin la cascade.

## Quy Tac Dung Som

Chay A' truoc. Sau A':

```bash
python3 -m measurements.additivity_check --compare-a-vs-truthtable
```

Neu bat ky `A' - A` vuot `0.44 ms`, dung live run. Khi do truth table mot-link
khong chuyen duoc sang topology ba-link, va B/C khong con la kiem G6 sach.

## Lenh Da Khoa

```bash
python3 -m measurements.additivity_check \
  --write-plan results/phase-20R/additivity_plan.json

sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --smoke-topo

sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch Aprime --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_a_state.json

sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch B --modes poisson,h2 --rho-bar 0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_b_state.json

sudo -n env PYTHONPATH="$PWD" python3 -m measurements.additivity_live \
  --branch C --modes poisson,h2 --rho-bar 0.85,0.925 \
  --seeds 101,102,103,104,105 \
  --state results/phase-20R/additivity_branch_c_state.json

python3 -m measurements.additivity_check --analyze
```
