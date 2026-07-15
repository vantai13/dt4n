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
- `episode_log`: moi episode train mot dong, co return/loss/epsilon/steps.
- `log`: cac moc eval trong qua trinh train, theo `--eval-every`.
- `agent_minus_greedy_strong`: gap voi baseline rule-based manh. Day la cot
  can doc khi tra loi phan bien "if-else co du khong?".
- `elapsed_s`: tong thoi gian chay.
- `args`: tham so CLI da dung cho run.

## File Sidecar Sau Khi Train

Script train moi tu dong ghi them:

- `<out>.episodes.csv`: bang tung episode train.
- `<out>.eval.csv`: bang cac moc eval.
- `<out>.svg`: bieu do train/eval doc duoc truc tiep trong VSCode/browser.

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
  --eval-every 30 \
  --delta-s 1.1 \
  --out results/train/a2_train_hard.json \
  --save-model results/train/a2_dqn_hard.pt
```

Sau khi demand dynamic duoc lam kho hon, khong so truc tiep run moi voi file
`a2_train_dynamic_clean.json` cu. Hay so trong cung mot run: agent vs greedy,
agent vs greedy_strong, agent vs myopic_oracle.
