#!/usr/bin/env python3
"""
verify_things.py — Nghiệm thu bootstrap (Lesson 2.2 Validation).
Đếm Thing trong Ditto vs số kỳ vọng từ spec; GET 1 Thing xem cấu trúc.

CHẠY:  python3 -m scenarios.verify_things
"""
import argparse
import sys
import json
import requests

from bridge.bootstrap import entities_from_spec
from bridge.ditto_common import (DITTO_BASE_URL, DITTO_AUTH, NAMESPACE, HTTP_TIMEOUT)


def main(spec_path='ditto/topology_spec.json'):
    entities = entities_from_spec(spec_path)
    expected_ids = {e['thing_id'] for e in entities}
    counts = {}
    for e in entities:
        counts[e['kind']] = counts.get(e['kind'], 0) + 1
    expected = len(expected_ids)

    print('Kỳ vọng từ spec/bootstrap: %d host + %d switch + %d link + %d controller = %d Thing'
          % (counts.get('host', 0), counts.get('switch', 0),
             counts.get('link', 0), counts.get('controller', 0), expected))

    # Đếm Thing thật trong namespace qua search API
    url = '%s/search/things' % DITTO_BASE_URL
    params = {'filter': 'like(thingId,"%s:*")' % NAMESPACE, 'option': 'size(200)'}
    r = requests.get(url, params=params, auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
    if r.status_code != 200:
        print('❌ search lỗi %d: %s' % (r.status_code, r.text[:200]))
        sys.exit(1)
    items = r.json().get('items', [])
    actual_ids = {item.get('thingId') for item in items if item.get('thingId')}
    print('Thực tế trong Ditto: %d Thing' % len(items))

    missing = sorted(expected_ids - actual_ids)
    extra = sorted(actual_ids - expected_ids)
    if not missing and not extra:
        print('✅ KHỚP — bootstrap đúng số lượng.')
    else:
        print('⚠ LỆCH %d. Kiểm tra missing/extra bên dưới.'
              % (len(actual_ids) - expected))
        if missing:
            print('  Thiếu: %s' % ', '.join(missing))
        if extra:
            print('  Thừa ngoài spec: %s' % ', '.join(extra))

    missing_meta = []
    for entity in entities:
        if entity.get('kind') != 'link':
            continue
        thing_id = entity['thing_id']
        rr = requests.get('%s/things/%s' % (DITTO_BASE_URL, thing_id),
                          auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
        try:
            rr.json()['features']['meta']['properties']['tSource']
        except (KeyError, TypeError, ValueError):
            missing_meta.append(thing_id)
    if missing_meta:
        print('❌ Link Thing thieu meta.tSource: %s' % ', '.join(missing_meta))
    else:
        print('✅ Mọi link Thing mong đợi đều có meta.tSource.')

    # GET 1 host xem cấu trúc
    if items:
        sample = items[0]['thingId']
        rr = requests.get('%s/things/%s' % (DITTO_BASE_URL, sample),
                          auth=DITTO_AUTH, timeout=HTTP_TIMEOUT)
        print('\nMẫu cấu trúc (%s):' % sample)
        print(json.dumps(rr.json(), indent=2, ensure_ascii=False)[:600])
    return not missing and not missing_meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--spec', default='ditto/topology_spec.json')
    args = parser.parse_args()
    sys.exit(0 if main(args.spec) else 1)
