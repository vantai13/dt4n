#!/usr/bin/env python3

import os
import sys
import tempfile
import threading
import time


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl.flow_ack import FlowLogTail, parse_flow_line, parse_fields  # noqa: E402


def test_parse_fields_and_event():
    line = (
        '[2026-07-10 12:00:00.123] [AGENT] [INFO] [cid=abc-123] '
        'EXECUTE_DONE subject=setBandwidth target=org.dt4n:link-s2-s3 '
        'detail=link bw -> 15.0 Mbps code=200'
    )
    fields = parse_fields(line)
    assert fields['cid'] == 'abc-123'
    assert fields['subject'] == 'setBandwidth'

    parsed = parse_flow_line(line)
    assert parsed['source'] == 'AGENT'
    assert parsed['level'] == 'INFO'
    assert parsed['event'] == 'EXECUTE_DONE'
    assert parsed['cid'] == 'abc-123'


def test_incremental_no_reread():
    with tempfile.NamedTemporaryFile('w', suffix='.log', delete=False) as f:
        path = f.name
        f.write('[t] [AGENT] [INFO] [cid=A] EXECUTE_DONE code=200\n')
    try:
        tail = FlowLogTail(path)
        tail.poll()
        assert tail.stats()['n_lines_read'] == 1

        with open(path, 'a', encoding='utf-8') as f:
            f.write('[t] [AGENT] [WARN] [cid=B] REJECT detail=bad code=400\n')
        tail.poll()
        assert tail.stats()['n_lines_read'] == 2
        assert tail.stats()['n_cids_indexed'] == 2
    finally:
        os.unlink(path)


def test_verdict_ok_reject_and_missing():
    with tempfile.NamedTemporaryFile('w', suffix='.log', delete=False) as f:
        path = f.name
        f.write('[t] [AGENT] [INFO] [cid=OK1] RECEIVE subject=setBandwidth\n')
        f.write('[t] [AGENT] [INFO] [cid=OK1] EXECUTE_DONE detail=ok code=200\n')
        f.write('[t] [AGENT] [WARN] [cid=BAD1] REJECT detail=bw out of range code=400\n')
    try:
        tail = FlowLogTail(path)
        ok, reason, _records = tail.verdict('OK1', timeout=0.01)
        assert ok and reason is None

        ok, reason, _records = tail.verdict('BAD1', timeout=0.01)
        assert not ok
        assert reason == 'bw out of range'

        ok, reason, _records = tail.verdict('GHOST', timeout=0.01)
        assert not ok and reason == 'no_flow_log_entry'
    finally:
        os.unlink(path)


def test_prune_bounds_memory():
    with tempfile.NamedTemporaryFile('w', suffix='.log', delete=False) as f:
        path = f.name
        for i in range(500):
            f.write('[t] [AGENT] [INFO] [cid=C%d] EXECUTE_DONE code=200\n' % i)
    try:
        tail = FlowLogTail(path)
        tail.poll()
        assert tail.stats()['n_cids_indexed'] == 500
        tail.prune()
        assert tail.stats()['n_cids_indexed'] == 0
    finally:
        os.unlink(path)


def test_verdict_waits_for_terminal_event():
    with tempfile.NamedTemporaryFile('w', suffix='.log', delete=False) as f:
        path = f.name
        f.write('[t] [AGENT] [INFO] [cid=LATE] RECEIVE subject=setBandwidth\n')

    def append_terminal():
        time.sleep(0.05)
        with open(path, 'a', encoding='utf-8') as f:
            f.write('[t] [AGENT] [INFO] [cid=LATE] EXECUTE_DONE code=200\n')

    try:
        threading.Thread(target=append_terminal, daemon=True).start()
        tail = FlowLogTail(path)
        ok, reason, _records = tail.verdict('LATE', timeout=0.3)
        assert ok and reason is None
    finally:
        os.unlink(path)


if __name__ == '__main__':
    for name, fn in sorted(globals().items()):
        if name.startswith('test_'):
            fn()
            print('PASS', name)
