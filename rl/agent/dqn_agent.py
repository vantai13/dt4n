# rl/agent/dqn_agent.py
"""DQN Agent cho DT4N — port + tia tu routing-sdn (Lesson 6.1).

CAU HINH TOI GIAN CO CHU DICH (nguyen tac "agent nhan chan"):
    BAT mac dinh : Double DQN, Dueling (qua QNetwork), uniform replay, e-greedy.
    TAT mac dinh : softmax exploration, entropy bonus, PER.
                   -> code GIU lai nhung dieu khien bang co config; chi bat khi
                      Lesson 6.4 quan sat thay TRIEU CHUNG (vd policy collapse),
                      va khi bat thi GHI thanh ablation. "Khong uong thuoc khi
                      chua co benh."

Vi sao tia? Agent la DUNG CU DO cho Phase 7. Moi ky thuat thua = mot confounder
lam mo tin hieu "fidelity <-> policy". Giu don gian = giu tin hieu sach.
"""

import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

from rl.agent.q_network import QNetwork
from rl.agent.replay_buffer import ReplayBuffer   # [6.1] KHONG import PER mac dinh


class DQNAgent:
    def __init__(self, state_size: int, action_size: int, config: dict):
        self.state_size = state_size
        self.action_size = action_size
        acfg = config['agent']

        # ---- Hyperparameter loi ----
        self.gamma = acfg['gamma']
        self.epsilon = acfg['epsilon_start']
        self.epsilon_end = acfg['epsilon_end']
        self.epsilon_decay = acfg['epsilon_decay']
        self.lr = acfg['learning_rate']
        self.batch_size = acfg['batch_size']
        self.target_update_freq = acfg['target_update_freq']
        hidden_layers = acfg['hidden_layers']

        # ---- 3 CO KIEN TRUC/THUAT TOAN (dieu khien ablation 6.6) ----
        self.use_double = acfg.get('use_double', True)   # Double DQN
        self.use_dueling = acfg.get('use_dueling', True)  # Dueling (truyen vao QNetwork)
        # exploration: 'epsilon_greedy' (mac dinh) hoac 'softmax' (tat, cho 6.4)
        self.exploration = acfg.get('exploration', 'epsilon_greedy')

        # ---- Device: CPU du cho mang be nay; ghi ro de tai lap ----
        self.device = torch.device(acfg.get('device', 'cpu'))

        # ---- Hai mang: chinh + target ----
        self.main_net = QNetwork(state_size, action_size, hidden_layers,
                                 dueling=self.use_dueling).to(self.device)
        self.target_net = QNetwork(state_size, action_size, hidden_layers,
                                   dueling=self.use_dueling).to(self.device)
        self.target_net.load_state_dict(self.main_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.main_net.parameters(), lr=self.lr)

        # ---- Buffer: uniform mac dinh (PER tat) ----
        self.buffer = ReplayBuffer(capacity=acfg['buffer_capacity'])

        # ---- Tham so softmax (TAT mac dinh, giu de 6.4 bat neu can) ----
        self.temperature = acfg.get('temp_start', 2.0)
        self.temperature_end = acfg.get('temp_end', 0.1)
        self.temperature_decay = acfg.get('temp_decay', 0.9985)

        self.total_steps = 0
        self.loss_history = []

    # ==================================================================
    # SELECT ACTION
    # ==================================================================
    def select_action(self, state: np.ndarray, epsilon: float = None,
                      valid_mask=None) -> int:
        """Chon action. Mac dinh e-greedy. Khi eval GOI voi epsilon=0.

        valid_mask=None giu nguyen hanh vi cu cho A2. Routing can mask vi mot
        so node chi co 1 neighbor, nen action 1 khong ton tai o cac node do.
        """
        eps = self.epsilon if epsilon is None else epsilon

        if valid_mask is None:
            valid_idx = np.arange(self.action_size)
        else:
            valid_idx = np.flatnonzero(np.asarray(valid_mask) > 0.5)
            if len(valid_idx) == 0:
                return 0

        if self.exploration == 'softmax' and epsilon is None:
            # nhanh softmax chi dung khi TRAIN va duoc bat tuong minh (6.4)
            return self._select_softmax(state, valid_mask)

        # --- e-greedy ---
        if np.random.random() < eps:
            return int(np.random.choice(valid_idx))
        q = self.main_net.get_action_values(state, self.device).cpu().numpy()
        q_masked = np.full_like(q, -np.inf)
        q_masked[valid_idx] = q[valid_idx]
        return int(np.argmax(q_masked))

    def _select_softmax(self, state, valid_mask=None):
        """Boltzmann exploration — TAT mac dinh. Bat qua config o 6.4 neu collapse."""
        q = self.main_net.get_action_values(state, self.device).cpu().numpy().astype(np.float64)
        if valid_mask is not None:
            valid = np.asarray(valid_mask) > 0.5
            if not np.any(valid):
                return 0
            q = np.where(valid, q, -1e9)
        q_shift = q - np.max(q)                        # on dinh so hoc
        exp_q = np.exp(q_shift / max(self.temperature, 1e-6))
        probs = exp_q / (np.sum(exp_q) + 1e-10)
        return int(np.random.choice(self.action_size, p=probs))

    def q_values(self, state: np.ndarray) -> np.ndarray:
        """Return raw Q-values for hand-tracing/debug output."""
        return self.main_net.get_action_values(state, self.device).cpu().numpy()

    # ==================================================================
    # REMEMBER
    # ==================================================================
    def remember(self, state, action, reward, next_state, done,
                 next_valid_mask=None):
        if next_valid_mask is None:
            next_valid_mask = np.ones(self.action_size, dtype=np.float32)
        self.buffer.push(state, action, reward, next_state, done,
                         next_valid_mask)

    # ==================================================================
    # TRAIN STEP — Double DQN (co the tat qua use_double)
    # ==================================================================
    def train_step(self):
        if not self.buffer.is_ready(self.batch_size):
            return None

        states, actions, rewards, next_states, dones, next_masks = \
            self.buffer.sample(self.batch_size)
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)
        next_masks_t = torch.FloatTensor(next_masks).to(self.device)

        # Q(s,a) hien tai theo mang chinh
        q_pred = self.main_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            NEG = -1e9
            if self.use_double:
                # DOUBLE: mang CHINH chon action hop le, mang TARGET dinh gia.
                q_next_main = self.main_net(next_states_t)
                q_next_main = q_next_main.masked_fill(next_masks_t < 0.5, NEG)
                best_a = q_next_main.argmax(dim=1)
                q_next = self.target_net(next_states_t).gather(
                    1, best_a.unsqueeze(1)).squeeze(1)
            else:
                # DQN thuong: mask ngay truoc max de action ao khong vao target.
                q_next_tgt = self.target_net(next_states_t)
                q_next_tgt = q_next_tgt.masked_fill(next_masks_t < 0.5, NEG)
                q_next = q_next_tgt.max(dim=1)[0]
            # (1 - done): het episode tu nhien thi KHONG bootstrap tuong lai
            q_target = rewards_t + self.gamma * q_next * (1.0 - dones_t)

        loss = F.smooth_l1_loss(q_pred, q_target)      # Huber loss
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.main_net.parameters(), max_norm=10)
        self.optimizer.step()

        self.total_steps += 1
        if self.total_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.main_net.state_dict())

        v = loss.item()
        self.loss_history.append(v)
        return v

    # ==================================================================
    # DECAY & SAVE/LOAD
    # ==================================================================
    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        torch.save({
            'main_net_state': self.main_net.state_dict(),
            'target_net_state': self.target_net.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'total_steps': self.total_steps,
            'config_flags': {'use_double': self.use_double,
                             'use_dueling': self.use_dueling,
                             'exploration': self.exploration},
        }, filepath)

    def load(self, filepath: str):
        ck = torch.load(filepath, map_location=self.device, weights_only=False)
        self.main_net.load_state_dict(ck['main_net_state'])
        self.target_net.load_state_dict(ck['target_net_state'])
        self.optimizer.load_state_dict(ck['optimizer_state'])
        self.epsilon = ck['epsilon']
        self.total_steps = ck['total_steps']
