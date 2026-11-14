"""Skill-driven robustness review; raw/processed data and Power BI are read-only."""
from common import *
import argparse
import math

FEATURES=['arrival_n','arrival_sum','severe','scheduled','disrupted']
METRICS=['mean_arrival_gap_minutes','severe_rate_gap_pp','severe_risk_ratio','disruption_rate_gap_pp']

def contrasts(totals):
    """Weighted contrasts from [..., EARLY/EVENING, sufficient statistics]."""
    x=np.asarray(totals,dtype='float64')
    if x.shape[-2:]!=(2,5):raise ValueError('Expected two time groups and five sufficient statistics')
    if not np.isfinite(x).all() or (x[...,0]<=0).any() or (x[...,3]<=0).any():
        raise ValueError('Nonfinite values or empty arrival/scheduled denominator')
    means=x[...,1]/x[...,0]
    severe=x[...,2]/x[...,0]
    disruption=x[...,4]/x[...,3]
    if (severe[...,0]<=0).any():raise ValueError('Early severe rate must be positive for a risk ratio')
    return np.stack([means[...,1]-means[...,0],100*(severe[...,1]-severe[...,0]),severe[...,1]/severe[...,0],100*(disruption[...,1]-disruption[...,0])],axis=-1)

def month_block_bootstrap(values,months,block_days,repetitions=3000,seed=20261112):
    """Paired circular day blocks, sampled separately inside each calendar month."""
    a=np.asarray(values,dtype='float64');months=np.asarray(months)
    if a.ndim!=3 or a.shape[1:]!=(2,5) or len(months)!=len(a):raise ValueError('Invalid day panel')
    if block_days<1 or repetitions<2:raise ValueError('Positive block length and at least two repetitions required')
    rng=np.random.default_rng(seed)
    totals=np.zeros((repetitions,2,5))
    for month in np.unique(months):
        subset=a[months==month];n=len(subset)
        if block_days>n:raise ValueError('Block length exceeds available days in a month')
        starts=rng.integers(0,n,size=(repetitions,math.ceil(n/block_days)))
        indices=((starts[:,:,None]+np.arange(block_days))%n).reshape(repetitions,-1)[:,:n]
        totals+=subset[indices].sum(axis=1)
    return contrasts(totals)

def carrier_comparison(frame,carrier,time_column,min_n):
    sub=frame.copy()
    sub['GROUP']=np.where(sub.AIRLINE.eq(carrier),'CARRIER','OTHER')
    keys=['ORIGIN_AIRPORT','DESTINATION_AIRPORT','MONTH',time_column]
    g=sub.groupby(keys+['GROUP'],observed=True).agg(n=('ARR','size'),mean=('ARR','mean'),severe=('SEVERE','sum')).reset_index()
    p=g.pivot(index=keys,columns='GROUP',values=['n','mean','severe'])
    p=p.loc[(p['n']['CARRIER']>=min_n)&(p['n']['OTHER']>=min_n)]
    if p.empty:raise ValueError('No common support for requested comparison')
    cn=p['n']['CARRIER'];on=p['n']['OTHER'];w=np.minimum(cn,on)
    cr=p['severe']['CARRIER']/cn;orr=p['severe']['OTHER']/on
    cmean=p['mean']['CARRIER'];omean=p['mean']['OTHER']
    cmask=sub.AIRLINE.eq(carrier)
    return {
        'carrier':carrier,'time_definition':time_column,'min_arrivals_each_group':min_n,'strata':len(p),
        'geographic_carrier_n':int(cmask.sum()),'geographic_other_n':int((~cmask).sum()),
        'retained_carrier_n':int(cn.sum()),'retained_other_n':int(on.sum()),
        'carrier_common_support_share':float(cn.sum()/cmask.sum()),'other_common_support_share':float(on.sum()/(~cmask).sum()),
        'geographic_raw_severe_gap_pp':float(100*(sub.loc[cmask,'SEVERE'].mean()-sub.loc[~cmask,'SEVERE'].mean())),
        'geographic_raw_mean_gap_minutes':float(sub.loc[cmask,'ARR'].mean()-sub.loc[~cmask,'ARR'].mean()),
        'retained_raw_severe_gap_pp':float(100*(p['severe']['CARRIER'].sum()/cn.sum()-p['severe']['OTHER'].sum()/on.sum())),
        'retained_raw_mean_gap_minutes':float(np.average(cmean,weights=cn)-np.average(omean,weights=on)),
        'standardized_severe_gap_pp':float(100*np.average(cr-orr,weights=w)),
        'standardized_mean_gap_minutes':float(np.average(cmean-omean,weights=w)),
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repetitions',type=int,default=3000)
    args=parser.parse_args()
    require_quality_gate()
    folder=REPORTS/'skill_review';folder.mkdir(exist_ok=True)
    cols=['YEAR','MONTH','DAY','AIRLINE','ORIGIN_AIRPORT','DESTINATION_AIRPORT','SCHEDULED_DEPARTURE','CANCELLED','DIVERTED','ARRIVAL_DELAY']
    print('Reading full source population for targeted review...',flush=True)
    d=pd.read_csv(ROOT/'flights.csv',usecols=cols,dtype={c:('category' if c in CODES else 'float64') for c in cols})
    d['DATE']=dates(d);d['HOUR']=(d.SCHEDULED_DEPARTURE//100).astype('int8')
    d['BAND']=np.where(d.HOUR.between(6,11),'EARLY',np.where(d.HOUR.between(17,21),'EVENING','OTHER'))
    valid=d.CANCELLED.eq(0)&d.DIVERTED.eq(0)&d.ARRIVAL_DELAY.notna()
    d['ARR']=d.ARRIVAL_DELAY.where(valid);d['SEVERE']=valid&d.ARR.ge(60)
    d['DISRUPTED']=d.CANCELLED.eq(1)|d.DIVERTED.eq(1)|d.SEVERE
    panel=d.loc[d.BAND.ne('OTHER')].groupby(['DATE','BAND'],observed=True).agg(arrival_n=('ARR','count'),arrival_sum=('ARR','sum'),severe=('SEVERE','sum'),scheduled=('ARR','size'),disrupted=('DISRUPTED','sum'))
    calendar=pd.date_range(d.DATE.min(),d.DATE.max())
    assert calendar.size==365 and d.DATE.nunique()==365
    expected=pd.MultiIndex.from_product([calendar,['EARLY','EVENING']],names=['DATE','BAND'])
    panel=panel.reindex(expected)
    assert panel.notna().all().all() and panel.arrival_n.gt(0).all()
    panel.reset_index().to_csv(folder/'daily_paired_time_panel.csv',index=False,date_format='%Y-%m-%d')
    values=panel[FEATURES].to_numpy().reshape(365,2,5)
    point=contrasts(values.sum(axis=0))
    bootstrap=[]
    for block in [1,7,14]:
        sims=month_block_bootstrap(values,calendar.month.to_numpy(),block,args.repetitions,20261112)
        for j,name in enumerate(METRICS):
            low,high=np.quantile(sims[:,j],[.025,.975])
            bootstrap.append({'metric':name,'block_days':block,'repetitions':args.repetitions,'seed':20261112,'estimate':float(point[j]),'percentile_2_5':float(low),'percentile_97_5':float(high)})
    pd.DataFrame(bootstrap).to_csv(folder/'time_block_stability.csv',index=False)
    print('Paired day-block stability checks complete.',flush=True)
    ap,_=read_dimensions()
    geo=d.ORIGIN_AIRPORT.isin(ap.IATA_CODE)&d.DESTINATION_AIRPORT.isin(ap.IATA_CODE)
    f=d.loc[valid&geo,['AIRLINE','ORIGIN_AIRPORT','DESTINATION_AIRPORT','MONTH','HOUR','BAND','ARR','SEVERE']]
    results=[]
    for carrier in ['NK','MQ']:
        for time_column,min_n in [('BAND',10),('BAND',30),('HOUR',10)]:
            result=carrier_comparison(f,carrier,time_column,min_n);results.append(result)
            print(carrier,time_column,min_n,'retained',result['retained_carrier_n'],'gap_pp',round(result['standardized_severe_gap_pp'],4),flush=True)
    pd.DataFrame(results).to_csv(folder/'carrier_comparison_sensitivity.csv',index=False)
    previous=json.loads((REPORTS/'robustness_summary.json').read_text())
    for carrier in ['NK','MQ']:
        r=next(x for x in results if x['carrier']==carrier and x['time_definition']=='BAND' and x['min_arrivals_each_group']==10)
        old=previous[f'{carrier}_matched']
        assert r['retained_carrier_n']==old['carrier_n']
        assert np.isclose(r['standardized_severe_gap_pp']/100,old['severe_gap'],rtol=0,atol=1e-12)
    baseline=pd.read_csv(TABLES/'time_band.csv').set_index('TIME_BAND')
    assert np.isclose(point[0],baseline.loc['17-21','avg_arr']-baseline.loc['06-11','avg_arr'])
    assert np.isclose(point[1],100*(baseline.loc['17-21','severe_rate']-baseline.loc['06-11','severe_rate']))
    write_json(folder/'statistical_review.json',{'status':'PASS','population_rows':len(d),'paired_days':len(calendar),'bootstrap_scope':'Historical within-2015 stability, not count uncertainty, future forecast or causal effect. Month-stratified circular blocks assume local dependence within each month; wrap-around and block choice are approximations.','baseline_time_contrasts':dict(zip(METRICS,map(float,point))),'bootstrap':bootstrap,'carrier_comparisons':results,'previous_matched_results_reproduced':True,'source_sha256':require_current_profile()['source_sha256']})
    print('Review results saved; original KPIs and prior matched results reproduced.',flush=True)

if __name__=='__main__':main()
