# rl/run_identity.py
"""Tao danh tinh cho moi run — chong 'run vo danh' (nguyen tac reproducibility).

Ten thu muc: runs/{timestamp}_{githash}_{seed}/
Chua: config da dung (copy), logs, checkpoints. Tu ten -> tai lap duoc.
"""

import os
import shutil
import subprocess
from datetime import datetime


def _git_hash_short():
    """Lay 7 ky tu dau cua git commit hien tai; 'nogit' neu khong co."""
    try:
        h = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL).decode().strip()
        # danh dau neu co thay doi chua commit (khong sach)
        dirty = subprocess.call(
            ['git', 'diff', '--quiet'], stderr=subprocess.DEVNULL) != 0
        return h + ('-dirty' if dirty else '')
    except Exception:
        return 'nogit'


def create_run_dir(log_dir, seed, config_paths=()):
    """Tao thu muc run + copy config vao trong. Tra ve duong dan."""
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    run_name = '%s_%s_seed%d' % (ts, _git_hash_short(), seed)
    run_dir = os.path.join(log_dir, run_name)
    os.makedirs(os.path.join(run_dir, 'checkpoints'), exist_ok=True)
    # copy cac config da dung vao run (bang chung config chinh xac)
    for p in config_paths:
        if os.path.exists(p):
            shutil.copy(p, os.path.join(run_dir, os.path.basename(p)))
    return run_dir