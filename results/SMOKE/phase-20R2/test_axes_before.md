# baseline.log

```text
....s....................................................s......s......s [ 10%]
........................sss............................................. [ 20%]
........................................................................ [ 31%]
........................................................................ [ 41%]
......s......sFsFFFFFFsFFFsFF........................................... [ 52%]
........................................................................ [ 62%]
........................................................................ [ 73%]
........................................................................ [ 83%]
........................................................................ [ 94%]
..ssssssssssssssssssssssssssssssFFFFF.                                   [100%]
=================================== FAILURES ===================================
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
=========================== short test summary info ============================
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
17 failed, 627 passed, 42 skipped in 2.88s

```
