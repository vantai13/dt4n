#!/usr/bin/env python3
"""Oracle actions for scenario feasibility — SUA de tro DUNG link + greedy da buoc.

Oracle biet scenario. No khong phai baseline Phase 6; no tra loi cau hoi:
"scenario nay CO giai duoc bang action hien tai khong, trong bao nhieu buoc?"
TRUOC khi bat agent mu hoc.

SUA so voi ban cu:
  - TrafficFlood: khong tro cung 's2-s3' nua. Flood h1->dst nghen duong TOI dst.
    Oracle tang bw cac link TREN DUONG toi dst (de traffic that chen duoc).
  - Tra ve DANH SACH action uu tien (greedy): thu lan luot, chua thang thi thu tiep.
"""

from mininet.topology_meta import canonical
from rl.scenarios import CongestionShift, LinkDegrade, LinkDown, TrafficFlood


# Duong (chuoi link) toi tung server, theo topology tam giac cua ban.
# Khi flood dst, tang bw cac link nay de traffic that thoat.
CORE_PATH_TO_SERVER = {
    'srv1': ['s1-s2', 's2-srv1', 's1-s3', 's2-s3'],
    'srv2': ['s1-s3', 's3-srv2', 's1-s2', 's2-s3'],
}


def _dedupe(actions):
    seen = set()
    out = []
    for action in actions:
        if action in seen:
            continue
        seen.add(action)
        out.append(action)
    return out


def _flow_relief_actions(src, dst):
    """Return bw_up actions that can give a src->dst flow more room."""
    links = []
    if src and src.startswith('h'):
        links.append(canonical(src, 's1'))  # access link: h1-s1/h2-s1/h3-s1
    links.extend(CORE_PATH_TO_SERVER.get(dst, []))
    return [('bw_up', link) for link in links]


def oracle_actions(scenario):
    """Tra DANH SACH action uu tien (greedy). Oracle thu tung cai tren env that.

    Moi action la tuple (kind, link). Env se thu lan luot: neu action 1 chua
    thang, thu them action 2 (buoc sau), v.v.
    """
    if isinstance(scenario, (LinkDown, LinkDegrade)):
        # Link bi suy hao -> tang bw chinh link do. Neu la LinkDown (hong han),
        # tang bw vo ich -> oracle se THUA (dung: can steering, chua co).
        return [('bw_up', scenario.link_key)]

    if isinstance(scenario, CongestionShift):
        # Vua degrade link vua flood -> tang bw link degrade + duong toi flood_dst
        acts = [('bw_up', scenario.degrade_link)]
        acts.extend(_flow_relief_actions(scenario.flood_src,
                                         scenario.flood_dst))
        return _dedupe(acts)

    if isinstance(scenario, TrafficFlood):
        # Flood h*->dst -> tang bw cac link tren duong toi dst (traffic that chen duoc)
        return _flow_relief_actions(scenario.src, scenario.dst)

    return []


# Giu API cu cho tuong thich (code khac co the goi)
def oracle_action(scenario):
    acts = oracle_actions(scenario)
    return acts[0] if acts else None


def oracle_plan(scenario, max_steps=10):
    return oracle_actions(scenario)[:max_steps]


def oracle_feasible(scenario, max_steps=10):
    return bool(oracle_plan(scenario, max_steps=max_steps))
