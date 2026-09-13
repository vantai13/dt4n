# Lệnh kiểm 20R2-E1

Chạy từ repo `/home/ubuntu/dt4n`. Môi trường đã đo được lưu ở environment.json.

```bash
export PATH=/home/ubuntu/miniforge3/envs/sdn_rl/bin:$PATH
find . -name __pycache__ -prune -exec rm -rf {} +
python -m pytest test/test_estimand_registry_matches_code.py test/test_inherited_restrictions.py test/test_20r2_e1_evidence.py -q -p no:randomly
python -m pytest test/test_20r2_tools_run_and_reproduce.py -q -p no:randomly -k '20r2_9 or every_20r2_tool'
python -m pytest test/test_20r2_6_adjudicator.py test/test_20r2_7_dsla.py test/test_t2_estimand_registry.py test/test_20r2_2_prediction.py -q -p no:randomly
python -m pytest test/test_no_stale_axes.py -q -p no:randomly
```

Lệnh cuối hiện trả mã 1 vì 17 lỗi cũ. So tập dòng `FAILED` với stale-before.log,
không chỉ so số lượng. Không chạy lại đối chứng đỏ trên sổ đã sửa: red.log
được ghi trước commit E1-a; lịch sử E1-0 còn test trước sửa.

Tái lập ra file tạm để không ghi đè artifact:

```bash
python -m tools.20r2_9_partition_invariance --deterministic --out /tmp/E1b-partition-invariance.json
python -m tools.20r2_9_e1_mechanics --deterministic --out /tmp/E1-mechanics.json
cmp docs/phase-20R2/E1b-partition-invariance.json /tmp/E1b-partition-invariance.json
cmp docs/phase-20R2/E1-mechanics.json /tmp/E1-mechanics.json
sha256sum docs/phase-20R2/E1b-partition-invariance.json docs/phase-20R2/E1-mechanics.json
```

Custody: với từng dòng kind=run, returncode=0 trong 04-campaign-log.jsonl,
tính SHA256 của `out` và file cùng stem + `_report.json`; đối chiếu `sha256`
và `sidecar_sha256`. Thực chạy: 167 dòng, 334 file, không lệch.

Kiểm đóng băng và publish:

```bash
git diff --name-only phase-20R2-closed HEAD -- docs/phase-20R2/00-preregistration.md docs/phase-20R2/03-run-plan.json docs/phase-20R2/04-campaign-log.jsonl docs/phase-20R2/05-hygiene.json 'docs/phase-20R2/06*' 'docs/phase-20R2/07*' docs/phase-20R2/08-handoff-21R2.md docs/phase-20R2/99-gate-decision.md 'tools/20r2_5_*' 'tools/20r2_6_*' 'results/LIVE/phase-20R2/**'
git rev-parse 'phase-20R2-closed^{}'
git rev-parse 'phase-20R2-erratum-1^{}'
git ls-remote origin refs/heads/main 'refs/tags/phase-20R2-erratum-1*' 'refs/tags/phase-20R2-closed*'
```

Với tag annotated, `git rev-parse tag` là hash object của tag; thêm `^{}` để
lấy commit đích. Đây là lý do không so hash tag cũ trực tiếp với `042c58f4`.
