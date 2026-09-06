"""Post-hoc uncertainty addendum. Never changes G3b signed gates."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.stats import norm, t
from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g1_estimator_bias_sim import provenance
from tools.g4_nugget_model import BASE


def regression_intervals(x,y,groups):
    """OLS, HC3, and CR1 sensitivity. CR1 uses finite-cluster t quantiles."""
    x,y=np.asarray(x,float),np.asarray(y,float)
    n,k=x.shape
    beta=np.linalg.lstsq(x,y,rcond=None)[0]
    bread=np.linalg.inv(x.T@x)
    residual=y-x@beta
    leverage=np.sum((x@bread)*x,axis=1)
    covariance={'ols':(bread*float(residual@residual)/(n-k),n-k)}
    scores=x*(residual/(1-leverage))[:,None]
    covariance['hc3']=(bread@(scores.T@scores)@bread,n-k)
    for name,g in groups.items():
        g=np.asarray(g); unique=np.unique(g); m=len(unique)
        scores=np.array([x[g==v].T@residual[g==v] for v in unique])
        cov=bread@(scores.T@scores)@bread*m/(m-1)*(n-1)/(n-k)
        covariance['cluster_'+name]=(cov,m-1)
    intervals={}
    for name,(cov,df) in covariance.items():
        se=float(np.sqrt(max(cov[1,1],0)))
        lo,hi=beta[1]+np.array([-1,1])*float(t.ppf(.975,df))*se
        log_bound=float(max(abs(lo),abs(hi))*np.log(.045/.028))
        intervals[name]={'se':se,'df':df,'ci95':[float(lo),float(hi)],
                         'log_drift_upper':log_bound,'relative_drift_upper':float(np.expm1(log_bound))}
    return {'beta_sigma':float(beta[1]),'beta_tau':float(beta[2]),
            'n':n,'rank':int(np.linalg.matrix_rank(x)),'intervals':intervals}


def bootstrap_slopes(values,indices):
    # values: cell x replicate x link. Resample whole link identities jointly.
    med=np.median(values[:,:,indices],axis=(1,3))
    if not np.all(med>0): raise ValueError('positive estimates required')
    return med


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--model',type=Path,default=BASE/'g4_nugget_model.json')
    ap.add_argument('--out',type=Path,default=BASE/'g3b_orthogonality_audit.json')
    ap.add_argument('--doc',type=Path,default=Path('docs/phase-G/66a-g3b-uncertainty-addendum.md'))
    args=ap.parse_args()
    for path in (args.out,args.doc):
        if path.exists(): raise FileExistsError(path)
    model=json.loads(args.model.read_text())
    allrows=model['g3b_estimates']; rows=[r for r in allrows if r['tau_s']<=5]
    assert len(rows)==64
    links=np.array([r['link_index'] for r in rows])
    runs=np.array([f"{r['tau_s']}_{r['sigma_ref']}_{r['replicate']}" for r in rows])
    x=np.column_stack([np.ones(64),np.log([r['sigma_ref']/.028 for r in rows]),
                       np.log([r['tau_s']/2 for r in rows]),np.eye(8)[links,1:]])
    y=np.log([r['tau_hat_s']/r['tau_s'] for r in rows])
    regression=regression_intervals(x,y,{'link':links,'run':runs})
    rng=np.random.default_rng(20260906); indices=rng.integers(0,8,(20000,8))
    cube_tau=np.array([r['tau_hat_s'] for r in rows]).reshape(4,2,8)
    cube_sig=np.array([r['sigma_ratio'] for r in rows]).reshape(4,2,8)
    med_tau=bootstrap_slopes(cube_tau,indices); med_sig=bootstrap_slopes(cube_sig,indices)
    b1=(np.log(med_tau[1]/med_tau[0])+np.log(med_tau[3]/med_tau[2]))/(2*np.log(.045/.028))
    b2=(np.log(med_sig[2]/med_sig[0])+np.log(med_sig[3]/med_sig[1]))/(2*np.log(5/2))
    bootstrap={}
    for name,b,gate in [('RT-O1',b1,.10),('RT-O2',b2,.05)]:
        sd=float(np.std(b,ddof=1))
        bootstrap[name]={'ci95':np.percentile(b,[2.5,97.5]).tolist(),'sd':sd,
                         'normal_p_pass_at_zero':float(norm.cdf(gate/sd)-norm.cdf(-gate/sd)),
                         'normal_p_pass_at_slope_point2':float(norm.cdf((gate-.2)/sd)-norm.cdf((-gate-.2)/sd))}
    outlier=next(r for r in allrows if r['tau_s']==5 and r['sigma_ref']==.045 and r['replicate']==0 and r['link']=='vC')
    spread=np.array([r['tau_hat_s']/r['tau_s']-1 for r in allrows])
    per_cell_ci=[]
    for i,(tau,sigma) in enumerate(((2,.028),(2,.045),(5,.028),(5,.045))):
        per_cell_ci.append({'tau':tau,'sigma_ref':sigma,'sigma_ratio_bootstrap_ci95':np.percentile(med_sig[i],[2.5,97.5]).tolist()})
    payload={'schema':'dt4n.phase_g2.g3b_orthogonality_audit.v1','status':'POST_HOC_DIAGNOSTIC_NO_REGATING',
             'source':str(args.model),'source_sha256':sha256_of(args.model),'provenance':provenance(),
             'regression':regression,'bootstrap':bootstrap,'bootstrap_seed':20260906,'bootstrap_draws':20000,
             'bootstrap_unit':'8 link identities jointly over all 4 cells, both replicates retained',
             'outlier':outlier,'per_link_tau_error_range':[float(spread.min()),float(spread.max())],
             'sigma_cell_intervals':per_cell_ci,
             'external_review_arithmetic':{'p_pass_zero_if_sd_point11':float(norm.cdf(.1/.11)-norm.cdf(-.1/.11)),
                                         'p_pass_slope_point2_if_sd_point11':float(norm.cdf(-.1/.11)-norm.cdf(-.3/.11))}}
    write_contract_artifact(args.out,payload)
    text=['# G3b — phụ lục bất định và G-L107','','Phân tích hậu nghiệm; doc 66 và toàn bộ phán quyết đã ký giữ nguyên.',
          '64 ước lượng ở lưới 2×2 được tính lại từ NPZ bởi g4_nugget_model; đối chiếu JSON ở rtol=atol=1e-12.',
          '', '## Hồi quy có hiệu ứng cố định theo link','',
          'log(tau_hat/tau) = intercept + beta_sigma*log(sigma_ref/.028) + beta_tau*log(tau/2) + 7 dummy link.',
          f"beta_sigma = {regression['beta_sigma']:.7f}; n=64, rank={regression['rank']}.",'',
          '| Phương pháp CI95 | Cận dưới | Cận trên | Cận độ trôi log | Cận thay đổi exp(bound)−1 |',
          '|---|---:|---:|---:|---:|']
    for name,r in regression['intervals'].items():
        text.append(f"| {name} | {r['ci95'][0]:.6f} | {r['ci95'][1]:.6f} | {r['log_drift_upper']:.3%} | {r['relative_drift_upper']:.3%} |")
    text+=['','OLS giả định sai số độc lập, đồng phương sai; HC3 cho phép phương sai khác nhau. CR1 theo link hoặc lượt là kiểm tra độ nhạy với phụ thuộc trong nhóm, dùng t(7). Chỉ có 8 nhóm nên các CI này là xấp xỉ; fixed effects không tự loại bỏ phụ thuộc. Không chọn CI hẹp nhất làm kết luận chắc chắn.',
           'Các cận độ trôi là cho hiệu ứng trung bình trong mô hình log tuyến tính trên dải đã quét, không chặn mọi link hoặc mọi đường cong phi tuyến.',
           '', 'Tham khảo công thức CR1 và hiệu chỉnh mẫu nhỏ: [statsmodels](https://www.statsmodels.org/v0.13.5/generated/statsmodels.stats.sandwich_covariance.cov_cluster.html); lượng vị t: [SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.t.html).',
           '', '## Bootstrap đúng thống kê đã ký','',
           '20000 lần, seed 20260906, resample 8 link cùng danh tính qua bốn ô; giữ cả hai lượt mỗi link. Đây là bootstrap theo link, có điều kiện trên các lượt đã có, không chứng minh độc lập giữa các link qua kernel dùng chung.',
           '| Thống kê | CI95 percentile | SD | P(pass khi slope=0), xấp xỉ chuẩn |',
           '|---|---|---:|---:|']
    for name,r in bootstrap.items():
        text.append(f"| {name} | [{r['ci95'][0]:.5f}, {r['ci95'][1]:.5f}] | {r['sd']:.5f} | {r['normal_p_pass_at_zero']:.3f} |")
    text+=['', '**G-L107:** PASS của ước lượng điểm không thiết lập tương đương trong biên đã ký. Gate độ dốc cần kèm CI và tính trước xác suất PASS dưới mô hình đúng. Độ trôi trên dải đo liên hệ với ngân sách claim, nhưng chuyển sang đại lượng đó sau khi xem dữ liệu là phân tích bổ sung, không phải gate tiền đăng ký mới.',
           '', '## Các điểm cần sửa trong nhận xét được cung cấp','',
           '- Code G3b lấy trung vị gộp 16 giá trị link/lượt, không phải trung vị-của-trung-vị. Phụ lục bootstrap đúng code đã ký.',
           '- Nếu SD=.11, P(|N(0,.11)|<=.1)=%.4f; với slope thật .20, xác suất là %.4f, không phải ~50%%.' % (payload['external_review_arithmetic']['p_pass_zero_if_sd_point11'],payload['external_review_arithmetic']['p_pass_slope_point2_if_sd_point11']),
           '- 4.8e-5 là khoảng 48 ppm, không phải 5 ppm.',
           '- Khoảng [0.948,0.993] không chứa tỉ số 1; việc hai CI chồng nhau không phải kiểm định hiệu giữa hai ô. Không thể kết luận bác bỏ clipping chỉ từ thứ hạng vài link.',
           '- Cận 0.0732 trên thang log tương ứng exp(0.0732)-1 khoảng 7.59%, không phải cận chính xác 7.32%.',
           '', f"Outlier giữ nguyên: tau=5, sigma=.045, rep=0, vC: sf={outlier['sf']:.9f}, v gián tiếp={outlier['v_indirect']:.9g}. Hệ số chặn gần 1 là dấu hiệu bất ổn ngoại suy; riêng con số này chưa chứng minh cơ chế bão hòa vật lý hay clipping của code.",
           f"Sai số tau từng link/lượt quan sát được: [{spread.min():+.2%}, {spread.max():+.2%}]. Gate trung vị không bảo đảm từng link đáp ứng claim B.",
           '', '## Bằng chứng','',f'- [JSON phân tích](../../{args.out})',f'- SHA256 JSON: `{sha256_of(args.out)}`',f'- SHA256 model nguồn: `{sha256_of(args.model)}`']
    with args.doc.open('x') as f: f.write('\n'.join(text)+'\n')
    print(json.dumps({'regression':regression,'bootstrap':bootstrap,'outlier':outlier},indent=2))
    print(args.out); print(args.doc)


if __name__=='__main__': main()
