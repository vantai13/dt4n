#!/usr/bin/env python3
"""Backward-compatible wrapper for the calibrated routing oracle gate."""

import sys

from rl.routing.oracle_gate import main


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
