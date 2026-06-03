#!/usr/bin/env python3
"""
verify_things.py — Nghiệm thu bootstrap (Lesson 2.2 Validation).
Đếm Thing trong Ditto vs số kỳ vọng từ spec; GET 1 Thing xem cấu trúc.

CHẠY:  python3 -m scenarios.verify_things
"""
import sys
import json
import requests

from bridge.ditto_common import (DITTO_BASE_URL, DITTO_AUTH, NAMESPACE, HTTP_TIMEOUT)


def main(spec_path='ditto/topology_spec.json'):
    spec = json.load(open(spec_path))
    n_host = len(spec.get('hosts', []))
    n_sw   = len(spec.get('switches', []))
    # đếm link canonical (loại trùng)
    seen = set()
    for ln in spec.get('links', []):
        seen.add(tuple(sorted([ln[0], ln[1]])))
    n_link = len(seen)
    expected = n_host + n_sw + n_link

    print('Kỳ vọng từ spec: %d host + %d switch + %d link = %d Thing'
          % (n_host, n_sw, n_link, expected))

    # Đếm Thing thật trong namespace qua search API
    url = '%s/search/things' % DITTO_BASE_URL
    params = {'filter': 'like(thingId,"%s:*")' % NAMESPACE, 'option': 'size(200)'}
    r = requests.get(url, params=params, auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
    if r.status_code != 200:
        print('❌ search lỗi %d: %s' % (r.status_code, r.text[:200]))
        sys.exit(1)
    items = r.json().get('items', [])
    print('Thực tế trong Ditto: %d Thing' % len(items))

    if len(items) == expected:
        print('✅ KHỚP — bootstrap đúng số lượng.')
    else:
        print('⚠ LỆCH %d. Kiểm tra log bootstrap.' % (len(items) - expected))

    # GET 1 host xem cấu trúc
    if items:
        sample = items[0]['thingId']
        rr = requests.get('%s/things/%s' % (DITTO_BASE_URL, sample),
                          auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
        print('\nMẫu cấu trúc (%s):' % sample)
        print(json.dumps(rr.json(), indent=2, ensure_ascii=False)[:600])


if __name__ == '__main__':
    main()