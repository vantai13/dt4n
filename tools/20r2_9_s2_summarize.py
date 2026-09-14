#!/usr/bin/env python3
"""Audit the complete S2 ledger, aggregate only seeds, and produce regional maps."""
from __future__ import annotations
import argparse
import importlib
import json
import numpy as np
import pandas as pd
from tools import sensitivity_20r2 as C
R=importlib.import_module('tools.20r2_9_s2_run')

def validate_frame(frame,run,zs):
    assert len(frame)==1404 and not frame.duplicated(['z_s','t_delay_ms','t_loss']).any()
    assert set(zip(frame.t_delay_ms,frame.t_loss))==set(C.GRID)
    assert set(frame.z_s)==set(zs)
    assert set(frame.cell)=={run['cell']} and set(frame.tau)=={run['tau']} and set(frame.seed)=={run['seed']}
    assert np.isfinite(frame[['d_sla_at_threshold','viol_rate_truth','viol_rate_twin']]).all().all()
    assert frame.viol_rate_truth.between(0,1).all() and frame.viol_rate_twin.between(0,1).all()
    assert np.array_equal(frame.d_sla_at_threshold.to_numpy(),(frame.viol_rate_twin-frame.viol_rate_truth).to_numpy())

def aggregate(d):
    keys=['cell','tau','z_s','t_delay_ms','t_loss']
    grouped=d.groupby(keys,sort=True)
    out=grouped.agg(d_sla_at_threshold=('d_sla_at_threshold','mean'),
        d_sla_min_seed=('d_sla_at_threshold','min'),d_sla_max_seed=('d_sla_at_threshold','max'),
        viol_rate_truth=('viol_rate_truth','mean'),viol_rate_twin=('viol_rate_twin','mean'),
        truth_min_seed=('viol_rate_truth','min'),truth_max_seed=('viol_rate_truth','max'),
        n_seeds=('seed','nunique')).reset_index()
    assert (out.n_seeds==5).all()
    out['truth_region']=np.where(out.truth_max_seed==0,'ALL_SEEDS_TRUTH_ZERO',
        np.where(out.truth_min_seed==1,'ALL_SEEDS_TRUTH_ONE','TRUTH_INTERIOR_OR_SEED_MIXED'))
    out['effect_region']=np.where((out.d_sla_min_seed==0)&(out.d_sla_max_seed==0),'ALL_SEEDS_ZERO','OBSERVED_NONZERO_SOME_SEED')
    return out

def build(out_table):
    plan=C.read(R.PLAN);log=[json.loads(x) for x in (C.ROOT/R.LOG).read_text().splitlines()]
    done={r['run_index']:r for r in log if r['kind']=='run' and r['returncode']==0}
    assert set(done)==set(range(320)), 'incomplete S2 campaign'
    envs=[r for r in log if r['kind']=='env'];assert len(envs)==1
    assert envs[0]['signed_tag_commit']==envs[0]['git_commit']==C.git('rev-parse',R.TAG+'^{commit}')
    assert envs[0]['plan_sha256']==C.sha(R.PLAN) and not envs[0]['guard_skipped']
    frames=[];reports=[];pins=[R.PLAN,R.LOG];fields=None
    for run in plan['runs']:
        e=done[run['run_index']]
        assert e['git_commit']==envs[0]['git_commit']
        for key,value in run.items():assert e[key]==value, 'ledger differs from signed plan'
        R.verify_completed(run,e);report=C.read(e['sidecar'])
        assert report['parquet_sha256']==e['sha256']
        assert report['controls']['original_campaign_fields_exact'] and report['controls']['signed_threshold_identity_max_abs_diff']==0
        for path,want in report['inputs_sha256'].items():assert C.sha(path)==want, 'worker input pin changed'
        assert report['source_sha256']['measurements/decision_error_v2.py']==C.sha('measurements/decision_error_v2.py')
        f=pd.read_parquet(C.ROOT/run['out']);validate_frame(f,run,plan['grid']['z_values'])
        frames.append(f);reports.append(report);pins.extend([run['out'],e['sidecar']])
    d=pd.concat(frames,ignore_index=True);assert len(d)==449280
    table=aggregate(d);assert len(table)==89856
    table_path=C.ROOT/out_table;assert not table_path.exists()
    table_path.parent.mkdir(parents=True,exist_ok=True);table.to_parquet(table_path,index=False)
    reference=[]
    for (cell,tau),f in table[table.z_s==.366].groupby(['cell','tau']):
        op=f[(f.t_delay_ms==50)&(f.t_loss==.01)].iloc[0]
        peak=f.loc[f.d_sla_at_threshold.abs().idxmax()]
        reference.append({'cell':cell,'tau':float(tau),'z_s':.366,
            'operating_point':op.to_dict(),'max_abs_observed':peak.to_dict(),
            'n_thresholds_all_seeds_zero':int((f.effect_region=='ALL_SEEDS_ZERO').sum()),
            'n_truth_zero':int((f.truth_region=='ALL_SEEDS_TRUTH_ZERO').sum()),
            'n_truth_one':int((f.truth_region=='ALL_SEEDS_TRUTH_ONE').sum())})
    doc={**C.provenance('tools/20r2_9_s2_summarize.py',pins,plan['grid']['z_values']),
        'schema':'dt4n.s2_threshold_map.v1','estimand_id':'SLA_VIOL_BY_AGE_BY_THRESHOLD',
        'n_runs':320,'n_raw_rows':len(d),'n_seed_mean_rows':len(table),
        'table':out_table,'table_sha256':C.sha(out_table),'reference_z_rows':reference,
        'controls':{'all_original_fields_exact':True,'n_signed_threshold_identities':320*13,
                    'signed_threshold_max_abs_diff':0.,'ledger_complete_and_hashes_verified':True},
        'timing':{'worker_wall_seconds_sum':sum(done[i]['seconds'] for i in done),
                  'peak_worker_rss_kib':max(r['peak_rss_kib'] for r in reports),
                  'estimate_minutes':68.},
        'reading':'Means across five seeds only; no pooled-eight headline. Observed nonzero is not statistical significance. Truth-zero and truth-one regions differ. Operating SLA is unchanged.'}
    doc['validity']=reports[0]['validity'];return doc,table

def plots(table,pdf_path,png_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    selected=table[table.z_s==.366]
    def panel(ax,f,value,title):
        pivot=f.pivot(index='t_delay_ms',columns='t_loss',values=value).reindex(index=C.TD,columns=C.TL)
        vmax=max(float(np.max(np.abs(pivot.to_numpy()))),1e-6) if value=='d_sla_at_threshold' else 1.
        im=ax.imshow(pivot,origin='lower',aspect='auto',cmap='coolwarm' if value=='d_sla_at_threshold' else 'viridis',
            vmin=-vmax if value=='d_sla_at_threshold' else 0,vmax=vmax)
        ax.set_xticks(range(12),[f'{x:g}' for x in C.TL],rotation=90,fontsize=6)
        ax.set_yticks(range(9),[f'{x:g}' for x in C.TD],fontsize=7)
        ax.scatter([C.TL.index(.01)],[C.TD.index(50)],marker='s',s=75,facecolors='none',edgecolors='black',linewidths=1.5)
        ax.set_title(title,fontsize=9);ax.set_xlabel('Loss threshold');ax.set_ylabel('Delay threshold (ms)')
        plt.colorbar(im,ax=ax,shrink=.8)
    with PdfPages(C.ROOT/pdf_path) as pdf:
        for cell,g in selected.groupby('cell'):
            fig,axes=plt.subplots(4,4,figsize=(17,14),constrained_layout=True)
            for i,tau in enumerate(C.TAUS):
                f=g[g.tau==tau]
                panel(axes.flat[2*i],f,'d_sla_at_threshold',f'tau={tau:g}: mean d_sla')
                panel(axes.flat[2*i+1],f,'viol_rate_truth',f'tau={tau:g}: truth violation')
            fig.suptitle(f'{cell}; z=0.366s; a=0.9; 5 seed means; square=(50ms,1%). Nonzero is descriptive.',fontsize=12)
            pdf.savefig(fig);plt.close(fig)
    fig,axes=plt.subplots(4,4,figsize=(17,14),constrained_layout=True)
    for i,(cell,g) in enumerate(selected[selected.tau==3].groupby('cell')):
        panel(axes.flat[2*i],g,'d_sla_at_threshold',cell+': mean d_sla')
        panel(axes.flat[2*i+1],g,'viol_rate_truth',cell+': truth violation')
    fig.suptitle('S2 at tau=3, z=0.366s; each effect panel has its own color scale; operating point marked')
    fig.savefig(C.ROOT/png_path,dpi=140);plt.close(fig)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True)
    ap.add_argument('--table',required=True);ap.add_argument('--pdf',required=True);ap.add_argument('--png',required=True)
    a=ap.parse_args();doc,table=build(a.table);plots(table,a.pdf,a.png)
    doc['figures']={p:C.sha(p) for p in (a.pdf,a.png)};C.write(a.out,doc)
    print(doc['controls']);print(doc['timing'])
    for r in doc['reference_z_rows']:
        if r['tau']==3:print(r['cell'],'operating d_sla',r['operating_point']['d_sla_at_threshold'],'max abs',r['max_abs_observed']['d_sla_at_threshold'])
    return 0
if __name__=='__main__':raise SystemExit(main())
