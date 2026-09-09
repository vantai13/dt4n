#!/usr/bin/env python3
"""20R2: ghi DANH SACH TEN cua cac loi baseline, tu output pytest.

Run: python -m pytest test/ -q -rf > /tmp/run.txt 2>&1; \
     python -m tools.20r2_baseline_failures --from /tmp/run.txt \
        --out docs/phase-20R2/baseline_failures.txt

Vi sao can tep nay: mot tap 25 phan tu KHONG so duoc voi mot tap 25 phan tu
khac neu chi biet LUC LUONG. "Khong co loi moi" chi la mot LOI KHAI cho den khi
co danh sach TEN. Cong cu nay sinh danh sach do, de lan sau `diff` duoc.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Nhom N7: mot test duy nhat, chay tren nhieu artifact -> gom lai, dung dem
# tung dong nhu tung loi rieng.
N7 = 'test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for'


def parse(text: str) -> dict:
    failed = [l.split(' ', 1)[1].strip() for l in text.splitlines()
              if l.startswith('FAILED ')]
    failed = [re.sub(r'\s+-\s+.*$', '', f) for f in failed]
    # pytest nhung DUONG DAN TUYET DOI vao id cua test parametrize theo tep.
    # Cat goc repo di, neu khong tep nay khong `diff` duoc giua hai may -- dung
    # loi ma 20R2-L7 vua cam doi voi artifact.
    failed = [f.replace(str(REPO) + '/', '') for f in failed]
    n7 = sorted(f for f in failed if N7 in f)
    other = sorted(f for f in failed if N7 not in f)
    tail = [l for l in text.splitlines() if ' passed' in l and (' failed' in l or ' warning' in l)]
    return {'n7': n7, 'other': other, 'summary': tail[-1].strip() if tail else '(khong doc duoc)'}


def render(data: dict) -> str:
    n7, other = data['n7'], data['other']
    lines = [
        '# Baseline loi cua dt4n -- DANH SACH TEN, khong phai so dem',
        '# Sinh boi tools/20r2_baseline_failures.py, %s' % datetime.now(timezone.utc).isoformat(),
        '#',
        '# Doi chieu bang `diff`, khong bang so dem. Hai tap cung luc luong van co',
        '# the khac nhau hoan toan.',
        '#',
        '# Dieu kien doc: env sdn_rl, Python 3.12, requirements-test.txt, VA co san',
        '# cay results/. Mot clone sach KHONG cho cung con so -- xem',
        '# docs/phase-20R2/01-recovery-and-remediation.md.',
        '',
        '## pytest: %s' % data['summary'],
        '',
        '## NHOM N7 -- %d artifact, MOT test duy nhat' % len(n7),
        '## %s' % N7,
    ]
    lines += ['   %s' % re.sub(r'^.*\[(.*)\]$', r'\1', f).replace(str(REPO) + '/', '')
              for f in n7]
    lines += ['', '## CAC LOI CON LAI -- %d, ghi DU TEN' % len(other)]
    lines += ['   %s' % f for f in other]
    lines += ['', '## TONG: %d ten (N7 tinh la %d dong)' % (len(n7) + len(other), len(n7))]
    by_file = Counter(f.split('::')[0] for f in other)
    lines += ['', '## Phan bo cac loi con lai theo tep']
    lines += ['   %3d  %s' % (v, k) for k, v in sorted(by_file.items())]
    return '\n'.join(lines) + '\n'


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--from', dest='src', required=True, help='output cua pytest -rf')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    data = parse(Path(args.src).read_text(encoding='utf-8', errors='replace'))
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data), encoding='utf-8')
    print('N7: %d dong | loi khac: %d | -> %s' % (len(data['n7']), len(data['other']), out))


if __name__ == '__main__':
    main()
