"""A partial or corrupt archive must never satisfy the 166/166 gate."""
import importlib
import json

import pyarrow as pa
import pyarrow.parquet as pq

R = importlib.import_module('tools.20r2_1_parquet_recovery')


def put_report(repo, index):
    folder = repo / R.SWEEP
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f't2_6_r{index:04d}.parquet'
    pq.write_table(pa.table({'err_total': [.25]}), path)
    report = path.with_name(path.stem + '_report.json')
    report.write_text(json.dumps(dict(parquet=str(path.relative_to(repo)),
                                      parquet_sha256=R.sha256_file(path), n_rows=1)))
    return path, report


def test_exactly_166_files_required(tmp_path):
    assert not R.audit(tmp_path)['summary']['gate_1_2_full_recovery']
    for i in range(165):
        put_report(tmp_path, i)
    s = R.audit(tmp_path)['summary']
    assert s['n_ok'] == 165
    assert not s['gate_1_2_full_recovery']
    put_report(tmp_path, 165)
    assert R.audit(tmp_path)['summary']['gate_1_2_full_recovery']
    put_report(tmp_path, 166)
    assert not R.audit(tmp_path)['summary']['gate_1_2_full_recovery']


def test_missing_corrupt_and_wrong_row_count(tmp_path):
    missing, _ = put_report(tmp_path, 0)
    corrupt, _ = put_report(tmp_path, 1)
    _, report = put_report(tmp_path, 2)
    missing.unlink()
    corrupt.write_bytes(corrupt.read_bytes() + b'changed')
    rep = json.loads(report.read_text()); rep['n_rows'] = 99
    report.write_text(json.dumps(rep))
    s = R.audit(tmp_path)['summary']
    assert s['n_missing'] == 1
    assert s['n_sha_mismatch'] == 1
    assert s['status_counts']['ROW_COUNT_MISMATCH'] == 1
    assert not s['gate_1_2_full_recovery']
