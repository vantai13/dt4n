"""Certification layer for DT4N v7.

Phase 21: age-conditional conformal prediction intervals.
Phase 22: simultaneous coverage for K actions.
Phase 23: trust gate (accept/abstain) and risk-coverage frontier.

The analysis unit for this package is a block:
1435 samples = 14.35 s = 5*tau_core.

Samples spaced by 10 ms are strongly correlated, so conformal coverage is
claimed at block granularity, not sample granularity.
"""
