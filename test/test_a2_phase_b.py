import numpy as np

from rl.a2.allocation import AllocationSpace
from rl.a2.scenarios.demand_scenarios import best_level_for, make_scenario


def test_allocation_reset_without_rng_keeps_legacy_middle():
    alloc = AllocationSpace(c_total=20.0, n_levels=5)
    alloc.reset(level=0)
    alloc.reset()
    assert alloc._level == 2
    assert alloc.current() == (10.0, 10.0)


def test_allocation_reset_rng_is_deterministic():
    alloc_a = AllocationSpace(c_total=20.0, n_levels=5)
    alloc_b = AllocationSpace(c_total=20.0, n_levels=5)

    got_a = alloc_a.reset(rng=np.random.default_rng(31337))
    got_b = alloc_b.reset(rng=np.random.default_rng(31337))

    assert got_a == got_b
    assert 0 <= alloc_a._level < alloc_a.n_levels


def test_named_static_skew_keeps_both_branches_live():
    for seed in range(20):
        scenario = make_scenario('S2_static_skew', seed)
        total = scenario.demand_A + scenario.demand_B
        frac_a = scenario.demand_A / total
        assert 0.30 <= frac_a <= 0.42 or 0.58 <= frac_a <= 0.70
        assert min(scenario.demand_A, scenario.demand_B) > 4.0


def test_named_far_flip_keeps_far_best_level_gap():
    for seed in range(500, 510):
        scenario = make_scenario('S4_flip_far', seed)
        level_1, _ = best_level_for(
            scenario.demand_A_1, scenario.demand_B_1)
        level_2, _ = best_level_for(
            scenario.demand_A_2, scenario.demand_B_2)
        assert abs(level_1 - level_2) == 2
