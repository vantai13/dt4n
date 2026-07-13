# rl/agent/q_network.py
"""Dueling Q-Network cho DT4N — port tu routing-sdn (Lesson 6.1).

Q(s,a) = V(s) + A(s,a) - mean_a'[A(s,a')]

Tach Q thanh:
    V(s)    : state s tot/xau bao nhieu (khong phu thuoc action)
    A(s,a)  : action a nhinh hon action trung binh bao nhieu

Loi ich: khi mang khoe, moi action gan nhu vo thuong vo phat -> network
chi can hoc "V(s) cao" MOT lan thay vi hoc rieng cho tung action.

QUAN TRONG: output shape = (batch, action_size) — GIONG HET DQN thuong,
nen DQNAgent khong phai sua gi de dung mang nay (drop-in).
"""

import torch
import torch.nn as nn


class QNetwork(nn.Module):
    def __init__(self, state_size: int, action_size: int,
                 hidden_layers: list = None, dueling: bool = True):
        super().__init__()

        if hidden_layers is None:
            hidden_layers = [128, 64]

        self.action_size = action_size
        self.dueling = dueling          # <-- CO O 6.1: co bat/tat Dueling cho ablation

        # LayerNorm dau vao: chuan hoa state truoc khi vao mang.
        # Vi sao LayerNorm chu khong BatchNorm? RL train tung sample mot,
        # BatchNorm can batch dong nhat nen hoat dong te; LayerNorm chuan hoa
        # theo chieu feature nen on dinh hon.
        self.input_norm = nn.LayerNorm(state_size)

        # ---- Trunk (than chung): cac lop an ----
        trunk_layers = []
        in_size = state_size
        for h_size in hidden_layers:
            trunk_layers.append(nn.Linear(in_size, h_size))
            trunk_layers.append(nn.LayerNorm(h_size))
            trunk_layers.append(nn.ReLU())
            in_size = h_size
        self.trunk = nn.Sequential(*trunk_layers)
        trunk_out = in_size             # = hidden_layers[-1]

        if self.dueling:
            # ---- Dueling: hai dau V va A ----
            self.value_head = nn.Sequential(
                nn.Linear(trunk_out, trunk_out // 2), nn.ReLU(),
                nn.Linear(trunk_out // 2, 1))            # V(s): 1 so
            self.advantage_head = nn.Sequential(
                nn.Linear(trunk_out, trunk_out // 2), nn.ReLU(),
                nn.Linear(trunk_out // 2, action_size))  # A(s,a): action_size so
        else:
            # ---- DQN thuong: mot dau ra thang Q ----
            self.q_head = nn.Sequential(
                nn.Linear(trunk_out, trunk_out // 2), nn.ReLU(),
                nn.Linear(trunk_out // 2, action_size))

        self._init_weights()

    def _init_weights(self):
        """He (Kaiming) init — hop voi ReLU."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, nonlinearity='relu')
                nn.init.constant_(m.bias, 0.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_norm(x)
        features = self.trunk(x)

        if self.dueling:
            V = self.value_head(features)          # (batch, 1)
            A = self.advantage_head(features)      # (batch, action_size)
            # Tru mean(A) de phep tach V/A la DUY NHAT (chong "unidentifiable").
            # keepdim=True de broadcast dung: (batch,1) voi (batch,action_size).
            Q = V + (A - A.mean(dim=1, keepdim=True))
        else:
            Q = self.q_head(features)              # (batch, action_size)
        return Q

    def get_action_values(self, state_np, device):
        """numpy state -> Q-values (khong tinh gradient). Dung khi select_action."""
        with torch.no_grad():
            t = torch.FloatTensor(state_np).unsqueeze(0).to(device)
            return self.forward(t).squeeze(0)