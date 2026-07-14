# Train Results

Thu muc nay chua ket qua training/evaluation va model checkpoint.

## File Quan Trong

- `a2_train_static.json`: log train/eval A2 static demand.
- `a2_dqn_static.pt`: checkpoint model static demand.
- `a2_train_dynamic_200_valseed4.json`: log train/eval A2 dynamic demand.
- `a2_dqn_dynamic_200_valseed4.pt`: checkpoint model dynamic demand.
- `bench_sync_cycle.json`: benchmark cycle sync lien quan den ha tang.

## Key Can Doc

- `baselines`: return/satisfaction cua oracle, greedy, equal, noop.
- `log`: cac moc eval trong qua trinh train.
- `elapsed_s`: tong thoi gian chay.
- `args`: tham so CLI da dung cho run.

## Lenh Sinh A2

Vi du static:

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/train_a2.py \
  --episodes 150 \
  --out results/train/a2_train_static.json \
  --save-model results/train/a2_dqn_static.pt
```

Vi du dynamic:

```bash
sudo -E env PYTHONPATH="$PWD" DT4N_FAST_PUSH=1 "$CONDA_PY" rl/a2/train_a2.py \
  --dynamic \
  --episodes 200 \
  --out results/train/a2_train_dynamic.json \
  --save-model results/train/a2_dqn_dynamic.pt
```
