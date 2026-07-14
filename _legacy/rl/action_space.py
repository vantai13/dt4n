#!/usr/bin/env python3
"""ActionSpace — dich action index (0..19) -> lenh Command Agent.

Layout 20 action (Lesson 5.4 Phan 1):
    0            : no-op
    1..8         : bw_up(link_i)    -> setBandwidth(bw * up_factor)
    9..16        : bw_down(link_i)  -> setBandwidth(bw * down_factor)
    17..19       : toggle(link)     -> disableLink/enableLink (chi link toggle-duoc)

Khong co switch (chot Lesson 5.4). Toggle chi tren link KHONG phai cau.
"""

from mininet.topology_meta import baseline_bw, find_bridges
from bridge.ditto_common import make_thing_id_link


class ActionSpace:
    def __init__(self, spec, up_factor=1.5, down_factor=0.67,
                 bw_min=1.0, bw_max=100.0):
        self.up_factor = up_factor
        self.down_factor = down_factor
        self.bw_min = bw_min
        self.bw_max = bw_max

        bws = baseline_bw(spec, 20.0, 5.0)
        self.links = sorted(bws.keys())               # 8 link, thu tu canonical
        self.baseline_bw = bws
        bridges = find_bridges(spec)
        self.toggle_links = [l for l in self.links if l not in bridges]  # 3 link

        # Xay bang tra: index -> mo ta action
        self._table = [('noop', None)]
        for l in self.links:
            self._table.append(('bw_up', l))
        for l in self.links:
            self._table.append(('bw_down', l))
        for l in self.toggle_links:
            self._table.append(('toggle', l))
        self.n = len(self._table)                     # = 20

        # Nho trang thai link up/down de toggle dung chieu (can dong bo voi env)
        self._link_up = {l: True for l in self.toggle_links}

    def reset(self):
        """Goi moi episode trong TwinEnv.reset().

        Sau soft_reset -> _restore_links, moi link o tang Mininet deu "up".
        Dict _link_up phai dong bo lai voi thuc te do, neu khong toggle se
        gui lenh nguoc chieu va state leak tich luy qua cac episode.
        """
        self._link_up = {l: True for l in self.toggle_links}

    def is_noop(self, action):
        return self._table[int(action)][0] == 'noop'

    def describe(self, action):
        kind, link = self._table[int(action)]
        return kind if link is None else '%s(%s)' % (kind, link)

    def to_command(self, action, current_bw=None):
        """Tra dict {subject, target, params} de POST xuong Command Agent.

        current_bw: bw hien tai cua link (doc tu obs). Neu None, dung baseline
        (kem chinh xac hon — nen truyen bw that tu env).
        """
        kind, link = self._table[int(action)]
        if kind == 'noop':
            return None
        target = make_thing_id_link(*link.split('-', 1)) \
            if '-' in link else make_thing_id_link(link)
        # Luu y: link key dang 'a-b'; make_thing_id_link can 2 dau.
        a, b = link.split('-')
        target = make_thing_id_link(a, b)

        if kind in ('bw_up', 'bw_down'):
            base = current_bw if current_bw is not None \
                else self.baseline_bw[link]
            factor = self.up_factor if kind == 'bw_up' else self.down_factor
            new_bw = base * factor
            new_bw = max(self.bw_min, min(self.bw_max, new_bw))  # chan tran/san
            return {'subject': 'setBandwidth', 'target': target,
                    'params': {'bw': round(new_bw, 2)}}

        if kind == 'toggle':
            up = self._link_up.get(link, True)
            subject = 'disableLink' if up else 'enableLink'
            self._link_up[link] = not up
            return {'subject': subject, 'target': target, 'params': {}}
