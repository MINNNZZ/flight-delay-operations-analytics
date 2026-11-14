"""Targeted robustness checks after the quality gate and baseline analysis."""
from common import *

require_quality_gate()
cols=['MONTH','DAY','YEAR','DAY_OF_WEEK','AIRLINE','ORIGIN_AIRPORT','DESTINATION_AIRPORT','SCHEDULED_DEPARTURE','CANCELLED','DIVERTED','ARRIVAL_DELAY']+CAUSES
d=pd.read_csv(ROOT/'flights.csv',usecols=cols,dtype={c:('category' if c in CODES else 'float64') for c in cols})
ap,al=read_dimensions()
valid=d.CANCELLED.eq(0)&d.DIVERTED.eq(0)&d.ARRIVAL_DELAY.notna()
d['HOUR']=(d.SCHEDULED_DEPARTURE//100).astype('int8')
d['BAND']=np.where(d.HOUR.between(6,11),'EARLY',np.where(d.HOUR.between(17,21),'EVENING','OTHER'))
d['POSITIVE_MINUTES']=d.ARRIVAL_DELAY.clip(lower=0)
d['SEVERE']=d.ARRIVAL_DELAY.ge(60)
d['DISRUPTED']=d.CANCELLED.eq(1)|d.DIVERTED.eq(1)|d.SEVERE
geo=d.ORIGIN_AIRPORT.isin(ap.IATA_CODE)&d.DESTINATION_AIRPORT.isin(ap.IATA_CODE)
results={}
for prefix,group in [('month',['MONTH']),('airline',['AIRLINE'])]:
    g=d.loc[valid & d.BAND.ne('OTHER')].groupby(group+['BAND'],observed=True).agg(n=('ARRIVAL_DELAY','size'),mean=('ARRIVAL_DELAY','mean'),median=('ARRIVAL_DELAY','median'),severe_rate=('SEVERE','mean')).reset_index()
    csv(g,f'robust_time_by_{prefix}')
    piv=g.pivot(index=group,columns='BAND',values='mean').dropna()
    results[f'{prefix}_positive_evening_gap']=int((piv.EVENING>piv.EARLY).sum())
    results[f'{prefix}_total']=len(piv)
g=d.loc[valid & d.BAND.ne('OTHER') & d.ARRIVAL_DELAY.le(360)].groupby('BAND').agg(n=('ARRIVAL_DELAY','size'),mean=('ARRIVAL_DELAY','mean'),median=('ARRIVAL_DELAY','median'),severe_rate=('SEVERE','mean')).reset_index()
csv(g,'robust_time_without_extremes')
g=d.loc[d.BAND.ne('OTHER')].groupby('BAND').agg(n=('DISRUPTED','size'),disruption_rate=('DISRUPTED','mean')).reset_index()
csv(g,'robust_time_including_cancellations')

matched=d.loc[geo&valid&d.BAND.ne('OTHER')].copy()
matched['ORIGIN_KEY']=matched.ORIGIN_AIRPORT
matched['ROUTE']=matched.ORIGIN_AIRPORT.astype(str)+' > '+matched.DESTINATION_AIRPORT.astype(str)
for label,strata in [('airline_origin_month',['AIRLINE','ORIGIN_KEY','MONTH']),('route_month',['ROUTE','MONTH'])]:
    g=matched.groupby(strata+['BAND'],observed=True).agg(n=('ARRIVAL_DELAY','size'),mean=('ARRIVAL_DELAY','mean'),severe=('SEVERE','mean')).reset_index()
    p=g.pivot(index=strata,columns='BAND',values=['n','mean','severe'])
    p=p.loc[(p['n']['EARLY']>=30)&(p['n']['EVENING']>=30)]
    w=np.minimum(p['n']['EARLY'],p['n']['EVENING'])
    out=pd.DataFrame({'early_n':p['n']['EARLY'],'evening_n':p['n']['EVENING'],'weight':w,'mean_difference':p['mean']['EVENING']-p['mean']['EARLY'],'severe_rate_difference':p['severe']['EVENING']-p['severe']['EARLY']})
    csv(out.reset_index(),f'matched_{label}')
    write_json(REPORTS/f'matched_{label}.json',{'strata':len(out),'early_flights':int(out.early_n.sum()),'evening_flights':int(out.evening_n.sum()),'weighted_mean_difference':float(np.average(out.mean_difference,weights=w)), 'weighted_severe_rate_difference':float(np.average(out.severe_rate_difference,weights=w)), 'strata_with_positive_mean_difference_share':float(out.mean_difference.gt(0).mean())})

for airport in ['LGA','ORD']:
    sub=d.loc[geo&d.ORIGIN_AIRPORT.eq(airport)]
    g=sub.groupby('MONTH').agg(flights=('SEVERE','size'),cancel_rate=('CANCELLED','mean'),severe=('SEVERE','sum'),disruption_rate=('DISRUPTED','mean')).reset_index()
    csv(g,f'robust_{airport.lower()}_month')
    hours=sub.loc[sub.BAND.ne('OTHER')].groupby('BAND').agg(flights=('SEVERE','size'),mean=('ARRIVAL_DELAY','mean'),median=('ARRIVAL_DELAY','median'),disruption_rate=('DISRUPTED','mean'),late_aircraft_minutes=('LATE_AIRCRAFT_DELAY','sum')).reset_index()
    csv(hours,f'robust_{airport.lower()}_time')

# Carrier contrast with common route x month x departure band, excluding October.
# Minimum n=10 completed flights in both groups per stratum; descriptive standardization.
for carrier in ['NK','MQ']:
    sub=d.loc[geo&valid].copy()
    sub['GROUP']=np.where(sub.AIRLINE.eq(carrier),carrier,'OTHER')
    g=sub.groupby(['ORIGIN_AIRPORT','DESTINATION_AIRPORT','MONTH','BAND','GROUP'],observed=True).agg(n=('SEVERE','size'),severe_rate=('SEVERE','mean'),mean=('ARRIVAL_DELAY','mean')).reset_index()
    p=g.pivot(index=['ORIGIN_AIRPORT','DESTINATION_AIRPORT','MONTH','BAND'],columns='GROUP',values=['n','severe_rate','mean'])
    p=p.loc[(p['n'][carrier]>=10)&(p['n']['OTHER']>=10)]
    w=np.minimum(p['n'][carrier],p['n']['OTHER'])
    out=pd.DataFrame({'carrier_n':p['n'][carrier],'other_n':p['n']['OTHER'],'weight':w,'severe_gap':p['severe_rate'][carrier]-p['severe_rate']['OTHER'],'mean_gap':p['mean'][carrier]-p['mean']['OTHER']})
    csv(out.reset_index(),f'robust_carrier_{carrier.lower()}')
    results[f'{carrier}_matched']={'strata':len(out),'carrier_n':int(out.carrier_n.sum()),'other_n':int(out.other_n.sum()),'severe_gap':float(np.average(out.severe_gap,weights=w)), 'mean_gap':float(np.average(out.mean_gap,weights=w))}

# Cancellation seasonality and interaction with carrier, not weather observations.
csv(d.loc[d.CANCELLED.eq(1)].groupby(['MONTH','AIRLINE'],observed=True).size().reset_index(name='cancelled'),'cancellations_month_airline')
write_json(REPORTS/'robustness_summary.json',results)
print(json.dumps(results,indent=2),flush=True)
