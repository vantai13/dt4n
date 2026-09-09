# Full pytest run

Command: `/home/ubuntu/miniforge3/envs/sdn_rl/bin/python -m pytest -q`

```text
........................................................................ [  2%]
..................................s....s.......s.....................s.. [  4%]
..s.s....s.......s............ss....................s....ss............s [  7%]
ss......ss.......s.....ss......sss..s.s.....s..s..s..s..ssss...s......ss [  9%]
ssss..s.ss...sss.......sF..sss.........ssFs..sF..s.ssssssss..s.sss.s.... [ 11%]
....s.s.ssssss..s...s.s.s.sssss....s.ss...s.............ssss............ [ 14%]
........................................................................ [ 16%]
........................................................................ [ 19%]
...........F.......FF................................................... [ 21%]
........................................................................ [ 23%]
........................................................................ [ 26%]
........................................................................ [ 28%]
.....................F.....s............................................ [ 31%]
........s......s......s........................sss...................... [ 33%]
........................................................................ [ 35%]
........................................................................ [ 38%]
..............................s......sFsFFFFFFsFFFsFF................... [ 40%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 47%]
........................................................................ [ 50%]
..........................ssssssssssssssssssssssssssssssFFFFF........... [ 52%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 67%]
..............................................F......................... [ 69%]
.................................................s...................... [ 71%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 79%]
.................................s...................................... [ 81%]
........................................................................ [ 83%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 98%]
.....................................................                    [100%]
=================================== FAILURES ===================================
_ test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g2_kill_test.py] _

path = '/home/ubuntu/dt4n/tools/g2_kill_test.py'

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
_ test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g3a_omega_sweep.py] _

path = '/home/ubuntu/dt4n/tools/g3a_omega_sweep.py'

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
_ test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g3b_sigma_tau_grid.py] _

path = '/home/ubuntu/dt4n/tools/g3b_sigma_tau_grid.py'

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
___________ test_quantize_target_is_independent_per_window_rounding ____________

    def test_quantize_target_is_independent_per_window_rounding():
        rng = np.random.default_rng(1)
        target = rng.uniform(0.7, 0.9, size=(len(LINKS), 10000))
        sent, packets = quantize_target(target)
        wanted = target * CAP_BPS[:, None] * DT_S / (WIRE_BYTES * 8.0)
>       assert np.array_equal(packets, np.round(wanted))
E       assert False
E        +  where False = <function array_equal at 0x78eed579a270>(array([[56., 62., 51., ..., 50., 53., 55.],\n       [42., 37., 38., ..., 41., 46., 39.],\n       [40., 41., 41., ..., 45..., 45., 39.],\n       [61., 51., 52., ..., 58., 60., 59.],\n       [36., 37., 47., ..., 41., 43., 41.]], shape=(8, 10000)), array([[111., 123., 101., ..., 100., 106., 110.],\n       [ 85.,  73.,  76., ...,  81.,  92.,  79.],\n       [ 80.,  83....\n       [122., 102., 103., ..., 117., 120., 119.],\n       [ 73.,  73.,  93., ...,  82.,  85.,  82.]], shape=(8, 10000)))
E        +    where <function array_equal at 0x78eed579a270> = np.array_equal
E        +    and   array([[111., 123., 101., ..., 100., 106., 110.],\n       [ 85.,  73.,  76., ...,  81.,  92.,  79.],\n       [ 80.,  83....\n       [122., 102., 103., ..., 117., 120., 119.],\n       [ 73.,  73.,  93., ...,  82.,  85.,  82.]], shape=(8, 10000)) = <function round at 0x78eed578ad70>(array([[111.28492718, 123.45252972, 101.08625833, ..., 100.31952436,\n        105.95864026, 110.44254355],\n       [ 84....  [ 72.95128482,  73.18837116,  93.40522273, ...,  82.25487577,\n         85.29555315,  82.43842231]], shape=(8, 10000)))
E        +      where <function round at 0x78eed578ad70> = np.round

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
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/adjudication_r2.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/adjudication_r2.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/adjudication_r2.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'amendment_measurements_committed_before_adjudication': '1c3a4baf5d0ce4f8e40d76eaa9377ba8492b239e', 'cross_phase_esti..._gate': {'R5_median_pass': True, 'actual_results_committed': True, 'branch_join_pass': True, 'canary_pass': True}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_report.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_report.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/calib_p0925_tau10_report.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'blocks_per_cell': {'0_0': 171, '0_1': 196, '0_2': 220, '0_3': 270, ...}, 'gap': {'gap_true': {'p10': 3.0888221263885...3, 0.7], 'sigma_rho': 0.01, ...}, 'git_dirty': True, 'git_hash': 'd8c904c0dfd39afc3ca6a3d1fae603c5b7e93886', ...}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_v3_report.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_v3_report.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/calib_p0925_tau10_v3_report.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'blocks_per_cell': {'0_0': 171, '0_1': 196, '0_2': 220, '0_3': 270, ...}, 'gap': {'gap_true': {'p10': 3.0888221263885...3, 0.7], 'sigma_rho': 0.01, ...}, 'git_dirty': True, 'git_hash': '44e4ec63d217e637c0f75a9d5591ad998aaf8830', ...}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/clip_direction_r2.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/clip_direction_r2.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/clip_direction_r2.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'note': 'Replay same AR1 cell and seeds; endpoint counts match raw n_clipped diagnostics exactly.', 'rows': [{'ar1_cl...'ad': 0, 'bc': 0, 'bd': 0, ...}, 'ceiling_count': 0, 'floor_by_link': {'ac': 0, 'ad': 0, 'bc': 0, 'bd': 0, ...}, ...}]}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/conformal_u_cond.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'H3': {'marginal': 0.90999570619155, 'pass': True}, 'H4': {'pass': True}, 'H6': {'pass': True, 'qhat_alpha_over_k': {...': 51.23406982421875, '101': 34.913299560546875, ...}}, 'V3': {'pass': True, 'sd_ratio_mean': 0.3052781159796635}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond_load.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond_load.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/conformal_u_cond_load.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'H3': {'marginal': 0.9126990559213561, 'pass': True}, 'H4': {'pass': True}, 'H6': {'pass': True, 'qhat_alpha_over_k':...': 48.673221588134766, '101': 38.94731903076172, ...}}, 'V3': {'pass': True, 'sd_ratio_mean': 0.2997003792595483}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_main.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_main.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/conformal_u_main.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'H3': {'marginal': 0.9105732260973035, 'pass': True}, 'H4': {'pass': True}, 'H6': {'pass': True, 'qhat_alpha_over_k':...': 38.25224304199219, '101': 33.12382507324219, ...}}, 'V3': {'pass': True, 'sd_ratio_mean': 0.30513017837879713}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/hygiene_checks.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'KIEM_1_canary_NC_T2_4': {'max_span_any_numeric_column': 0.0, 'n_canary': 6, 'n_distinct_sha256': 1, 'verdict': 'PASS...ai nhanh cham diem tren HAI DAI HANG KHAC NHAU.', 'n_groups': 100, 'n_groups_violating': 2, ...}, 'minutes': 30.3, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks_r2.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks_r2.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/hygiene_checks_r2.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'KIEM_1_canary_NC_T2_4': {'max_span_any_numeric_column': 0.0, 'n_canary': 6, 'n_distinct_sha256': 1, 'verdict': 'PASS...c 0 la bang chung cua so lech', 'threshold': 0.01, ...}, 'git_commit': 'd8956cf5650c023c809659aa0c58886b79388b4a', ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/preservation_r2.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/preservation_r2.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/preservation_r2.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'changed': [], 'n_files': 336, 'sha256_before_and_after': {'docs/phase-T2/01-prediction-signed.json': '68e975c2c08247...e-T2/sweep/run_log.jsonl': 'b4909f382e2bd4724df44e65ed943032be7bc3cc88280d525c53f66089330a22', ...}, 'verdict': 'PASS'}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/realizability_grid.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/realizability_grid.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/realizability_grid.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'n_cells': 96, 'n_realizable': 96, 'n_rejected': 0, 'rejected_by_reason': {}, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/rms_reference_check_r2.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/rms_reference_check_r2.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/rms_reference_check_r2.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'consequence': 'Algebraic identity passes, but it does not make the two estimands equal. Do not adjudicate signed RMS...'n': 10000.0, 'rms_e_model': 2.15153199684004, ...}, 'formula': 'sqrt(rms_e_model**2 + 2*cov_e + rms_e_stale**2)', ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s101.meta.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s101.meta.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/traces/rho_p0925_tau10_s101.meta.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'B3_sigma_scale_mismatch': {'calib_sigma_rho_hardcoded': 0.01, 'ratio': 2.1802325581395348, 'trace_sigma_design': 0.0...U_EDGES. Day la B3. KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21.'}, 'a': 0.9, 'cycles': 100.0, 'dt': 0.005, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s102.meta.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s102.meta.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/traces/rho_p0925_tau10_s102.meta.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'B3_sigma_scale_mismatch': {'calib_sigma_rho_hardcoded': 0.01, 'ratio': 2.1802325581395348, 'trace_sigma_design': 0.0...U_EDGES. Day la B3. KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21.'}, 'a': 0.9, 'cycles': 100.0, 'dt': 0.005, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s103.meta.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s103.meta.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/traces/rho_p0925_tau10_s103.meta.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'B3_sigma_scale_mismatch': {'calib_sigma_rho_hardcoded': 0.01, 'ratio': 2.1802325581395348, 'trace_sigma_design': 0.0...U_EDGES. Day la B3. KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21.'}, 'a': 0.9, 'cycles': 100.0, 'dt': 0.005, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s104.meta.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s104.meta.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/traces/rho_p0925_tau10_s104.meta.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'B3_sigma_scale_mismatch': {'calib_sigma_rho_hardcoded': 0.01, 'ratio': 2.1802325581395348, 'trace_sigma_design': 0.0...U_EDGES. Day la B3. KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21.'}, 'a': 0.9, 'cycles': 100.0, 'dt': 0.005, ...}

test/test_no_stale_axes.py:490: AssertionError
_ test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s105.meta.json] _

path = '/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s105.meta.json'

    @pytest.mark.parametrize("path", _pending_json())
    def test_pending_artifacts_declare_what_they_wait_for(path):
        """PENDING/ khac SUPERSEDED/: no CHO, khong bi THAY THE.

        Hai rang buoc, va cai thu hai lam tang nay TU DON:
          (1) phai khai `pending_on` -- truc nao chua duyet
          (2) truc do phai THUC SU chua duyet; neu no DA duoc duyet thi test do
              va bat phai promote len LIVE/, thay vi de artifact nam quen o day.
        """
        rel = os.path.relpath(path, PENDING).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            pytest.skip("khong phai artifact dang dict")

        # ★ SUA (amendment 23-60): thieu `validity` KHONG con la ly do bo qua.
        # Ban cu `skip` khi thieu `validity` -- tuc la muon THOAT test chi can
        # khong viet `validity`, ma `validity` chinh la thu can kiem. PASS RONG
        # (vacuous pass), cung lop loi voi `R1` ("sensitivity chua thuc su chay").
        # Do duoc 2026-08-24: 16/16 file PENDING/phase-23 thoat theo dung duong do.
        if rel in PENDING_NO_VALIDITY_GRANDFATHERED:
            pytest.skip("grandfathered: %s" % PENDING_NO_VALIDITY_GRANDFATHERED[rel])

        # Chinh sidecar la CO CHE KHAI, khong phai mot artifact do dac.
        if rel == "phase-T2/FROZEN_PENDING_ON.json":
            pytest.skip("sidecar khai bao, khong phai artifact do dac")

        # Artifact BI DONG BANG (sha256 ghim noi khac) khai `pending_on` qua
        # sidecar thay vi trong chinh no. Hieu luc cua duong nay den tu
        # test_frozen_entries_prove_the_freeze_instead_of_declaring_it: muc nao
        # khong chung minh duoc viec dong bang thi KHONG toi duoc day.
        if rel in FROZEN:
            entry = FROZEN[rel]
            approved_axes = _approved()
            pend = entry["pending_on"]
            assert pend, "%s: muc sidecar khong khai pending_on" % rel
            for axis in pend:
                assert axis in approved_axes, "%s: truc la %r" % (rel, axis)
                assert entry["axis_label"] not in approved_axes[axis], (
                    "%s: khai cho %s nhung nhan %r DA duoc duyet -> PROMOTE."
                    % (rel, axis, entry["axis_label"]))
            return

>       assert "validity" in payload, (
            f"{rel}: nam o PENDING/ nhung KHONG co khoi validity.\n"
            f"  -> them validity_block(...)/sla_only_validity_block(...) vao script "
            f"sinh ra no,\n"
            f"  -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua."
        )
E       AssertionError: phase-T2/traces/rho_p0925_tau10_s105.meta.json: nam o PENDING/ nhung KHONG co khoi validity.
E           -> them validity_block(...)/sla_only_validity_block(...) vao script sinh ra no,
E           -> hoac chuyen sang SMOKE/ neu no khong nham tao ket qua.
E       assert 'validity' in {'B3_sigma_scale_mismatch': {'calib_sigma_rho_hardcoded': 0.01, 'ratio': 2.1802325581395348, 'trace_sigma_design': 0.0...U_EDGES. Day la B3. KHONG sua SIGMA_RHO -- sua se pha tai tao Phase 21.'}, 'a': 0.9, 'cycles': 100.0, 'dt': 0.005, ...}

test/test_no_stale_axes.py:490: AssertionError
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
=============================== warnings summary ===============================
bridge/command_agent.py:114
bridge/command_agent.py:114
  /home/ubuntu/dt4n/bridge/command_agent.py:114: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    'ts': datetime.datetime.utcnow().isoformat() + 'Z',

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g2_kill_test.py]
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g3a_omega_sweep.py]
FAILED test/test_cli_flags_are_wired.py::test_every_declared_flag_is_read_somewhere[/home/ubuntu/dt4n/tools/g3b_sigma_tau_grid.py]
FAILED test/test_g3_dryrun.py::test_quantize_target_is_independent_per_window_rounding
FAILED test/test_g3_dryrun.py::test_quantization_step_is_smaller_in_dangerous_persistent_cell
FAILED test/test_g3_dryrun.py::test_mixture_acf_has_the_signed_endpoints - as...
FAILED test/test_no_dangling_parquet_refs.py::test_known_dangling_only_shrinks
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/adjudication_r2.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_report.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/calib_p0925_tau10_v3_report.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/clip_direction_r2.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_cond_load.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/conformal_u_main.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/hygiene_checks_r2.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/preservation_r2.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/realizability_grid.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/rms_reference_check_r2.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s101.meta.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s102.meta.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s103.meta.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s104.meta.json]
FAILED test/test_no_stale_axes.py::test_pending_artifacts_declare_what_they_wait_for[/home/ubuntu/dt4n/results/PENDING/phase-T2/traces/rho_p0925_tau10_s105.meta.json]
FAILED test/test_phase23_cell_margins.py::test_G23_225_canonical_input_preserves_published_numbers[g23-17c]
25 failed, 2842 passed, 138 skipped, 13 deselected, 2 warnings in 688.02s (0:11:28)

```
