"""Controls for the input generator; Phase22's score implementation stays locked."""
import numpy as np
import pytest
from tools.g2_topology import CAP_BPS, INCIDENCE, design_covariance
from tools.g5_estimand_transfer import A0, covariance_factor, measured_errors, make_inputs, adjudicate
from tools.g5_parameters import nugget_variance


def test_covariance_factor_matches_topology_including_singular_endpoint():
    for w in (0,.25,.5,.75,1):
        f=covariance_factor(w)
        np.testing.assert_allclose(f@f.T,design_covariance(A0,w),rtol=1e-12,atol=1e-15)
    assert INCIDENCE.shape==(8,4)


def test_null_pair_is_identical_across_omega_and_only_inputs_change():
    reference=make_inputs(0,3,1,null_pair=True,n=1000)
    for w in (.25,.5,.75,1):
        for got,want in zip(make_inputs(w,3,1,null_pair=True,n=1000),reference):
            np.testing.assert_array_equal(got,want)
    other=make_inputs(0,3,0,null_pair=True,n=1000)
    assert not np.array_equal(reference[0],other[0])


def test_stationary_generator_covariance_and_ma1_lag_one():
    dt=tau=.1; omega=.5
    values=measured_errors(omega,120000,dt,np.random.default_rng(719),tau=tau)
    cov=design_covariance(A0,omega); v=nugget_variance(CAP_BPS,dt)
    np.testing.assert_allclose(np.cov(values.T),cov+np.diag(v),atol=1.6e-5,rtol=.03)
    centered=values-values.mean(axis=0)
    lag=centered[:-1].T@centered[1:]/(len(values)-1)
    np.testing.assert_allclose(lag,np.exp(-dt/tau)*cov-.5*np.diag(v),atol=1.6e-5,rtol=.04)


def test_diagnostic_pass_cannot_retire_time_ratio_if_runtime_transfer_fails():
    passed={'amplitude':.05,'snr':4.,'worst_step':.001,'marginal_drift':.001}
    null={'uncorrected':dict(passed,amplitude=0)}
    primary={'uncorrected':passed,'maxscore':dict(passed,amplitude=.001)}
    result=adjudicate(primary,null)
    assert result['diagnostic_verdict']=='ADOPT_DIAGNOSTIC'
    assert result['overall']=='TRANSFER_FAILS_RUNTIME'
    assert not result['retire_kappa_time']
    primary['uncorrected']=dict(passed,amplitude=.001)
    assert adjudicate(primary,null)['overall']=='TRANSFER_FAILS'


def test_null_family_adjusts_for_multiplicity_and_heterogeneous_n():
    from tools.g5_null_addendum import expected_max_abs_normal,family_assessment
    assert expected_max_abs_normal(1)==pytest.approx(np.sqrt(2/np.pi))
    assert expected_max_abs_normal(364)>expected_max_abs_normal(28)
    r=family_assessment([.03,.03],[4100,61500])
    assert r['per_comparison_z'][1]>r['per_comparison_z'][0]
    assert r['m']==2
    assert r['per_comparison_p_bonferroni'][0]>=r['per_comparison_p'][0]
