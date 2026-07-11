#!/usr/bin/env python3
"""Async acknowledgement for actions sent through Ditto live messages.

Ditto is configured for fast fire-and-forget POSTs, so HTTP 202 means only
"message accepted by Ditto". Command execution must be checked later from
``logs/command_flow.log`` by correlation-id.
"""

import os
import re
import time


FLOW_LOG_PATH = 'logs/command_flow.log'
FIELD_RE = re.compile(r'(?P<key>[A-Za-z_][\w-]*)=(?P<value>[^\s\]]*)')
HEADER_RE = re.compile(
    r'^\[[^\]]+\]\s+\[(?P<source>[^\]]+)\]\s+\[(?P<level>[^\]]+)\]\s+'
    r'\[cid=(?P<cid>[^\]]+)\]\s+(?P<event>\S+)'
)

OK_EVENTS = {'EXECUTE_DONE'}
REJECT_EVENTS = {'REJECT', 'EXECUTE_ERROR', 'ERROR'}
TERMINAL_EVENTS = OK_EVENTS | REJECT_EVENTS | {'DUPLICATE_IGNORED'}


def parse_fields(line):
    """Extract compact key=value fields from one flow-log line."""
    return {m.group('key'): m.group('value') for m in FIELD_RE.finditer(line)}


def parse_flow_line(line):
    """Parse a flow-log line into a dict with event metadata and fields."""
    out = parse_fields(line)
    match = HEADER_RE.match(line)
    if match:
        out.update(match.groupdict())
    out['raw'] = line.rstrip('\n')
    return out


def _detail_from_line(record):
    """Best-effort detail extraction; detail values may contain spaces."""
    raw = record.get('raw') or ''
    marker = ' detail='
    if marker not in raw:
        return None
    value = raw.split(marker, 1)[1]
    for stop in (' code=', ' params=', ' waitMs=', ' http_status=',
                 ' correlationSource=', ' ok='):
        if stop in value:
            value = value.split(stop, 1)[0]
    return value.strip() or None


class FlowLogTail:
    """Incrementally tail command_flow.log and index records by correlation-id."""

    def __init__(self, path=FLOW_LOG_PATH):
        self.path = path
        self._pos = 0
        self._by_cid = {}
        self._n_lines = 0

    def poll(self):
        """Read new lines since the previous poll. Never scans old lines again."""
        try:
            size = os.path.getsize(self.path)
            if self._pos > size:
                self._pos = 0
                self._by_cid.clear()
            with open(self.path, encoding='utf-8', errors='replace') as f:
                f.seek(self._pos)
                for line in f:
                    self._n_lines += 1
                    record = parse_flow_line(line)
                    cid = record.get('cid')
                    if cid and cid != '-':
                        self._by_cid.setdefault(cid, []).append(record)
                self._pos = f.tell()
        except FileNotFoundError:
            return
        except OSError:
            self._pos = 0

    def lookup(self, cid, timeout=0.3, poll_interval=0.02):
        """Return records for cid, or None if not observed before timeout."""
        deadline = time.monotonic() + timeout
        while True:
            self.poll()
            if cid in self._by_cid:
                return self._by_cid[cid]
            if time.monotonic() >= deadline:
                return None
            time.sleep(poll_interval)

    def verdict(self, cid, timeout=0.3):
        """Return (executed, reason, records) for a correlation-id."""
        deadline = time.monotonic() + timeout
        records = None
        terminals = []
        while True:
            self.poll()
            records = self._by_cid.get(cid)
            if records:
                terminals = [
                    record for record in records
                    if record.get('source') == 'AGENT'
                    and record.get('event') in TERMINAL_EVENTS
                ]
                if terminals:
                    break
            if time.monotonic() >= deadline:
                if records is None:
                    return False, 'no_flow_log_entry', None
                return False, 'no_terminal_flow_event', records
            time.sleep(0.02)

        last = terminals[-1]
        event = last.get('event')
        if event in OK_EVENTS:
            return True, None, records
        if event == 'DUPLICATE_IGNORED':
            code = last.get('code')
            if code and code.startswith('2'):
                return True, None, records
        reason = _detail_from_line(last) or last.get('detail') or event
        return False, reason, records

    def prune(self):
        """Drop old correlation ids. Call at environment reset."""
        self._by_cid.clear()

    def stats(self):
        return {
            'n_lines_read': self._n_lines,
            'n_cids_indexed': len(self._by_cid),
            'file_pos': self._pos,
        }
