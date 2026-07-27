# rl/agent/replay_buffer.py
"""Replay buffer cho DT4N — port nguyen tu routing-sdn (Lesson 6.1).

ReplayBuffer (uniform): dung MAC DINH o Phase 6.
PrioritizedReplayBuffer (PER): GIU trong file nhung KHONG import mac dinh
    — de dand cho ablation neu 6.4 thay can. "Tat bang co, dung dot."
"""

import random
import numpy as np
from collections import deque


class ReplayBuffer:
    """Bo nho kinh nghiem uniform. Luu (s,a,r,s',done,next_mask).

    Vi sao sample ngau nhien? Mau lien nhau trong 1 episode rat tuong quan
    (dang nghen thi buoc sau van nghen). Train tren du lieu tuong quan ->
    mang "cham cham" tinh huong gan nhat va quen cai cu. Bốc ngẫu nhiên tu
    khap buffer -> pha tuong quan -> hoc tong quat hon.

    Loi ich phu (rat quy voi env cham ~2s/buoc cua ta): moi trai nghiem
    duoc TAI SU DUNG nhieu lan truoc khi bi day ra khoi deque.

    [9.1] Luu next_valid_mask de Bellman target khong lay max qua action
    khong ton tai. Luu mask trong buffer ro rang hon viec suy nguoc tu
    next_state, vi cach encode state co the doi khi them staleness layer.
    """

    def __init__(self, capacity: int = 50000):
        self.buffer = deque(maxlen=capacity)   # day thi tu xoa cai cu nhat

    def push(self, state, action, reward, next_state, done, next_valid_mask):
        self.buffer.append((state, action, reward, next_state, done,
                            np.asarray(next_valid_mask, dtype=np.float32)))

    def sample(self, batch_size: int = 64):
        batch = random.sample(self.buffer, batch_size)   # khong lay trung
        states, actions, rewards, next_states, dones, next_masks = zip(*batch)
        return (
            np.array(states,      dtype=np.float32),
            np.array(actions,     dtype=np.int64),
            np.array(rewards,     dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones,       dtype=np.float32),   # float de dung trong (1-done)
            np.array(next_masks,   dtype=np.float32),
        )

    def __len__(self):
        return len(self.buffer)

    def is_ready(self, batch_size: int = 64) -> bool:
        return len(self.buffer) >= batch_size


# ======================================================================
# PrioritizedReplayBuffer — COPY NGUYEN tu routing-sdn/agent/replay_buffer.py
# (dong 100 tro di). GIU O DAY nhung KHONG dung mac dinh o Phase 6.
# Chi bat lai neu Lesson 6.4/6.6 can (ablation), qua co 'use_per' trong config.
# ======================================================================
# class PrioritizedReplayBuffer:
#     ... (dan nguyen noi dung tu file cu vao day) ...
    
class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay Buffer.

    Ý tưởng cốt lõi: sample nhiều hơn từ transition có TD error lớn.
    Transition có TD error lớn = network đang sai nhiều ở đó = học được nhiều.

    Cấu trúc dữ liệu: SUM TREE
    Tại sao dùng cây thay vì list?
    Nếu dùng list: mỗi lần sample phải tính Σ priority → O(N).
    SumTree: tìm transition theo priority trong O(log N).
    Với buffer 100k transitions, log(100k) ≈ 17 thao tác vs 100k.

    SumTree hoạt động thế nào?
    - Leaf nodes: priority của từng transition
    - Internal nodes: tổng priority của subtree
    - Root: tổng tất cả priority
    - Sample: random float r in [0, root_sum], đi từ root xuống leaf
    """

    def __init__(self, capacity: int = 100000,
                 alpha: float = 0.6,
                 beta_start: float = 0.4,
                 beta_end: float = 1.0,
                 beta_anneal_steps: int = 100000,
                 epsilon: float = 1e-6):
        """
        Args:
            capacity     : số lượng transition tối đa
            alpha        : mức độ ưu tiên (0=uniform, 1=full priority)
            beta_start   : IS weight ban đầu (nhỏ → ít hiệu chỉnh)
            beta_end     : IS weight cuối (1.0 → hiệu chỉnh đầy đủ)
            beta_anneal_steps: số bước để beta tăng từ start đến end
            epsilon      : nhỏ để priority không bao giờ = 0
        """
        self.capacity = capacity
        self.alpha    = alpha
        self.beta     = beta_start
        self.beta_end = beta_end
        self.beta_increment = (beta_end - beta_start) / beta_anneal_steps
        self.epsilon  = epsilon

        # SumTree: array có kích thước 2*capacity - 1
        # Index 0 đến capacity-2: internal nodes
        # Index capacity-1 đến 2*capacity-2: leaf nodes (chứa priority)
        self.tree     = np.zeros(2 * capacity - 1, dtype=np.float64)
        self.data     = [None] * capacity  # transitions
        self.size     = 0                  # số transition hiện có
        self.ptr      = 0                  # vị trí ghi tiếp theo (circular)

        # Max priority để khởi tạo priority cho transition mới
        # Tại sao dùng max?
        # Transition mới chưa có TD error → gán priority cao nhất
        # → đảm bảo nó được sample ít nhất một lần để tính TD error thực
        self.max_priority = 1.0

    def _tree_update(self, leaf_idx: int, priority: float):
        """
        Cập nhật priority của một leaf và propagate lên root.

        leaf_idx: vị trí trong data array (0 to capacity-1)
        priority: giá trị mới

        Tree index của leaf = leaf_idx + capacity - 1
        """
        tree_idx = leaf_idx + self.capacity - 1
        delta = priority - self.tree[tree_idx]
        self.tree[tree_idx] = priority

        # Đi từ leaf lên root, cập nhật tổng
        # parent(i) = (i - 1) // 2
        while tree_idx != 0:
            tree_idx = (tree_idx - 1) // 2
            self.tree[tree_idx] += delta

    def push(self, state, action, reward, next_state, done):
        """
        Lưu transition với priority = max_priority^alpha.
        Transition mới luôn được gán priority cao nhất.
        """
        # Tính priority: max_priority^alpha
        # Tại sao ^alpha? Để smooth hóa sự chênh lệch giữa priorities.
        # alpha=0.6: priorities bớt extreme hơn so với alpha=1.0
        priority = self.max_priority ** self.alpha

        # Ghi data
        self.data[self.ptr] = (state, action, reward, next_state, done)

        # Cập nhật tree
        self._tree_update(self.ptr, priority)

        # Circular buffer
        self.ptr  = (self.ptr + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)

    def _get_leaf(self, value: float):
        """
        Tìm leaf node có priority tích lũy >= value.

        Đây là core của SumTree sampling:
        - Đi từ root (idx=0) xuống leaf
        - Mỗi bước: nếu left_child_sum >= value → đi trái
                    ngược lại → value -= left_child_sum → đi phải

        Returns: (tree_idx, leaf_priority, data_idx)
        """
        idx = 0  # bắt đầu từ root
        while idx < self.capacity - 1:   # khi chưa đến leaf
            left  = 2 * idx + 1
            right = 2 * idx + 2
            if value <= self.tree[left]:
                idx = left
            else:
                value -= self.tree[left]
                idx = right

        data_idx = idx - (self.capacity - 1)
        return idx, self.tree[idx], data_idx

    def sample(self, batch_size: int):
        """
        Sample batch_size transitions theo priority.

        Chia [0, total_priority] thành batch_size đoạn bằng nhau.
        Trong mỗi đoạn, sample ngẫu nhiên 1 điểm.
        → Stratified sampling: đảm bảo sample đều hơn, tránh cluster.

        Returns:
            states, actions, rewards, next_states, dones,
            weights (IS weights), indices (để update priority sau)
        """
        assert self.size >= batch_size, \
            f"Buffer có {self.size} transitions, cần {batch_size}"

        indices      = np.empty(batch_size, dtype=np.int32)
        is_weights   = np.empty(batch_size, dtype=np.float32)
        batch_data   = []

        total = self.tree[0]   # root = tổng tất cả priority
        segment = total / batch_size

        # Anneal beta theo thời gian
        self.beta = min(self.beta_end, self.beta + self.beta_increment)

        # Min priority để tính max IS weight
        # IS weight = (N * P(i))^(-beta)
        # Max IS weight ứng với min P(i) (transition ít được ưu tiên nhất)
        # Normalize IS weight bằng max → tất cả weight ≤ 1
        min_prob = np.min(self.tree[self.capacity-1:self.capacity-1+self.size]) / total
        # Tránh chia cho 0
        if min_prob == 0:
            min_prob = 1e-8
        max_weight = (self.size * min_prob) ** (-self.beta)

        for i in range(batch_size):
            # Sample 1 giá trị trong đoạn [segment*i, segment*(i+1)]
            a = segment * i
            b = segment * (i + 1)
            value = np.random.uniform(a, b)

            tree_idx, priority, data_idx = self._get_leaf(value)

            # Tính IS weight
            prob = priority / total
            if prob == 0:
                prob = 1e-8
            weight = (self.size * prob) ** (-self.beta)
            # Normalize bằng max_weight
            is_weights[i] = weight / max_weight

            indices[i] = data_idx
            batch_data.append(self.data[data_idx])

        # Unzip batch
        states, actions, rewards, next_states, dones = zip(*batch_data)

        return (
            np.array(states,      dtype=np.float32),
            np.array(actions,     dtype=np.int64),
            np.array(rewards,     dtype=np.float32),
            np.array(next_states, dtype=np.float32),
            np.array(dones,       dtype=np.float32),
            is_weights,   # shape (batch_size,) — IS correction weights
            indices,      # shape (batch_size,) — để update priority
        )

    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """
        Cập nhật priority sau khi tính TD error.
        Gọi sau mỗi train_step().

        Args:
            indices  : indices từ sample() call
            td_errors: TD errors tương ứng, shape (batch_size,)
        """
        for idx, error in zip(indices, td_errors):
            # priority = (|TD_error| + epsilon)^alpha
            # +epsilon: tránh priority = 0 (transition không bao giờ bị bỏ qua)
            priority = (abs(error) + self.epsilon) ** self.alpha
            self._tree_update(idx, priority)
            self.max_priority = max(self.max_priority, priority)

    def __len__(self):
        return self.size

    def is_ready(self, batch_size: int) -> bool:
        return self.size >= batch_size
