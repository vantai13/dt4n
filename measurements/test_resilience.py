#!/usr/bin/env python3
"""Quick checks for retry/backoff and sync-agent degradation.

Runs without Mininet or Ditto by using fake HTTP sessions and a dummy collector.
"""

import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def ensure_requests_module():
    """Provide a tiny requests stub if the local Python lacks requests."""
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

import requests  # noqa: E402

from bridge import pusher, sync_agent  # noqa: E402


class Response:
    def __init__(self, status_code, text='body'):
        self.status_code = status_code
        self.text = text


class FakeSession:
    def __init__(self, events):
        self.events = list(events)
        self.calls = 0

    def patch(self, *args, **kwargs):
        self.calls += 1
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        return Response(event)


PATCH = {
    'features': {
        'status': {'properties': {'state': 'up'}},
    },
}


def check(name, cond):
    print(('%s: ' % name) + ('PASS' if cond else 'FAIL'))
    return bool(cond)


def test_pusher():
    old_sleep = pusher.time.sleep
    pusher.time.sleep = lambda _: None
    try:
        ok = True

        session = FakeSession([503, 503, 204])
        got = pusher.patch_thing('org.dt4n:host-h1', PATCH, session=session)
        ok &= check('503 retries then success', got is True and session.calls == 3)

        session = FakeSession([403, 204])
        got = pusher.patch_thing('org.dt4n:host-h1', PATCH, session=session)
        ok &= check('403 permanent no retry', got is False and session.calls == 1)

        conn_err = requests.exceptions.ConnectionError('down')
        session = FakeSession([conn_err, conn_err, conn_err, conn_err])
        got = pusher.patch_thing('org.dt4n:host-h1', PATCH, session=session)
        ok &= check('connection error exhausts retries',
                    got is False and session.calls == pusher.MAX_RETRIES + 1)

        return ok
    finally:
        pusher.time.sleep = old_sleep


class DummyCollector:
    def __init__(self, net, interval=1.0, ping_every=5, net_lock=None):
        self.i = 0

    def collect_all(self):
        self.i += 1
        return {
            'timestamp': 'test',
            'things': {
                'host-h1': {
                    'attributes': {'type': 'host'},
                    'features': {
                        'status': {'state': 'up'},
                        'traffic': {'rxBytes': self.i},
                    },
                },
            },
        }


def test_sync_agent_degrades_without_crash():
    old_collector = sync_agent.Collector
    old_make_session = sync_agent.make_session
    old_patch = sync_agent.patch_thing
    old_sleep = sync_agent.time.sleep
    sync_agent.Collector = DummyCollector
    sync_agent.make_session = lambda: object()
    sync_agent.patch_thing = lambda tid, patch, session=None: False
    sync_agent.time.sleep = lambda _: None
    try:
        sync_agent.run(net=object(), period=0, max_cycles=2, ping_every=0)
        return check('sync agent survives failed pushes', True)
    except Exception as e:
        print('sync agent survives failed pushes: FAIL (%s)' % e)
        return False
    finally:
        sync_agent.Collector = old_collector
        sync_agent.make_session = old_make_session
        sync_agent.patch_thing = old_patch
        sync_agent.time.sleep = old_sleep


def main():
    ok = test_pusher()
    ok &= test_sync_agent_degrades_without_crash()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
