# Lesson 9.1 - Action Masking

## Van de

Agent DT4N da go `valid_mask` o Lesson 6.1 vi A2 co tinh chat "moi action
luon hop le" nho whitelist va clamp. Routing pha gia dinh do: node `E` chi co
1 neighbor, node `F` chi co 1 neighbor, nen action `1` khong ton tai o hai
node nay.

Neu khong mask, epsilon-greedy co the chon action khong ton tai, lam episode
bi truncate som va dua nhieu transition chet vao replay buffer. Bellman target
cung co the lay `max_a' Q(s', a')` qua action khong ton tai, tuc la dua mot gia
tri ngoai suy vao duong di hoc.

## Thay doi

- `rl/agent/replay_buffer.py`: uniform replay buffer luu them
  `next_valid_mask`.
- `rl/agent/dqn_agent.py`: `select_action`, `_select_softmax`, `remember`, va
  `train_step` nhan/lan truyen mask.
- `test/routing/test_action_masking.py`: khoa hanh vi action masking, Bellman
  target, neighbor order, env mask, va tuong thich nguoc A2.

`valid_mask=None` giu hanh vi cu: moi action duoc xem la hop le. Nho do code A2
cu van goi `select_action(obs)` va `remember(...)` duoc.

## Quyet dinh ky thuat

1. Luu mask trong buffer thay vi suy nguoc tu `next_state`. Suy nguoc se coupling
   agent vao cach env encode node; Phase 11 co staleness wrapper nen coupling an
   nay de gay am tham.
2. Mask random branch va greedy branch. Dau train epsilon cao, neu chi mask
   greedy thi phan nguy hiem nhat van con.
3. Trong `train_step`, dung `-1e9` thay vi `-inf`. `-inf * 0.0` co the sinh
   `nan`; `-1e9` du am de khong thang `argmax` nhung van la so huu han.
4. Double DQN mask o buoc chon action bang `main_net(...).argmax()`. Buoc dinh
   gia dung `target_net(...).gather(...)`, nen khong co `max` moi.
5. Env van giu nhanh phat invalid action. Agent mask la lop phong thu dau tien;
   env guard bat baseline/script nao goi `env.step(...)` sai.
6. Khong `sorted()` neighbor. Thu tu edge trong `TOPO` la hop dong action-index;
   test `test_neighbor_order_locked` khoa hop dong nay.

## Validation

```bash
python3 -m pytest test/routing/test_action_masking.py -v
python3 scripts/gate_route_stage.py
python3 -m pytest test/routing/ -q
```

Kiem tra diff tap trung:

```bash
git diff --stat rl/agent/
git diff rl/agent/ | grep "^+" | grep -i "per\|priorit\|entropy\|curriculum"
```

Lenh grep thu hai ky vong rong: Lesson 9.1 chi them masking, khong tien tay
bat PER/entropy/curriculum.
