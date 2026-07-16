#!/usr/bin/env python3
"""A2 — Allocation level logic: quan ly phan bo bandwidth voi budget CUNG.

Budget cung: cA + cB = C_total LUON dung, vi allocation la cac muc roi rac
da tinh san sao cho tong = C_total. Khong cach nao vi pham budget.

Action tuong doi (relative shift): agent dich DAN giua cac muc -> tao chieu
thoi gian (sequential), switching cost tu nhien (moi shift la 1 buoc).
"""


class AllocationSpace:
    """Quan ly cac muc phan bo roi rac giua 2 branch voi budget co dinh."""

    def __init__(self, c_total=20.0, n_levels=5):
        self.c_total = float(c_total)
        self.n_levels = n_levels
        # sinh n_levels muc: tu (cao A, thap B) -> (thap A, cao B)
        # level 0 = A nhieu nhat, level n-1 = B nhieu nhat
        self.levels = self._build_levels()
        self._level = n_levels // 2   # bat dau o giua (can bang)

    def _build_levels(self):
        """Tao danh sach (cA, cB) sao cho cA+cB = c_total, chia deu."""
        levels = []
        # cA giam tu ~80% xuong ~20% c_total; cB = c_total - cA
        hi, lo = 0.8, 0.2
        for i in range(self.n_levels):
            frac = hi - (hi - lo) * i / (self.n_levels - 1)
            cA = round(self.c_total * frac, 1)
            cB = round(self.c_total - cA, 1)
            levels.append((cA, cB))
        return levels

    def reset(self, level=None, rng=None):
        """Reset ve muc dau episode.

        level != None: dat cung (dung cho test/debug).
        rng != None: boc ngau nhien theo rng (dung cho train/eval).
        ca hai None: ve giua, giu hanh vi cu cho tuong thich.
        """
        if level is not None:
            self._level = int(level)
        elif rng is not None:
            self._level = int(rng.integers(0, self.n_levels))
        else:
            self._level = self.n_levels // 2
        return self.current()

    def current(self):
        """Tra (cA, cB) hien tai."""
        return self.levels[self._level]

    def level_norm(self):
        """Level chuan hoa [0,1] cho state."""
        return self._level / (self.n_levels - 1)

    def apply(self, action):
        """Ap action tuong doi. Tra (cA, cB) moi.

        action: 0=no-op, 1=shift A->B (level+1), 2=shift B->A (level-1).
        Chan bien: khong vuot [0, n_levels-1] (shift ngoai bien = no-op).
        """
        if action == 1:      # shift A->B: cho B nhieu hon
            self._level = min(self._level + 1, self.n_levels - 1)
        elif action == 2:    # shift B->A: cho A nhieu hon
            self._level = max(self._level - 1, 0)
        # action 0 (no-op) hoac shift ngoai bien: giu nguyen
        return self.current()

    @property
    def n_actions(self):
        return 3
