#!/usr/bin/env python3
"""Pure-logic tests for Phase 2.5 reconciliation and verification helpers."""

import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def ensure_requests_module():
    try:
        import requests  # noqa: F401
        return
    except ImportError:
        pass

    class Timeout(Exception):
        pass

    class ConnectionError(Exception):
        pass

    class RequestException(Exception):
        pass

    fake_requests = types.ModuleType('requests')
    fake_requests.exceptions = types.SimpleNamespace(
        Timeout=Timeout,
        ConnectionError=ConnectionError,
        RequestException=RequestException,
    )
    fake_requests.Session = lambda: types.SimpleNamespace(auth=None)
    sys.modules['requests'] = fake_requests


ensure_requests_module()

from bridge.sync_agent import build_full_changes, should_reconcile  # noqa: E402
from bridge.verify import values_match  # noqa: E402


passed = failed = 0


def check(name, cond):
    global passed, failed
    print(('  PASS ' if cond else '  FAIL ') + name)
    if cond:
        passed += 1
    else:
        failed += 1


print('== TEST 1: reconciliation cadence ==')
check('cycle 0 reconcile khi every=30', should_reconcile(0, 30) is True)
check('cycle 1 không reconcile', should_reconcile(1, 30) is False)
check('cycle 30 reconcile', should_reconcile(30, 30) is True)
check('every=0 tắt reconcile', should_reconcile(30, 0) is False)

print('\n== TEST 2: full changes gửi toàn bộ features ==')
things = {
    'org.dt4n:host-h1': {
        'features': {
            'status': {'properties': {'state': 'up'}},
            'traffic': {'properties': {'rxBytes': 10, 'txBytes': 20}},
        },
    },
    'org.dt4n:empty': {'features': {}},
}
full = build_full_changes(things)
check('chỉ Thing có features được gửi', set(full) == {'org.dt4n:host-h1'})
check('status được giữ nguyên', full['org.dt4n:host-h1']['features']['status']['properties']['state'] == 'up')
check('traffic được giữ nguyên', full['org.dt4n:host-h1']['features']['traffic']['properties']['txBytes'] == 20)

print('\n== TEST 3: values_match tolerance ==')
check('chuỗi khớp tuyệt đối', values_match('up', 'up') is True)
check('chuỗi lệch là fail', values_match('up', 'down') is False)
check('bool không bị True == 1 đánh lừa', values_match(True, 1) is False)
check('float lệch nhỏ tuyệt đối vẫn pass', values_match(100.0, 100.4, tol_abs=1.0) is True)
check('float lệch trong 5% vẫn pass', values_match(1000.0, 1040.0, tol_pct=5.0, tol_abs=1.0) is True)
check('float lệch quá tolerance fail', values_match(1000.0, 1100.0, tol_pct=5.0, tol_abs=1.0) is False)
check('ground truth 0 dùng tolerance tuyệt đối', values_match(0.0, 0.5, tol_abs=1.0) is True)

print('\n' + '=' * 50)
print('KET QUA: %d pass, %d fail' % (passed, failed))
sys.exit(0 if failed == 0 else 1)
