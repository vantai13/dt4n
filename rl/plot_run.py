# rl/plot_run.py
"""Ve 4 duong chan doan tu train_log.csv (Lesson 6.3).

    1. return + return_ma  (hoi tu?)
    2. epsilon             (lich kham pha)
    3. ty le terminated/truncated theo thoi gian (that bai giam?)
    4. val_return          (suc khoe THAT, greedy)

Chay: python3 -m rl.plot_run runs/<ten_run>/train_log.csv
"""

import sys
import csv
import matplotlib
matplotlib.use('Agg')            # khong can man hinh (chay tren server)
import matplotlib.pyplot as plt


def load_log(path):
    rows = list(csv.DictReader(open(path)))
    return rows


def plot(path):
    rows = load_log(path)
    ep = [int(r['episode']) for r in rows]
    ret = [float(r['return']) for r in rows]
    ma = [float(r['return_ma']) for r in rows]
    eps = [float(r['epsilon']) for r in rows]
    term = [int(r['terminated']) for r in rows]
    val_ep = [int(r['episode']) for r in rows if r['val_return'] not in ('', None)]
    val = [float(r['val_return']) for r in rows if r['val_return'] not in ('', None)]

    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    ax[0, 0].plot(ep, ret, alpha=0.3, label='return')
    ax[0, 0].plot(ep, ma, linewidth=2, label='MA-20')
    ax[0, 0].set_title('Return (hoi tu?)'); ax[0, 0].legend()

    ax[0, 1].plot(ep, eps); ax[0, 1].set_title('Epsilon (lich kham pha)')

    # ty le terminated truot 20 (that bai = 1 - ty le nay)
    win = 20
    term_rate = [sum(term[max(0, i-win):i+1]) / len(term[max(0, i-win):i+1])
                 for i in range(len(term))]
    ax[1, 0].plot(ep, term_rate); ax[1, 0].set_ylim(0, 1)
    ax[1, 0].set_title('Ty le phuc hoi (terminated) truot-20')

    ax[1, 1].plot(val_ep, val, marker='o')
    ax[1, 1].set_title('Val return (suc khoe THAT, greedy)')

    for a in ax.flat:
        a.set_xlabel('episode'); a.grid(alpha=0.3)
    out = path.replace('.csv', '_curves.png')
    plt.tight_layout(); plt.savefig(out, dpi=110)
    print('Da luu:', out)


if __name__ == '__main__':
    plot(sys.argv[1] if len(sys.argv) > 1 else 'runs/latest/train_log.csv')