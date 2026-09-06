"""Multiplicity-aware post-hoc null check and additive certificate v2.1."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.stats import norm
from tools.artifact_guard import sha256_of,write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g4_certify import require_clean
from tools.g4_nugget_model import v_q
from tools.g2_topology import CAP_BPS, DEGREE, LINKS,a0_from_sigma_at
from tools.g5_parameters import KAPPA_NUGGET,signal_fraction

BASE=Path('results/SMOKE/phase-G2')
CERT=Path('results/LIVE/phase-G2/measurement_path_cert_v2.json')


def expected_max_abs_normal(m):
    if m<1: raise ValueError('positive family size required')
    def survival(x):
        cdf=2*norm.cdf(x)-1
        return 1. if cdf<=0 else -np.expm1(m*np.log(cdf))
    return float(quad(survival,0,12,epsabs=1e-10)[0])


def family_assessment(correlations,n_samples):
    r=np.asarray(correlations,float); n=np.asarray(n_samples,float)
    if r.shape!=n.shape or np.any(n<4) or not np.isfinite(r).all():
        raise ValueError('finite aligned correlation/sample-size vectors required')
    sd=np.sqrt(1.5/n); z=r/sd; p=2*norm.sf(abs(z)); m=len(r)
    critical=float(norm.ppf(1-.05/(2*m)))
    adjusted=np.minimum(1,p*m)
    return {'m':m,'max_abs_standardized':float(np.max(abs(z))),
            'bonferroni_critical_z':critical,'min_adjusted_p':float(adjusted.min()),
            'n_rejected_fwer05':int(np.sum(adjusted<.05)),
            'max_abs_population_corr_upper95_normal_bonferroni':float(np.max(np.minimum(1,abs(r)+critical*sd))),
            'iid_normal_expected_max_abs_z_reference_only':expected_max_abs_normal(m),
            'verdict':'NO_EVIDENCE_AGAINST_NULL_AT_FWER_0.05' if adjusted.min()>=.05 else 'NULL_INCONSISTENCY_DETECTED',
            'per_comparison_z':z.tolist(),'per_comparison_p':p.tolist(),
            'per_comparison_p_bonferroni':adjusted.tolist()}


def main():
    out=BASE/'g5_rho_eps_null.json'; newcert=CERT.with_name('measurement_path_cert_v2_1.json')
    doc=Path('docs/phase-G/68a-null-consistency-and-forward-proxy.md')
    for path in (out,newcert,doc):
        if path.exists(): raise FileExistsError(path)
    require_clean()
    modelpath=BASE/'g4_nugget_model.json'; model=json.loads(modelpath.read_text())
    cert=json.loads(CERT.read_text())
    assert sha256_of(modelpath)==cert['evidence_sha256'][str(modelpath)]
    r_all=[]; n_all=[]; labels=[]; rp=[]; npool=[]; cell_rows=[]
    em28=expected_max_abs_normal(28)
    for row in model['cells']:
        nt=row['n_win']*row['n_rep']; sd=np.sqrt(1.5/nt)
        rp.extend(row['rho_eps_pairs']);npool.extend([nt]*28)
        for run in row['replicates']:
            r_all.extend(run['rho_eps_pairs']);n_all.extend([row['n_win']]*28)
            labels.extend([{'cell':row['cell'],'replicate':run['replicate'],'pair':p} for p in row['pair_labels']])
        cell_rows.append({'cell':row['cell'],'n_total':nt,'sd_null':float(sd),
                          'max_observed':row['rho_eps_max'],'max_in_sd_units':float(row['rho_eps_max']/sd),
                          'expected_max_28_iid_normal_reference':float(em28*sd),
                          'below_expected_max_reference':bool(row['rho_eps_max']<=em28*sd)})
    runs=family_assessment(r_all,n_all); pooled=family_assessment(rp,npool)
    ratio=a0_from_sigma_at('uA',1)*np.sqrt(DEGREE)/CAP_BPS
    factor=float(np.sqrt(KAPPA_NUGGET*.8264/(1-.8264)))
    boundaries=[]
    for dt in (.1,.15,.2,.25):
        q=np.sqrt(v_q(CAP_BPS,dt))
        boundaries.append({'dt':dt,'old_per_link':(4.36*q).tolist(),'new_per_link':(factor*q).tolist(),
                           'old_sigma_ref_min':float(np.max(4.36*q/ratio)),
                           'new_sigma_ref_min':float(np.max(factor*q/ratio)),
                           'status':'FORWARD_MODEL_PROXY_NOT_NEW_NETWORK_VALIDATION'})
    kappas={d:[float(np.median(r['kappa_per_link'])) for row in model['cells'] if row['dataset']==d for r in row['replicates']] for d in ('G3b','G2')}
    sf_changes=[]
    for row in model['cells']:
        if row['dataset']=='G3b':
            for d in ('G3b','G2'):
                empirical=model['summary'][d]['kappa_median']
                pred=signal_fraction(row['sigma_target_per_link'],CAP_BPS,row['dt_s'],empirical)
                sf_changes.extend(pred-np.array(row['sf_predicted']))
    payload={'schema':'dt4n.phase_g2.rho_eps_null.v1','status':'POST_HOC_NORMAL_APPROXIMATION',
             'provenance':provenance(),'source_sha256':{str(modelpath):sha256_of(modelpath),str(CERT):sha256_of(CERT)},
             'null_model':'independent MA1 residuals with ACF1=-.5; Bartlett Var(r) approximately 1.5/n',
             'individual_run_family':runs,'pooled_cell_family':pooled,'individual_comparison_labels':labels,
             'cells':cell_rows,'q1_forward_proxy':{'kappa_nugget':2.,'sf_floor':.8264,'factor':factor,'boundaries':boundaries},
             'kappa_run_medians':kappas,'max_abs_sf_change_empirical_vs_theory':float(np.max(abs(np.array(sf_changes)))),
             'limitations':['normal/Bartlett approximation, not an exact finite-sample test',
                'pair dependencies handled by Bonferroni; no independence claim from nonrejection',
                'max/SD still grows with family size; compare adjusted p or family-specific quantile',
                'G4 G3b and G2 inputs both have omega=0',
                'no inference that all mechanism, burst, timing or infrastructure risks are closed']}
    write_contract_artifact(out,payload)
    updated=copy.deepcopy(cert)
    updated.update(schema='dt4n.phase_g2.measurement_path_cert.v2.1',parent_certificate={'path':str(CERT),'sha256':sha256_of(CERT)},
                   parent_provenance=cert['provenance'],provenance=provenance())
    updated['certifies']['kappa_nugget']=updated['certifies']['kappa']
    updated['rho_eps_null_consistency']={'null_model':payload['null_model'],
        'sd_under_h0_per_run_n4100':float(np.sqrt(1.5/4100)),
        'max_standardized_over_heterogeneous_run_lengths':runs['max_abs_standardized'],
        'family_size':runs['m'],'min_bonferroni_p':runs['min_adjusted_p'],
        'verdict':runs['verdict'],'source':{'path':str(out),'sha256':sha256_of(out)},
        'note':'nonrejection is not proof of independence; both raw max and standardized max depend on family size'}
    updated['does_not_certify'].append('cross-campaign comparability of raw max or max/SD without family-size correction')
    updated['evidence_sha256'][str(out)]=sha256_of(out)
    updated['evidence_sha256']['tools/g5_null_addendum.py']=sha256_of(__file__)
    write_contract_artifact(newcert,updated)
    text=['# G4 — phụ lục null và proxy cho thiết kế tương lai','',
          'Giữ nguyên certificate v2 và mọi kết quả đã ký. Bản v2.1 bổ sung kiểm tra null hậu nghiệm, không đổi hệ số nugget hoặc phạm vi vật lý.',
          '', '| Ô | n gộp | SD dưới null | max quan sát | max/SD | E[max] tham khảo, 28 chuẩn độc lập |',
          '|---|---:|---:|---:|---:|---:|']
    for r in cell_rows:
        text.append(f"| {r['cell']} | {r['n_total']} | {r['sd_null']:.6f} | {r['max_observed']:.6f} | {r['max_in_sd_units']:.3f} | {r['expected_max_28_iid_normal_reference']:.6f} |")
    text+=['',f"364 phép so sánh từng lượt: max|z|={runs['max_abs_standardized']:.5f}, cận Bonferroni .05={runs['bonferroni_critical_z']:.5f}, min p hiệu chỉnh={runs['min_adjusted_p']:.5f}; {runs['verdict']}.",
           f"168 phép so sánh gộp: min p hiệu chỉnh={pooled['min_adjusted_p']:.5f}; {pooled['verdict']}.",
           'Var(r)≈(1+2*.5²)/n là xấp xỉ Bartlett cho hai MA1 độc lập. Bonferroni không cần độc lập giữa các cặp, nhưng p-value vẫn dựa trên xấp xỉ chuẩn.',
           '', '**Sửa nhận xét được cung cấp:** E[max] không phải ngưỡng kiểm định; một số ô vượt E[max] và điều đó có thể hoàn toàn bình thường. max/SD cũng tăng theo số phép thử. Các lượt có n khác nhau phải chuẩn hóa riêng, không chia tất cả cho SD tại n=4100.',
           'Không bác bỏ null không chứng minh rho_eps=0. NC-3 trong G5 cũng không tách riêng một nguyên nhân phụ thuộc.',
           '', '## Kappa và giới hạn G-L108','',
           f"Kappa G3b={model['summary']['G3b']['kappa_median']:.6f}; G2={model['summary']['G2']['kappa_median']:.6f}. IQR trên các link/ô không phải SE trên các lượt độc lập. Chưa khẳng định chênh lệch là hệ thống ở mức 4.9 SE từ phép tính trong nhận xét.",
           f"G-L108: mô hình gần κ_nugget=2, lệch mô tả khoảng 1% theo bộ dữ liệu. Thay hệ số bằng trung vị thực nghiệm làm sf đổi tối đa {payload['max_abs_sf_change_empirical_vs_theory']:.7f} ở các ô kiểm; không hiệu chỉnh mô hình. Vi phân đúng là d(sf)=-sf*(1-sf)*dκ/κ, không bỏ thừa số sf.",
           '', '## Proxy Q-1 cho thiết kế tương lai','',
           f"Hệ số mới sqrt(2*.8264/(1-.8264))={factor:.9f}; giữ sai số claim C=.10. Đây là thay thế proxy sf=.95 bằng sf=.8264 đã dùng, không hồi tố và không chứng nhận vận hành sigma thấp chưa đo.",
           '| dt | sigma_ref min cũ | sigma_ref min mô hình mới |','|---:|---:|---:|']
    for r in boundaries:text.append(f"| {r['dt']} | {r['old_sigma_ref_min']:.7f} | {r['new_sigma_ref_min']:.7f} |")
    text+=['','Vẫn phải xét clipping, T/tau, dt/tau, hiệu quả mẫu, timing, burst và hạ tầng. Việc raw max=.05867<.10 chỉ làm proxy pair-bias dùng raw max không binding; không chứng minh mọi bias omega hoặc mọi cấu hình đều đạt.',
           'G4 chỉ kiểm omega=0 trong cả hai bộ dữ liệu. Sai số phục hồi omega .0271 của G3a không phải giới hạn thay đổi coverage.',
           '',f'[Certificate v2.1](../../{newcert}) — SHA256 `{sha256_of(newcert)}`',
           f'[JSON đầy đủ](../../{out}) — SHA256 `{sha256_of(out)}`']
    with doc.open('x') as f:f.write('\n'.join(text)+'\n')
    print(json.dumps({'individual_run_family':{k:v for k,v in runs.items() if not k.startswith('per_')},
                     'pooled_cell_family':{k:v for k,v in pooled.items() if not k.startswith('per_')},
                     'q1_factor':factor,'max_sf_change':payload['max_abs_sf_change_empirical_vs_theory']},indent=2))
    print(newcert);print(doc)


if __name__=='__main__':main()
