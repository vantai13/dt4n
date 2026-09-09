# baseline_margins

```text
...F                                                                     [100%]
=================================== FAILURES ===================================
______ test_G23_225_canonical_input_preserves_published_numbers[g23-17c] _______

audit = 'g23-17c'

    @pytest.mark.parametrize("audit", sorted(HISTORICAL_REPORTS))
    def test_G23_225_canonical_input_preserves_published_numbers(audit: str) -> None:
        """L85 sua danh tinh input, khong duoc am tham sua ket luan G23-17."""
        _require_cell_artifacts()
        build, historical_path = HISTORICAL_REPORTS[audit]
        with open(historical_path, encoding="utf-8") as handle:
            historical = json.load(handle)
        current = build(CM.DEFAULT_CELLS, rowset="test")
>       assert _without_artifact_identity(current) == _without_artifact_identity(
            historical
        )
E       AssertionError: assert {'checks': {'...tered.'}, ...} == {'checks': {'...tered.'}, ...}
E
E         Omitting 8 identical items, use -vv to show
E         Differing items:
E         {'rows': [{'abs_ratio_gap': 0.0, 'cell': 'poisson@0.925', 'eps_regret_ms': 3.2222446816474113, 'err_neo': 0.2223986783...ap': 0.6069389222538454, 'cell': 'h2@0.700', 'eps_regret_ms': 2.861395300891912, 'err_neo': 0.12653635139919234, ...}]} != {'rows': [{'abs_ratio_gap': 0.0, 'cell': 'poisson@0.925', 'eps_regret_ms': 3.2222446816474113, 'err_neo': 0.2223986783...ap': 0.6069389222538454, 'cell': 'h2@0.700', 'eps_regret_ms': 2.861395300891912, 'err_neo': 0.12653635139919234, ...}]}
E         Use -v to get more diff

test/test_phase23_cell_margins.py:77: AssertionError
=========================== short test summary info ============================
FAILED test/test_phase23_cell_margins.py::test_G23_225_canonical_input_preserves_published_numbers[g23-17c]
1 failed, 3 passed in 3.42s

```
