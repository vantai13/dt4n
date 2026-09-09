# baseline_other

```text
s....s.......s.....................s....s.s....s.......s............ss.. [ 22%]
..................s....ss............sss......ss.......s.....ss......sss [ 45%]
..s.s.....s..s.s..s..ssss...s......ssssss..s.ss...sss.......sF..sss..... [ 68%]
....ssFs..sF..s.ssssssss..s.sss.s........s.s.ssssss..s...s.s.s.sssss.... [ 90%]
s.ss...s...................F.                                            [100%]
=================================== FAILURES ===================================
_ test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g2_kill_test.py] _

path = '/tmp/dt4n-20r2/baseline_repo/tools/g2_kill_test.py'

    @pytest.mark.parametrize("path", MODULES)
    def test_every_declared_flag_is_read_somewhere(path):
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "add_argument" not in source:
            pytest.skip("khong co CLI")

        dead = []
        for flag in sorted(_declared_flags(source)):
            if (rel, flag) in KNOWN_DEAD:
                continue
            if (rel, flag) in FORWARDED:
                continue
            if not _is_read(source, flag):
                dead.append(flag)
>       assert not dead, (
            "%s: co CLI duoc khai bao nhung KHONG BAO GIO doc: %s\n"
            "  -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi."
            % (rel, dead)
        )
E       AssertionError: tools/g2_kill_test.py: co CLI duoc khai bao nhung KHONG BAO GIO doc: ['run']
E           -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi.
E       assert not ['run']

test/test_cli_flags_are_wired.py:100: AssertionError
_ test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g3a_omega_sweep.py] _

path = '/tmp/dt4n-20r2/baseline_repo/tools/g3a_omega_sweep.py'

    @pytest.mark.parametrize("path", MODULES)
    def test_every_declared_flag_is_read_somewhere(path):
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "add_argument" not in source:
            pytest.skip("khong co CLI")

        dead = []
        for flag in sorted(_declared_flags(source)):
            if (rel, flag) in KNOWN_DEAD:
                continue
            if (rel, flag) in FORWARDED:
                continue
            if not _is_read(source, flag):
                dead.append(flag)
>       assert not dead, (
            "%s: co CLI duoc khai bao nhung KHONG BAO GIO doc: %s\n"
            "  -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi."
            % (rel, dead)
        )
E       AssertionError: tools/g3a_omega_sweep.py: co CLI duoc khai bao nhung KHONG BAO GIO doc: ['run']
E           -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi.
E       assert not ['run']

test/test_cli_flags_are_wired.py:100: AssertionError
_ test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g3b_sigma_tau_grid.py] _

path = '/tmp/dt4n-20r2/baseline_repo/tools/g3b_sigma_tau_grid.py'

    @pytest.mark.parametrize("path", MODULES)
    def test_every_declared_flag_is_read_somewhere(path):
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        with open(path, encoding="utf-8") as handle:
            source = handle.read()
        if "add_argument" not in source:
            pytest.skip("khong co CLI")

        dead = []
        for flag in sorted(_declared_flags(source)):
            if (rel, flag) in KNOWN_DEAD:
                continue
            if (rel, flag) in FORWARDED:
                continue
            if not _is_read(source, flag):
                dead.append(flag)
>       assert not dead, (
            "%s: co CLI duoc khai bao nhung KHONG BAO GIO doc: %s\n"
            "  -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi."
            % (rel, dead)
        )
E       AssertionError: tools/g3b_sigma_tau_grid.py: co CLI duoc khai bao nhung KHONG BAO GIO doc: ['run']
E           -> co chet; nguoi dung tuong da doi thi nghiem nhung thuc te khong doi.
E       assert not ['run']

test/test_cli_flags_are_wired.py:100: AssertionError
_______________________ test_known_dangling_only_shrinks _______________________

    def test_known_dangling_only_shrinks():
        """Muc nao trong KNOWN_DANGLING da duoc phuc hoi thi phai bi XOA khoi list.

        Danh sach no chet dan, khong phinh ra -- cung khuon voi `LEGACY_EXEMPT` va
        `KNOWN_DEAD`.
        """
        revived = sorted(
            s for s in KNOWN_DANGLING if os.path.exists(os.path.join(REPO, s))
        )
>       assert not revived, (
            "parquet DA co lai tren dia nhung van nam trong KNOWN_DANGLING:\n  %s\n"
            "  -> xoa muc do (danh sach nay chi duoc NGAN DI)." % "\n  ".join(revived)
        )
E       AssertionError: parquet DA co lai tren dia nhung van nam trong KNOWN_DANGLING:
E           results/SUPERSEDED/phase-22/calib_set_v3_h2_0.650.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_h2_0.850.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_h2_0.925.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_h2_0.960.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.875.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.900.parquet
E           results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.960.parquet
E           -> xoa muc do (danh sach nay chi duoc NGAN DI).
E       assert not ['results/SUPERSEDED/phase-22/calib_set_v3_h2_0.650.parquet', 'results/SUPERSEDED/phase-22/calib_set_v3_h2_0.850.parqu...ED/phase-22/calib_set_v3_poisson_0.875.parquet', 'results/SUPERSEDED/phase-22/calib_set_v3_poisson_0.900.parquet', ...]

test/test_no_dangling_parquet_refs.py:261: AssertionError
=========================== short test summary info ============================
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g2_kill_test.py]
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g3a_omega_sweep.py]
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/tmp/dt4n-20r2/baseline_repo/tools/g3b_sigma_tau_grid.py]
FAILED test/test_no_dangling_parquet_refs.py::test_known_dangling_only_shrinks
4 failed, 223 passed, 90 skipped, 3 deselected in 4.21s

```
