"""Scientific controls: alignment, common-mode contamination, certificate refusal."""
import numpy as np
import pytest
from tools.g4_nugget_model import alignment_check, analyse_series, v_model, sf_model
from tools.g4_certify import require_clean, validate_model


def test_alignment_detects_shift_and_rejects_uninformative_target():
    rng=np.random.default_rng(51)
    target=rng.normal(size=4000).cumsum()
    assert alignment_check(target+rng.normal(0,.01,len(target)),target)['aligned']
    shifted=alignment_check(np.roll(target,1),target)
    assert not shifted['aligned'] and shifted['argmin_lag']==-1
    assert not alignment_check(np.zeros(100),np.zeros(100))['aligned']


def test_conserving_uniform_frames_match_theory_and_common_noise_is_detected():
    rng=np.random.default_rng(8); caps=np.array([4e6,8e6]); dt=.1
    target=rng.normal(0,.04,(1,30000,2))
    w=rng.uniform(0,1442,(1,30001,2))
    eps=-np.diff(w,axis=1)*8/(caps*dt)
    r=analyse_series(target+eps,target,dt,caps)
    np.testing.assert_allclose(r['kappa_per_link'],2,atol=.05)
    np.testing.assert_allclose(r['acf1_per_link'],-.5,atol=.02)
    assert r['aligned'] and r['rho_eps_run_max']<.04
    common=np.repeat(eps[:,:,:1],2,axis=2)
    assert analyse_series(target+common,target,dt,caps)['rho_eps_run_max']>.99
    np.testing.assert_allclose(v_model(caps,.2),v_model(caps,.1)/4)
    assert np.all(sf_model([.03,.03],caps,.2)>sf_model([.03,.03],caps,.1))


def test_nonfinite_and_failed_model_cannot_be_certified():
    with pytest.raises(ValueError,match='nonfinite'):
        analyse_series(np.full((1,30,2),np.nan),np.ones((1,30,2)),.1,[4e6,8e6])
    with pytest.raises(ValueError,match='did not pass'):
        validate_model({'overall':'FAIL'})


def test_certificate_refuses_dirty_tree(monkeypatch):
    monkeypatch.setattr('tools.g4_certify.subprocess.check_output',lambda *a,**k:' M tools/g4_certify.py')
    with pytest.raises(RuntimeError,match='REFUSING'):
        require_clean()


def test_fixed_effect_regression_recovers_known_axis_and_bootstrap_pooling():
    from tools.g3b_orthogonality_audit import regression_intervals, bootstrap_slopes
    rng=np.random.default_rng(27)
    links=np.tile(np.arange(8),8)
    s=np.repeat([0,0,1,1,0,0,1,1],8)
    tau=np.repeat([0,0,0,0,1,1,1,1],8)
    x=np.column_stack([np.ones(64),s,tau,np.eye(8)[links,1:]])
    beta=np.array([.03,.12,-.07,.1,.2,.3,.4,.5,.6,.7])
    result=regression_intervals(x,x@beta,{'link':links,'run':np.repeat(np.arange(8),8)})
    assert result['beta_sigma']==pytest.approx(.12)
    assert result['beta_tau']==pytest.approx(-.07)
    assert result['intervals']['cluster_run']['df']==7
    values=rng.uniform(1,3,(4,2,8))
    med=bootstrap_slopes(values,np.arange(8)[None,:])
    np.testing.assert_allclose(med[:,0],np.median(values,axis=(1,2)))
