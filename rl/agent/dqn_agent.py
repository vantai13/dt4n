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
    def select_action(self, state: np.ndarray, epsilon: float = None) -> int:
        """Chon action. Mac dinh e-greedy. Khi eval GOI voi epsilon=0.

        [6.1] KHONG con valid_mask: TwinEnv moi action LUON hop le nho
        whitelist + clamp cua Command Agent (safe exploration by construction).
        """
        eps = self.epsilon if epsilon is None else epsilon

        if self.exploration == 'softmax' and epsilon is None:
            # nhanh softmax chi dung khi TRAIN va duoc bat tuong minh (6.4)
            return self._select_softmax(state)

        # --- e-greedy ---
        if np.random.random() < eps:
            return int(np.random.randint(self.action_size))
        q = self.main_net.get_action_values(state, self.device).cpu().numpy()
        return int(np.argmax(q))

    def _select_softmax(self, state):
        """Boltzmann exploration — TAT mac dinh. Bat qua config o 6.4 neu collapse."""
        q = self.main_net.get_action_values(state, self.device).cpu().numpy().astype(np.float64)
        q_shift = q - np.max(q)                        # on dinh so hoc
        exp_q = np.exp(q_shift / max(self.temperature, 1e-6))
        probs = exp_q / (np.sum(exp_q) + 1e-10)
        return int(np.random.choice(self.action_size, p=probs))

    # ==================================================================
    # REMEMBER
    # ==================================================================
    def remember(self, state, action, reward, next_state, done):
        self.buffer.push(state, action, reward, next_state, done)

    # ==================================================================
    # TRAIN STEP — Double DQN (co the tat qua use_double)
    # ==================================================================
    def train_step(self):
        if not self.buffer.is_ready(self.batch_size):
            return None

        states, actions, rewards, next_states, dones = self.buffer.sample(self.batch_size)
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)

        # Q(s,a) hien tai theo mang chinh
        q_pred = self.main_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            if self.use_double:
                # DOUBLE: mang CHINH chon action, mang TARGET dinh gia
                best_a = self.main_net(next_states_t).argmax(dim=1)
                q_next = self.target_net(next_states_t).gather(
                    1, best_a.unsqueeze(1)).squeeze(1)
            else:
                # DQN thuong: mang target vua chon vua dinh gia (co overestimation)
                q_next = self.target_net(next_states_t).max(dim=1)[0]
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