# baseline_g3_order

```text
.F.......FF......                                                        [100%]
=================================== FAILURES ===================================
___________ test_quantize_target_is_independent_per_window_rounding ____________

    def test_quantize_target_is_independent_per_window_rounding():
        rng = np.random.default_rng(1)
        target = rng.uniform(0.7, 0.9, size=(len(LINKS), 10000))
        sent, packets = quantize_target(target)
        wanted = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
>       assert np.array_equal(packets, np.round(wanted))
E       assert False
E        +  where False = <function array_equal at 0x7f700254b7f0>(array([[56., 62., 51., ..., 50., 53., 55.],\n       [42., 37., 38., ..., 41., 46., 39.],\n       [40., 41., 41., ..., 45..., 45., 39.],\n       [61., 51., 52., ..., 58., 60., 59.],\n       [36., 37., 47., ..., 41., 43., 41.]], shape=(8, 10000)), array([[111., 123., 101., ..., 100., 106., 110.],\n       [ 85.,  73.,  76., ...,  81.,  92.,  79.],\n       [ 80.,  83....\n       [122., 102., 103., ..., 117., 120., 119.],\n       [ 73.,  73.,  93., ...,  82.,  85.,  82.]], shape=(8, 10000)))
E        +    where <function array_equal at 0x7f700254b7f0> = np.array_equal
E        +    and   array([[111., 123., 101., ..., 100., 106., 110.],\n       [ 85.,  73.,  76., ...,  81.,  92.,  79.],\n       [ 80.,  83....\n       [122., 102., 103., ..., 117., 120., 119.],\n       [ 73.,  73.,  93., ...,  82.,  85.,  82.]], shape=(8, 10000)) = <function round at 0x7f700253fe70>(array([[111.28492718, 123.45252972, 101.08625833, ..., 100.31952436,\n        105.95864026, 110.44254355],\n       [ 84....  [ 72.95128482,  73.18837116,  93.40522273, ...,  82.25487577,\n         85.29555315,  82.43842231]], shape=(8, 10000)))
E        +      where <function round at 0x7f700253fe70> = np.round

test/test_g3_dryrun.py:35: AssertionError
________ test_quantization_step_is_smaller_in_dangerous_persistent_cell ________

    def test_quantization_step_is_smaller_in_dangerous_persistent_cell():
        fast = quantization_step_packets(A0, 0.0, 3.0, 3.0)
        slow = quantization_step_packets(A0, 0.0, 30.0, 30.0)
        assert np.all(slow < fast)
>       assert slow[LINKS.index("ad")] == pytest.approx(0.343113, abs=1e-5)
E       assert np.float64(0....0997140220743) == 0.343113 ± 1.0e-05
E
E         comparison failed
E         Obtained: 0.12140997140220743
E         Expected: 0.343113 ± 1.0e-05

test/test_g3_dryrun.py:54: AssertionError
__________________ test_mixture_acf_has_the_signed_endpoints ___________________

    def test_mixture_acf_has_the_signed_endpoints():
        for lag in (1, 2, 3):
>           assert mixture_acf(0.0, 30.0, 3.0, lag) == pytest.approx(
                np.exp(-lag * DT_S / 3.0), abs=1e-15
            )
E           assert 0.9672161004820059 == 0.9355069850316178 ± 1.0e-15
E
E             comparison failed
E             Obtained: 0.9672161004820059
E             Expected: 0.9355069850316178 ± 1.0e-15

test/test_g3_dryrun.py:59: AssertionError
=========================== short test summary info ============================
FAILED test/test_g3_dryrun.py::test_quantize_target_is_independent_per_window_rounding
FAILED test/test_g3_dryrun.py::test_quantization_step_is_smaller_in_dangerous_persistent_cell
FAILED test/test_g3_dryrun.py::test_mixture_acf_has_the_signed_endpoints - as...
3 failed, 14 passed in 1.12s

```
