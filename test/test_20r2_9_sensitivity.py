"""Controls that distinguish numerical/model mistakes from observed sensitivity."""
import importlib
import math
import numpy as np
import pandas as pd
import pytest
S1=importlib.import_module('tools.20r2_9_omega_sensitivity')
S3=importlib.import_module('tools.20r2_9_axis_marginal')

@pytest.mark.parametrize('r',[0.,.2,.8,.99,1.])
def test_gaussian_zero_mean_reduces_to_sheppard(r):
    assert S1.err_bivariate(0,r)==pytest.approx(math.acos(r)/math.pi,abs=2e-14)

def test_independent_gaussians_and_threshold_boundary():
    from scipy.special import ndtr
    assert S1.err_bivariate(2,0)==pytest.approx(2*ndtr(-2)*ndtr(2),abs=2e-14)
    star=S1.threshold(.88,1.7071067811865475)
    assert S1.classify(star,star,1.25)=='UNREADABLE'
    assert S1.classify(star*.8,star,1.1)=='NOT_SENSITIVE'
    assert S1.classify(star*1.2,star,1.4)=='SENSITIVE'
    assert S1.classify(star*1.2,star,1.4,False)=='UNREADABLE'

def test_axis_integration_jensen_and_algebraic_controls():
    linear=S3.integrate([0.,1.],[.5,.5],[0.,.5,1.],[0.,.5,1.])
    convex=S3.integrate([0.,1.],[.5,.5],[0.,.5,1.],[0.,.25,1.])
    assert linear['jensen_gap']==0 and convex['jensen_gap']>0
    assert S3.decompose(linear,convex)['identity_error']==0

def test_out_of_domain_mass_is_counted_without_extrapolation():
    r=S3.integrate([0.,2.],[.995,.005],[0.,1.],[.2,.3])
    assert r['E_err'] is None and r['status']=='PARTIAL_BOUNDED'
    assert r['mass_outside']==.005 and r['E_err_bounds']==[.199,.20400000000000001]
    r=S3.integrate([0.,2.],[.98,.02],[0.,1.],[.2,.3])
    assert r['status']=='UNREADABLE'

def test_common_z_mutation_cannot_be_hidden_by_seed_averaging():
    rows=[dict(mode='h2',rho_bar=.7,tau_rho=3.,seed=s,z_s=.1,err_total=.2,branch=b)
          for s in (101,102) for b in ('main','control_legacy')]
    d=pd.DataFrame(rows);assert S3.join_curves(d)[1]['max_abs_diff']==0
    d.loc[1,'err_total']+=.01;d.loc[3,'err_total']-=.01
    with pytest.raises(AssertionError,match='raw values differ'):S3.join_curves(d)
