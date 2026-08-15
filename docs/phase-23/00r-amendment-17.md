# AMENDMENT 23-17 -- G23-17a marginal priors before 23.4 sweeps

Ngay: 2026-08-15
Commit tool: `1be90cd`
Artifact: `results/phase-23/g23_17a_cell_margins.json`

Ly do: truoc khi chay bat ky sweep nao cua Lesson 23.4, do ba xac suat bien
cho moi cell de du doan do kho cua fallback. Day la diem dung bat buoc: chua
chay G23-21c tren hai cell moi, chua chay fallback sweep, chua chay baselines.

Rowset: TEST split, vi Phase 23 cham risk he thong tren TEST.

```text
cell                err_neo     err_P1       both   mass_pos   mass_neg        D      swing
poisson@0.925      0.222399   0.340276   0.093956   0.246320   0.128442    1.918   0.117878
poisson@0.850      0.220727   0.345169   0.122532   0.222637   0.098194    2.267   0.124442
h2@0.700           0.126536   0.157454   0.081605   0.075849   0.044931    1.688   0.030918
```

Definitions:

```text
mass_pos = P(twin dung, P1 sai)  = P(P1 sai) - P(ca hai sai)
mass_neg = P(twin sai, P1 dung)  = P(twin sai) - P(ca hai sai)
D        = mass_pos / mass_neg
swing    = mass_pos - mass_neg
```

## Cham truoc sweep

Du doan/phat bieu truoc G23-17a:

```text
D(h2@0.700) > 2.68
swing(h2@0.700) in [0.16, 0.24]
err(P1) gan nhu topology-invariant, xap xi 0.34
```

Ket qua G23-17a bac ca ba tien de tren cho TEST artifact hien tai:

```text
D(h2@0.700)     = 1.688
swing(h2@0.700) = 0.030918
err_P1(h2@0.700)= 0.157454
```

Do do G23-17a khong ung ho gia thuyet "cell h2@0.700 kho hon it nhat 40%"
neu do kho duoc dinh nghia bang `D`. No cho thay fallback P1 khong phai chi
la topology constant trong artifact nay; xac suat P1 sai thay doi manh theo
cell/load distribution.

Chua cham du doan ve beneficial band cua h2@0.700, vi dieu do can fallback
sweep. Nhung co che dau vao da doi: `h2@0.700` co `swing` nho hon nhieu so voi
poisson@0.925, khong nam quanh bien `0.176`.

## Dieu kien tiep theo

Truoc khi chay sweep 23.4:

```text
1. G23-21c phai chay lai tren poisson@0.850 va h2@0.700.
2. Neu cell nao co thin Mondrian cell hoac q_hat nonfinite, dung sweep va xu ly truoc.
3. Khi doc h2@0.700, khong duoc dung tien de err(P1) bat bien theo topology.
```
