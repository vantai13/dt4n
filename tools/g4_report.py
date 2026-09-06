"""Export G4 tables, figure, Vietnamese report and a checksum inventory."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np
from tools.artifact_guard import sha256_of, write_contract_artifact
from tools.g4_nugget_model import BASE


def main():
    cert_path=Path('results/LIVE/phase-G2/measurement_path_cert_v2.json')
    cert=json.loads(cert_path.read_text())
    model=json.loads((BASE/'g4_nugget_model.json').read_text())
    audit=json.loads((BASE/'g3b_orthogonality_audit.json').read_text())
    custody_path=BASE/'g4_data_manifest.json'
    custody=json.loads(custody_path.read_text())
    outputs=[BASE/'g4_nugget_summary.csv',BASE/'g4_nugget_per_link_run.csv',
             BASE/'g4_nugget_model.png',Path('docs/phase-G/68-measurement-path-cert-v2.md'),
             BASE/'g4_artifact_manifest.json']
    for path in outputs:
        if path.exists(): raise FileExistsError(path)
    summary=[]; detailed=[]
    for r in model['cells']:
        summary.append({k:r[k] for k in ('dataset','cell','n_rep','n_win','dt_s','kappa_median',
                       'acf1_median','rho_eps_max','rho_eps_run_max','aligned')})
        for rep in r['replicates']:
            for i,link in enumerate(cert['certifies']['links']):
                detailed.append({'dataset':r['dataset'],'cell':r['cell'],'replicate':rep['replicate'],
                    'link':link,'cap_bps':r['cap_bps'][i],'dt_s':r['dt_s'],
                    'v_q':r['v_q_per_link'][i],'v_theory':2*r['v_q_per_link'][i],
                    'v_direct':rep['v_direct_per_link'][i],'kappa':rep['kappa_per_link'][i],
                    'acf1':rep['acf_lags_1_to_8'][i][0],
                    'alignment_argmin':rep['alignment_per_link'][i]['argmin_lag'],
                    'aligned':rep['alignment_per_link'][i]['aligned']})
    for path,rows in zip(outputs[:2],(summary,detailed)):
        with path.open('x',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(13,4),constrained_layout=True)
    labels=[r['cell'] for r in model['cells']]
    for i,r in enumerate(model['cells']):
        axes[0].scatter(np.full(8,i),r['kappa_per_link'],s=24)
        axes[1].scatter(np.full(8,i),r['acf1_per_link'],s=24)
    axes[0].axhspan(1.5,2.5,color='#e1f2e7'); axes[0].axhline(2,color='black',ls='--')
    axes[0].set_title('Direct kappa; fixed theory = 2')
    axes[1].axhspan(-.55,-.45,color='#e1f2e7'); axes[1].axhline(-.5,color='black',ls='--')
    axes[1].set_title('Residual ACF at lag 1')
    axes[2].scatter(range(6),[r['rho_eps_max'] for r in model['cells']],label='Pooled by cell')
    axes[2].scatter(range(6),[r['rho_eps_run_max'] for r in model['cells']],marker='x',label='Worst individual run')
    axes[2].axhline(.15,color='#bc3333',ls='--',label='B-2 limit .15')
    axes[2].set_ylim(0,.17); axes[2].set_title('Maximum absolute residual correlation'); axes[2].legend(fontsize=8)
    for ax in axes:
        ax.set_xticks(range(6),labels,rotation=40,ha='right',fontsize=8)
    fig.suptitle('G4: stored kernel-network measurements — PASS; no new network run')
    fig.savefig(outputs[2],dpi=160); plt.close(fig)
    g=model['summary']['G3b']; k=model['summary']['G2']
    ad=cert['certifies']['links'].index('ad')
    sigmin=[cert['lookup_table'][d]['sigma_min_claim_c_proxy'][ad] for d in ('0.1','0.2')]
    lines=['# G′.4 — Chứng nhận đường đo v2','', '**Phán quyết: GO / certificate PASS trong phạm vi ghi rõ bên dưới.**',
           'Tái phân tích 5 ô G3b (9 lượt, 72 chuỗi link/lượt) và đối chứng G2 run 3 (4 lượt, 32 chuỗi). Không chạy mạng mới.',
           'Prereg phương pháp tái phân tích: [doc 67](67-prereg-g4-nugget-model.md), tag `phase-G2-g4-prereg`. Dữ liệu và nhận xét trước đó đã được biết; đây không phải tiền đăng ký trước khi thu thập.',
           '', '## 1. Kết quả mô hình','',
           '| Ô | κ trực tiếp, trung vị 8 link | ACF1 | max |ρ_eps| gộp | max từng lượt | Căn chỉnh |',
           '|---|---:|---:|---:|---:|---|']
    # Escape absolute-value notation inside Markdown table headers.
    lines[-2]='| Ô | κ trực tiếp, trung vị 8 link | ACF1 | max abs(ρ_eps) gộp | max từng lượt | Căn chỉnh |'
    for r in model['cells']:
        lines.append(f"| {r['cell']} | {r['kappa_median']:.6f} | {r['acf1_median']:.6f} | {r['rho_eps_max']:.6f} | {r['rho_eps_run_max']:.6f} | {'PASS' if r['aligned'] else 'FAIL'} |")
    lines+=['',f"G3b: κ trực tiếp={g['kappa_median']:.6f}, IQR={g['kappa_iqr']}; gián tiếp qua intercept sf={model['indirect_kappa_median']:.6f}. Sai khác trực tiếp so với lý thuyết 2 là {(g['kappa_median']/2-1):+.3%}.",
            f"G2: κ={k['kappa_median']:.6f}. Cả 104 chuỗi có cực tiểu Var(measured−target_shifted) tại lag 0. 28 cặp nhiễu được lưu cho từng lượt và từng ô.",
            f"sf dự đoán bằng κ=2 so với 40 trung vị link/ô: RMS={model['sf_self_test']['rms']:.8f}; max sai lệch={model['sf_self_test']['max_abs']:.8f}.",
            '', '## 2. Gate và dự đoán','', '| Gate | Điều kiện | Kết quả |','|---|---|---|']
    thresholds=['mọi link/lượt aligned ở lag 0','mọi thống kê hữu hạn','max abs(rho_eps) gộp và từng lượt <= .15',
                'median κ trong [1.5,2.5] ở mỗi bộ G3b/G2','median ACF1 cách −.5 không quá .05 ở mỗi bộ','sf RMS <= .02 (κ=2 cố định)']
    for (name,value),threshold in zip(model['gates'].items(),thresholds):
        lines.append(f"| {name} | {threshold} | {'PASS' if value else 'FAIL'} |")
    lines+=['','Dự đoán max nhiễu <=.05 đúng với thống kê gộp, nhưng không đúng với cực đại từng lượt (.05867 ở G2). Gate .15 vẫn PASS. Không đổi ngưỡng. M-6 là ngưỡng sf có trong hướng dẫn và đã được đưa vào prereg trước khi chạy.',
            'ACF1 gần −.5 và κ gần 2 phù hợp mô hình; không chứng minh cơ chế này là nguyên nhân duy nhất hoặc không có phần dư khác.',
            '', '![Kết quả mô hình](../../results/SMOKE/phase-G2/g4_nugget_model.png)',
            '', '## 3. Hợp đồng được phát hành','',
            f'- [measurement_path_cert_v2.json](../../{cert_path})',
            f'- SHA256: `{sha256_of(cert_path)}`',
            f"- Sinh từ commit `{cert['provenance']['git_head_at_execution']}`, worktree_dirty_at_execution=`{cert['provenance']['worktree_dirty_at_execution']}`.",
            '- Hệ số chứng nhận κ=2 là dự đoán cố định, không thay bằng κ fit sau khi xem dữ liệu.',
            '- Công thức: `v(C,dt,L) = (8*L/(C*dt))²/6`, L=1442 byte.',
            '- Self-test đọc 40 giá trị sf thực tế và được thực thi; SHA256 model, nguồn, code và test có trong cert.',
            '', '## 4. Phạm vi và giới hạn','',
            'PASS có điều kiện cho kernel veth/HTB trên host đã đo, dt=.1 s và các dung lượng link có trong NPZ. Giả định remainder đồng đều và độc lập là điều kiện của công thức, không phải hệ quả tất yếu của bảo toàn byte.',
            'Các bảng dt=.05,.15,.2,.25,.5,1,1.5 là dự đoán mô hình chưa được đo xác nhận. Đổi dt/C có thể thay đổi tương quan giữa remainder; max rho_eps đã thấy không phải cận tin cậy tổng thể và không tự chuyển sang cấu hình mới.',
            'Không chứng nhận NIC vật lý/Internet, estimator tau, omega>0, toàn bộ miền điều khiển hay mọi cấu hình telemetry. sf floor là proxy giữ từ protocol; sigma đã hiệu chỉnh cần đánh giá riêng. Bias từng cặp chưa phải bias của estimator omega tổng hợp.',
            f"Ví dụ link ad (4 Mbps): sigma_min theo proxy sf=.8264 tại dt=.1 là {sigmin[0]:.8f}; dự đoán tại dt=.2 là {sigmin[1]:.8f}, giảm đúng một nửa. Đây chỉ là ràng buộc sf; vẫn phải xét Q-1, clipping và các điều kiện khác.",
            'Lưới phân rã telemetry cũ được bỏ trong phạm vi bài này vì dữ liệu residual sẵn có đủ kiểm giả thuyết trực tiếp; không suy ra mọi telemetry đều tương đương.',
            '', '## 5. Phụ lục G3b và sửa code mẫu','',
            '- [Doc 66a — G-L107 và hồi quy](66a-g3b-uncertainty-addendum.md). Doc 66 cũ và gate giữ nguyên.',
            f"- Hồi quy beta_sigma={audit['regression']['beta_sigma']:.7f}; CI95 OLS={audit['regression']['intervals']['ols']['ci95']}; cận thay đổi thực tế {audit['regression']['intervals']['ols']['relative_drift_upper']:.2%}. Gom sai số theo link cho cận {audit['regression']['intervals']['cluster_link']['relative_drift_upper']:.2%}, chỉ xấp xỉ với 8 nhóm.",
            '- Sửa alignment để dịch target so với measured trên cùng độ dài, kiểm đủ link/lượt; code mẫu chỉ cắt chuỗi eps và không kiểm được căn chỉnh.',
            '- Dùng metadata NPZ, allow_pickle=False, kiểm SHA256; lưu cả 28 cặp, ACF1..8, từng replicate và các phía lag.',
            '- Cert từ worktree sạch, không allow-dirty; không ghi đè; không hardcode sf; phân biệt phạm vi đo với ngoại suy.',
            '', '## 6. Kiểm thử, custody và DOI','',
            'Bộ kiểm thử: 7 test G3b/estimator và 5 test G4 (alignment dịch 1 cửa sổ, uniform quantiser, nhiễu chung, đầu vào vô hiệu, dirty certificate, hồi quy và pooling). Log cuối: [g4_tests.log](../../results/SMOKE/phase-G2/g4_tests.log).',
            f"Manifest dữ liệu mới: [g4_data_manifest.json](../../{custody_path}), {custody['n_files']} file, {custody['total_bytes']} byte. Manifest lịch sử DATA_MANIFEST được giữ nguyên; bản mới bổ sung chuỗi G3b/checkpoint.",
            f"DOI hiện tại: `{custody['doi']}`. Chưa có DOI/bản ghi công bố để xác minh. Inventory và SHA256 đã chuẩn bị; chưa có thao tác tải lên hay công bố. G′.7/G′.8 chưa được coi là vượt yêu cầu DOI.",
            '', '## 7. Các file để tái sử dụng','',
            '- [Bảng tổng hợp CSV](../../results/SMOKE/phase-G2/g4_nugget_summary.csv)',
            '- [Bảng 104 link/lượt CSV](../../results/SMOKE/phase-G2/g4_nugget_per_link_run.csv)',
            '- [JSON mô hình và mọi kiểm tra](../../results/SMOKE/phase-G2/g4_nugget_model.json)',
            '- [JSON hồi quy/bootstrap](../../results/SMOKE/phase-G2/g3b_orthogonality_audit.json)',
            '- [Manifest artifact G4](../../results/SMOKE/phase-G2/g4_artifact_manifest.json)',
            '', 'Lệnh tái lập (dùng tên đầu ra mới vì các artifact từ chối ghi đè): `python -m tools.g4_nugget_model --out NEW.json`; `python -m tools.g3b_orthogonality_audit --model NEW.json --out NEW_AUDIT.json --doc NEW_DOC.md`. Commit dữ liệu/code trước khi `python -m tools.g4_certify --model NEW.json --out NEW_CERT.json`.']
    with outputs[3].open('x') as f: f.write('\n'.join(lines)+'\n')
    files=set(model['sources']) | set(cert['evidence_sha256'])
    files.update(str(p) for p in outputs[:-1])
    files.update([str(cert_path),str(custody_path),'tools/g4_report.py','tools/g3b_orthogonality_audit.py',
                  str(BASE/'g3b_orthogonality_audit.json'),'docs/phase-G/66a-g3b-uncertainty-addendum.md'])
    files.update(str(p) for p in BASE.glob('g4*.log'))
    files.add(str(BASE/'g3b_orthogonality_audit.log'))
    write_contract_artifact(outputs[-1],{'schema':'dt4n.phase_g2.g4_artifact_manifest.v1',
                            'sha256':{p:sha256_of(p) for p in sorted(files)}})
    print('\n'.join(lines[:lines.index('## 2. Gate và dự đoán')]))
    print(outputs[3]); print(outputs[-1])


if __name__=='__main__': main()
