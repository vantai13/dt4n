# Phase L / Lesson L.1 -- Bien ban ha tang do

Ngay: 2026-07-29
Base commit truoc L.1: 156563b
Script: measurements/l1_verify.py
Output JSON: results/phase-L/l1_infra_0729_0716.json

Lenh da chay:

```bash
sudo -n mn -c
sudo -n python3 -u -m measurements.l1_verify --bw 6 --queue 13 --delay 3
```

Ket luan ngan: PASS. Ha tang tach qdisc dung thiet ke, burst chot = 1600 B,
HTB that su shaping (overlimits tang, tokens am), va doi chung V-L4 khop
ti le 5/13.

## 1. Qdisc MAC DINH truoc khi can thiep

```text
--- s1-eth2 ---
qdisc noqueue 0: root refcnt 2
--- s2-eth2 ---
qdisc noqueue 0: root refcnt 2
--- h1-eth0 ---
qdisc noqueue 0: root refcnt 2
--- s1-eth1 ---
qdisc noqueue 0: root refcnt 2
```

Khong co hang doi an tren cac link host<->switch va link switch<->switch
truoc khi can thiep.

## 2. Lenh tc da chay

```text
tc qdisc del dev s1-eth2 root
tc qdisc add dev s1-eth2 root handle 1: htb default 10
tc class add dev s1-eth2 parent 1: classid 1:10 htb rate 6mbit burst 1600b cburst 1600b
tc qdisc add dev s1-eth2 parent 1:10 handle 10: bfifo limit 19656
tc qdisc del dev s2-eth2 root
tc qdisc add dev s2-eth2 root handle 1: netem delay 3ms
```

## 3. Output tho sau khi dung qdisc

### Chieu DO: s1-eth2, s1 -> s2

```text
qdisc htb 1: root refcnt 9 r2q 10 default 0x10 direct_packets_stat 0 direct_qlen 1000
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
qdisc bfifo 10: parent 1:10 limit 19656b
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
```

```text
class htb 1:10 root leaf 10: prio 0 rate 6Mbit ceil 6Mbit burst 1600b cburst 1600b
 Sent 90 bytes 1 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
 lended: 1 borrowed: 0 giants: 0
 tokens: 31459 ctokens: 31459
```

Doc bang mat:

- Chieu DO co dung hai tang qdisc: `htb` root va `bfifo` leaf.
- Khong co `netem` tren chieu DO.
- `bfifo limit 19656b` co don vi byte, bang 13 x 1512 B.
- `burst 1600b cburst 1600b` dung nhu preregistration.

### Chieu VE: s2-eth2, s2 -> s1

```text
qdisc netem 1: root refcnt 9 limit 1000 delay 3ms
 Sent 0 bytes 0 pkt (dropped 0, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
```

Chieu VE chi co `netem delay 3ms`, khong co `htb`.

## 4. Ket qua kiem V-L1a..V-L1f

| Kiem | Noi dung | Ket qua |
|---|---|---|
| V-L1a | htb o root chieu DO | PASS |
| V-L1b | KHONG co netem chieu DO | PASS |
| V-L1c | bfifo limit = q x 1512 byte = 19656 B | PASS |
| V-L1d | burst = 1600 B | PASS |
| V-L1e | chieu VE chi co netem | PASS |
| V-L1f | h1-eth0 khong co hang doi an | PASS: noqueue |
| V-L1f | s1-eth1 khong co hang doi an | PASS: noqueue |

Tran buffer ly thuyet cho cau hinh kiem: 26.21 ms (= 19656 B x 8 / 6 Mbps).

## 5. Ping: netem chieu ve hoat dong

```text
10 packets transmitted, 10 received, 0% packet loss, time 1803ms
rtt min/avg/max/mdev = 3.051/3.413/6.508/1.031 ms
```

RTT trung binh = 3.413 ms, khop ky vong gan 3 ms cua netem chieu ve.
Goi dau tien cao hon do ARP/warm-up, cac goi sau on dinh quanh 3.05-3.11 ms.

## 6. Quet burst

| burst (B) | rate dat (Mbps) | % danh nghia |
|---:|---:|---:|
| 1600 | 5.995 | 99.9 |
| 2400 | 5.996 | 99.9 |
| 3200 | 5.997 | 100.0 |
| 6400 | 6.004 | 100.1 |
| 15000 | 6.015 | 100.2 |

Ket luan: burst da chon = 1600 B, la gia tri nho nhat dat >= 98%.
Mac dinh Mininet 15000 B = 9.92 goi MTU, qua lon so voi buffer 13 goi.

## 6b. Raw tc sau qua tai voi burst chot

Da doi ve burst chot 1600 B va bom qua tai:

```text
rate=5.973 Mbps, peak_backlog=19656 B
```

Raw qdisc:

```text
qdisc htb 1: root refcnt 9 r2q 10 default 0x10 direct_packets_stat 0 direct_qlen 1000
 Sent 22656126 bytes 15004 pkt (dropped 17321151, overlimits 14965 requeues 0)
 backlog 0b 0p requeues 0
qdisc bfifo 10: parent 1:10 limit 19656b
 Sent 22656126 bytes 15004 pkt (dropped 17321151, overlimits 0 requeues 0)
 backlog 0b 0p requeues 0
```

Raw class:

```text
class htb 1:10 root leaf 10: prio 0 rate 6Mbit ceil 6Mbit burst 1600b cburst 1600b
 Sent 22656126 bytes 15004 pkt (dropped 17321151, overlimits 14965 requeues 0)
 backlog 0b 0p requeues 0
 lended: 15004 borrowed: 0 giants: 0
 tokens: -30992 ctokens: -30992
```

Bang chung co che:

- `overlimits 14965` tren HTB tang sau qua tai: HTB dang shaping.
- `tokens: -30992`: token bucket can, class dang bi gioi han toc do.
- `peak_backlog=19656 B`: bfifo cham tran dung 13 x 1512 B.

## 7. Doi chung duong V-L4

| q (goi) | tran ly thuyet (ms) | backlog do (B) | backlog (ms) | % tran |
|---:|---:|---:|---:|---:|
| 13 | 26.21 | 19656 | 26.21 | 100 |
| 5 | 10.08 | 7560 | 10.08 | 100 |

Ty le backlog(q=5)/backlog(q=13) = 0.385.
Mong doi = 5/13 = 0.385.
Ket qua: PASS.

## 8. Tran buffer chot cho ba cau hinh

| (bw, q) | limit bfifo (B) | tran (ms) |
|---|---:|---:|
| (8, 18) | 27216 | 27.22 |
| (6, 13) | 19656 | 26.21 |
| (4, 10) | 15120 | 30.24 |

## 9. Chenh lech so voi ban ke hoach v8 goc

- v8 goc dung TCLink params1/params2. Bo, ly do: `burst 15k` va
  `max_queue_size` di vao `netem limit` theo goi.
- Thay bang tc thu cong: `htb` chi rate, `bfifo` chi buffer, `netem` chi
  propagation o chieu ve.
- Doi cau hinh dung `tc class change` va `tc qdisc change`, khong restart
  Mininet. Dieu nay cho phep ngau nhien hoa thu tu toan phan o L.6.
