"""Lesson 23.25 -- test cho ma tran tuong quan link va truc omega.

Bao gom `NC-25-2` (hoi phuc `w` da biet) va `PC-25-1` (pooling artifact PHAI
fire). Mot doi chung duong khong fire thi moi so khac mat gia tri (`L101`).
"""
import csv
import inspect
import json

import numpy as np
import pytest

from measurements import link_corr_matrix as A
from twin import topology_v7 as T7


# ------------------------------------------------ M-242/243/244 kiem wiring
def test_M242_sum_k2_is_five():
    assert A.SUM_K2 == pytest.approx(5.0, abs=1e-12)


def test_structured_and_null_pairs_partition_all_28():
    assert len(A.S_PAIRS) == 12
    assert len(A.NULL_PAIRS) == 16
    assert len(A.S_PAIRS) + len(A.NULL_PAIRS) == 28


def test_null_pairs_are_the_right_ones():
    """Cac cap KHONG chung duong nao -- negative control CO SAN trong topology.

    `(uA,vD)` va `(uB,vC)` KHONG nam trong danh sach nay: chung chung `P2`/`P3`.
    Test ghim dieu do vi doc so do bang mat rat de sai.
    """
    got = {frozenset(p) for p in A.NULL_PAIRS}
    assert frozenset(("uA", "uB")) in got
    assert frozenset(("vC", "vD")) in got
    assert frozenset(("ac", "bd")) in got
    assert frozenset(("uA", "vD")) not in got     # chung P2
    assert frozenset(("uB", "vC")) not in got     # chung P3


def test_M243_M244_variance_ratios_match_analysis():
    w = A.wiring_checks()
    assert w["M_243_var_ratio_adjacent_at_omega1"] == pytest.approx(1.7071, abs=1e-3)
    assert w["M_244_var_ratio_crossed_at_omega1"] == pytest.approx(1.9428, abs=1e-3)


def test_wiring_classes_are_homogeneous():
    """Moi cap KE phai cho CUNG ti so; moi cap CHEO cung vay.

    Neu khong dong nhat, "ti so cua cap ke" khong phai mot dai luong -- va
    ban goc cua ham nay chi giu lai gia tri CUOI cua vong lap, tuc se giau
    mat su khong dong nhat do.
    """
    w = A.wiring_checks()
    assert w["adjacent_is_homogeneous"] and w["crossed_is_homogeneous"]
    assert w["n_adjacent_pairs"] == 4 and w["n_crossed_pairs"] == 2
    assert w["k_classes"] == [0.5, 0.7071]


def test_variance_invariance_of_the_omega_model():
    """`A077` muc 3 (i): `Var(rho_l) = sigma^2` voi MOI link va MOI `w`.

    Day la rang buoc `G23-125`. Neu he so `1/sqrt(d_l)` bi bo, test nay do.
    """
    M = np.zeros((len(A.LINKS), T7.K))
    for j, p in enumerate(T7.PATH_NAMES):
        for l in T7.PATHS[p]:
            M[A.IDX[l], j] = 1.0
    B = M / np.sqrt(M.sum(1))[:, None]
    for w in (0.0, 0.25, 0.5, 0.75, 1.0):
        var = w * (B @ B.T).diagonal() + (1.0 - w)
        assert np.allclose(var, 1.0, atol=1e-12)


def test_structured_matrix_at_omega_one_is_not_reconstructed_by_division():
    """Chan mot loi chia-cho-khong.

    Ban thao tinh ma tran o `w=1` bang `(R(w) - I)/w`. Khi `w_hat ~ 0` --
    dung dieu ta DU BAO cho testbed nay -- phep do cho `I`, tuc ti so `1.0`
    thay vi `1.7071`. `structured_matrix(1.0)` tinh TRUC TIEP.
    """
    R1 = A.structured_matrix(1.0)
    R0 = A.structured_matrix(0.0)
    assert np.allclose(R0, np.eye(len(A.LINKS)))
    v = A.margin_vector("P1", "P3")
    assert float(v @ R1 @ v) / float(v @ v) == pytest.approx(1.7071, abs=1e-3)


def test_var_margin_omega1_column_is_stable_at_omega_hat_zero():
    """`ratio_at_omega_1_analytic` KHONG duoc phu thuoc `w_hat`."""
    R = np.eye(len(A.LINKS))
    a = A.var_margin(R, 0.0)
    b = A.var_margin(R, 0.5)
    for k in a:
        assert a[k]["ratio_at_omega_1_analytic"] == pytest.approx(
            b[k]["ratio_at_omega_1_analytic"], abs=1e-12)
    assert a["m(P1,P3)"]["ratio_at_omega_1_analytic"] == pytest.approx(
        1.7071, abs=1e-3)


def test_sheppard_formula():
    for r in (0.0, 0.3, 0.6, 0.9):
        assert A.sheppard(r) == pytest.approx(np.arccos(r) / np.pi, abs=1e-12)
    assert A.sheppard(0.0) == pytest.approx(0.5)
    assert A.sheppard(1.0) == pytest.approx(0.0)


# ------------------------------------------------------------ tien ich gia
def _write_run(path, omega, rho_bar, n=599, seed=0, sigma=0.03,
               common_mode=0.0, tau=3.5):
    """Sinh mot run AR(1) voi `omega` DA BIET. `common_mode > 0` bom confound."""
    M = np.zeros((len(A.LINKS), T7.K))
    for j, p in enumerate(T7.PATH_NAMES):
        for l in T7.PATHS[p]:
            M[A.IDX[l], j] = 1.0
    B = M / np.sqrt(M.sum(1))[:, None]

    rng = np.random.default_rng(seed)
    phi = np.exp(-A.DT_MEASURED_S / tau)
    sd = np.sqrt(1.0 - phi * phi)
    f = np.zeros((n, T7.K))
    g = np.zeros((n, len(A.LINKS)))
    h = np.zeros(n)
    f[0] = rng.standard_normal(T7.K)
    g[0] = rng.standard_normal(len(A.LINKS))
    h[0] = rng.standard_normal()
    for t in range(1, n):
        f[t] = phi * f[t - 1] + sd * rng.standard_normal(T7.K)
        g[t] = phi * g[t - 1] + sd * rng.standard_normal(len(A.LINKS))
        h[t] = phi * h[t - 1] + sd * rng.standard_normal()

    eps = np.sqrt(omega) * (f @ B.T) + np.sqrt(1.0 - omega) * g
    eps = eps + common_mode * h[:, None]
    mean_load = np.mean(list(T7.LOAD_MEAN.values()))
    mu = np.array([rho_bar + T7.LOAD_MEAN[l] - mean_load for l in A.LINKS])
    rho = np.clip(mu + sigma * eps, 0.50, 1.05)

    fields = ("sample_index", "timestamp_s", "link", "rho",
              "throughput_mbps", "tx_bytes_delta", "dt_s")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields)
        wr.writeheader()
        for i in range(n):
            for j, l in enumerate(A.LINKS):
                wr.writerow({"sample_index": i,
                             "timestamp_s": "%.6f" % (i * A.DT_MEASURED_S),
                             "link": l, "rho": "%.8f" % rho[i, j],
                             "throughput_mbps": "0", "tx_bytes_delta": 0,
                             "dt_s": "%.8f" % A.DT_MEASURED_S})
    return rho


def _campaign(tmp_path, omega, common_mode=0.0):
    tmp_path.mkdir(parents=True, exist_ok=True)
    mats, cells = [], []
    s = 0
    for rb in (0.700, 0.850, 0.900, 0.925, 0.960):
        for rep in (1, 2, 3):
            s += 1
            p = tmp_path / ("rho_measured_clean_rho%.3f_rep%d.csv" % (rb, rep))
            _write_run(str(p), omega, rb, seed=9000 + s, common_mode=common_mode)
            mats.append(A.load_run(str(p)))
            cells.append(A.cell_of(str(p)))
    return mats, cells


# ------------------------------------------------------ NC-25-2 / NC-25-3
@pytest.mark.parametrize("omega", [0.00, 0.35, 0.75])
def test_NC_25_2_recovers_known_omega(tmp_path, omega):
    mats, _ = _campaign(tmp_path, omega)
    R, _ = A.pooled_corr(mats)
    est = A.omega_hat(R)
    assert est["omega_hat_corrected"] == pytest.approx(omega, abs=0.05)


def test_NC_25_3_b_hat_near_zero_without_confound(tmp_path):
    mats, _ = _campaign(tmp_path, 0.0)
    R, _ = A.pooled_corr(mats)
    assert abs(A.omega_hat(R)["b_hat_null_pairs"]) < 0.03


# --------------------------------------------------------------- PC-25-1
def test_PC_25_1_pooling_artifact_fires(tmp_path):
    """★ Gate `G23-309`. Noi cac run roi `corrcoef` PHAI cho `omega_hat >= 1`.

    Muc dich: chung minh phep do DU NHAY de phan biet hai cach tinh. Neu doi
    chung nay khong fire, moi so khac cua Lesson 23.25 mat gia tri.
    """
    mats, _ = _campaign(tmp_path, 0.0)
    R_ok, _ = A.pooled_corr(mats)
    R_bad, _ = A.pooled_corr([np.concatenate(mats, axis=0)])
    ok, bad = A.omega_hat(R_ok), A.omega_hat(R_bad)

    assert abs(ok["omega_hat_corrected"]) < 0.10        # cach DUNG: gan 0
    assert bad["omega_hat"] >= 1.00                     # cach SAI: bung
    assert bad["b_hat_null_pairs"] >= 0.50              # co bao truc tiep


# --------------------------------------------------------------- PC-25-2
def test_PC_25_2_common_mode_moves_b_hat_and_ATTENUATES_omega(tmp_path):
    """★ Bom confound chung vao ca 8 link.

    Ban thao du doan `omega_hat_corrected` GIU NGUYEN. Do la SAI. Dai so:

        eps_l = sqrt(w) F_l + sqrt(1-w) g_l + c*h    (h chung moi link)
        r_lm  = w*k_lm/(1+c^2) + c^2/(1+c^2)
        b_hat = c^2/(1+c^2)  ->  w_hat_corr = w*(1 - b_hat)

    Phep tru `b_hat` bo phan CONG THEM nhung khong bo phan LAM LOANG. Nen
    common-mode lam `omega_hat_corrected` BI THIEU, khong bi thoi phong --
    huong sai lech an toan. Ve `omega_hat_deattenuated` hoi phuc `w`.
    """
    m0, _ = _campaign(tmp_path / "a", 0.35, common_mode=0.0)
    m1, _ = _campaign(tmp_path / "b", 0.35, common_mode=0.8)
    e0 = A.omega_hat(A.pooled_corr(m0)[0])
    e1 = A.omega_hat(A.pooled_corr(m1)[0])

    assert e1["b_hat_null_pairs"] > e0["b_hat_null_pairs"] + 0.10
    # (a) huong sai lech: BI THIEU, khong bi thoi phong
    assert e1["omega_hat_corrected"] < e0["omega_hat_corrected"]
    # (b) do lon khop dai so: w_corr = w*(1 - b_hat)
    assert e1["omega_hat_corrected"] == pytest.approx(
        e0["omega_hat_corrected"] * (1.0 - e1["b_hat_null_pairs"]), abs=0.03)
    # (c) ve khu-lam-loang hoi phuc lai `w`
    assert e1["omega_hat_deattenuated"] == pytest.approx(0.35, abs=0.06)


def test_deattenuation_is_identity_without_confound(tmp_path):
    """Khong co confound thi `b_hat ~ 0` nen ve thu ba trung ve thu hai."""
    mats, _ = _campaign(tmp_path, 0.35)
    e = A.omega_hat(A.pooled_corr(mats)[0])
    assert e["omega_hat_deattenuated"] == pytest.approx(
        e["omega_hat_corrected"], abs=0.02)


# ------------------------------------------------------------- goodness
def test_M248_flags_structure_when_model_is_wrong():
    """`M-248` phai PHAN BIET duoc, khong chi 'khong bao gio bao'."""
    R_ok = A.structured_matrix(0.4)
    assert not A.goodness_of_fit(R_ok, 0.4)["_verdict_structured_residual"]

    R_bad = A.structured_matrix(0.4)
    for a, b in A.S_PAIRS:                       # bom lech theo LOP k
        bump = 0.06 if A.K_PAIR[(a, b)] > 0.6 else -0.06
        R_bad[A.IDX[a], A.IDX[b]] += bump
        R_bad[A.IDX[b], A.IDX[a]] += bump
    assert A.goodness_of_fit(R_bad, 0.4)["_verdict_structured_residual"]


# ------------------------------------------------------------- bootstrap
def test_block_length_is_capped_by_run_length(tmp_path):
    """`A077` muc 6b: block khong duoc dai qua `n_run / MIN_BLOCKS_PER_RUN`.

    Voi `tau_system = 26.74 s` va run 599 mau, `5*tau` = 669 mau > 599. Neu
    khong cap, bootstrap khong lay duoc block nao.
    """
    mats, _ = _campaign(tmp_path, 0.2)
    rng = np.random.default_rng(1)
    boot = A.block_bootstrap(mats, rng, tau_system=26.74)
    assert boot["block_was_capped_by_run_length"] is True
    assert boot["block_len_samples"] == 599 // A.MIN_BLOCKS_PER_RUN
    assert boot["ci_is_lower_bound_on_width"] is True     # 29.8s / 26.74s = 1.11
    assert boot["n_boot"] > 0


def test_block_not_capped_when_tau_is_small(tmp_path):
    mats, _ = _campaign(tmp_path, 0.2)
    rng = np.random.default_rng(1)
    boot = A.block_bootstrap(mats, rng, tau_system=3.0)
    assert boot["block_was_capped_by_run_length"] is False
    assert boot["ci_is_lower_bound_on_width"] is False


# ------------------------------------------------------------- ve sinh
def test_NC_25_1_deterministic(tmp_path):
    mats, _ = _campaign(tmp_path, 0.20)
    a1 = A.omega_hat(A.pooled_corr(mats)[0])
    a2 = A.omega_hat(A.pooled_corr(mats)[0])
    assert json.dumps(a1, sort_keys=True) == json.dumps(a2, sort_keys=True)


def test_locked_constants_are_not_flags():
    """Chong p-hacking (`A077` muc 9/11 N4)."""
    src = inspect.getsource(A.main)
    for bad in ("--tau", "--snr-flat", "--snr-strong", "--w-loss",
                "--n-boot", "--block-mult", "--mode"):
        assert bad not in src


def test_decision_thresholds_are_module_constants():
    """`G23-311` co dau ra la NGAN SACH -> nguong phai khoa trong ma nguon."""
    assert A.SNR_FLAT == 0.25 and A.SNR_STRONG == 1.00
    src = inspect.getsource(A.snr_and_forecast)
    assert "SNR_FLAT" in src and "SNR_STRONG" in src


# ------------------------------------------- Lesson 23.25c / A079 / T8
def test_G23_315_k_and_shared_host_are_collinear_in_structured_pairs():
    audit = A.collinearity_audit()
    assert audit["k_and_host_perfectly_collinear_within_structured"] is True
    assert len(audit["all_28_pairs"]) == 28
    assert audit["by_k_class"]["0.7071"]["n_shared_host"] == 8
    assert audit["by_k_class"]["0.5"]["n_shared_host"] == 0


def test_bartlett_neff_is_measured_from_both_acfs():
    rng = np.random.default_rng(7901)
    mats = []
    phi = np.array([np.exp(-A.DT_MEASURED_S / 20.0),
                    np.exp(-A.DT_MEASURED_S / 3.0)])
    innovation = np.sqrt(1.0 - phi * phi)
    for _ in range(8):
        X = np.zeros((599, 2))
        X[0] = rng.standard_normal(2)
        for i in range(1, len(X)):
            X[i] = phi * X[i - 1] + innovation * rng.standard_normal(2)
        mats.append(X)
    neff = A.neff_bartlett_empirical(mats, 0, 1)
    assert 20.0 < neff <= 8 * 599
    # Chan hoi quy ve cong thuc max(tau) cu (xap xi 24 mau cho 8 run).
    assert neff > 4.0 * (8 * 599 * A.DT_MEASURED_S / (2.0 * 20.0))


def test_PC_25c_1_joint_wls_recovers_known_half():
    neff = {pair: 300.0 for pair in A.K_PAIR}
    fit = A.fit_joint_wls(A.structured_matrix(0.5), neff)
    assert 0.45 <= fit["coef"]["omega"] <= 0.55


def test_NC_25c_2_identity_and_joint_wls_sd():
    neff = {pair: 300.0 for pair in A.K_PAIR}
    controls = A._control_checks(neff)
    nc = controls["NC_25c_2_identity"]
    assert nc["passed"] is True
    assert nc["omega_hat"] == pytest.approx(0.0, abs=1e-12)
    assert nc["relative_error_sd"] < 0.05


def test_t0_t7_canonical_block_excludes_t8():
    report = {"T0_wiring": {"x": 1}, "T2b_omega_by_cell": {"x": 2},
              "T7_null_audit": {"x": 3}, "T8_identifiability": {"x": 4},
              "provenance": {"x": 5}}
    assert A._t0_t7_block(report) == {
        "T0_wiring": {"x": 1}, "T2b_omega_by_cell": {"x": 2},
        "T7_null_audit": {"x": 3}}


def test_wls_reports_overdispersion_scaled_uncertainty():
    neff = {pair: 300.0 for pair in A.K_PAIR}
    R = A.structured_matrix(0.2)
    R[A.IDX["uA"], A.IDX["uB"]] = 0.8
    R[A.IDX["uB"], A.IDX["uA"]] = 0.8
    fit = A.fit_joint_wls(R, neff)
    assert fit["scale_factor_S"] == pytest.approx(
        np.sqrt(fit["chi2_over_dof"]))
    assert fit["sd_scaled"]["omega"] == pytest.approx(
        fit["sd"]["omega"] * fit["scale_factor_S"])
    assert abs(fit["t_scaled"]["omega"]) <= abs(fit["t"]["omega"])


def test_M3_is_algebraically_M1_without_two_dummy_points():
    neff = {pair: 100.0 + i for i, pair in enumerate(A.K_PAIR)}
    rng = np.random.default_rng(801)
    R = np.eye(len(A.LINKS))
    for a, b in A.K_PAIR:
        R[A.IDX[a], A.IDX[b]] = R[A.IDX[b], A.IDX[a]] = rng.uniform(-0.2, 0.4)
    cov = ("host_x_slow", lambda a, b: (a, b) in
           (("uA", "uB"), ("vC", "vD")))
    m3 = A.fit_joint_wls(R, neff, [cov])
    keep = [p for p in A.K_PAIR if p not in (("uA", "uB"), ("vC", "vD"))]
    drop = A.fit_joint_wls(R, neff, pairs=keep)
    assert m3["coef"]["intercept_b"] == pytest.approx(
        drop["coef"]["intercept_b"], abs=1e-12)
    assert m3["coef"]["omega"] == pytest.approx(drop["coef"]["omega"], abs=1e-12)


def test_default_branch_admissibility_rejects_negative_omega():
    with pytest.raises(AssertionError, match="ngoai"):
        A.assert_scenarios_are_exhaustive({"coef": {"omega": -0.1}})
