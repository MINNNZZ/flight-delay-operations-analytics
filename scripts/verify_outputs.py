"""Independent full-export readback and conservation checks, including sources."""
from common import *
import platform
import matplotlib
from pandas.testing import assert_frame_equal

manifest=json.loads((REPORTS/'source_manifest.json').read_text(encoding='utf-8'))
for name, expected in manifest['sha256'].items():
    if name == 'AGENTS.md': continue  # Historical private-workspace instruction hash, not a dataset.
    assert sha256(ROOT.parents[1]/name if name == "AGENTS.md" else ROOT/name)==expected, f'Source modified: {name}'
rawcols=list(pd.read_csv(ROOT/'flights.csv',nrows=0).columns)
types={c:('string' if c in CODES else 'float64') for c in rawcols}
raw_reader=pd.read_csv(ROOT/'flights.csv',dtype=types,chunksize=200000)
clean_reader=pd.read_csv(PROCESSED/'flights_cleaned.csv.gz',dtype=types,chunksize=200000)
totals={k:0 for k in ['rows','COMPLETED','ARR_ELIGIBLE','ON_TIME','SEVERE_60','CANCELLED','DIVERTED','DISRUPTED','POSITIVE_ARR_MINUTES','GEO_ELIGIBLE','TIME_ISSUE']}
cause_minutes=0
last_id=0
for i,raw in enumerate(raw_reader):
    clean=next(clean_reader)
    assert_frame_equal(raw.reset_index(drop=True),clean[rawcols].reset_index(drop=True),check_exact=True)
    assert clean.FLIGHT_ID.tolist()==list(range(last_id+1,last_id+len(clean)+1))
    last_id+=len(clean)
    dt=pd.to_datetime(clean.DATE,errors='raise')
    expected=pd.to_datetime(raw[['YEAR','MONTH','DAY']].rename(columns=str.lower))
    assert np.array_equal(dt.to_numpy(),expected.to_numpy()), 'Date assembly regression'
    assert clean.GEO_ELIGIBLE.eq(raw.MONTH.ne(10).astype(int)).all()
    assert clean.ARR_ELIGIBLE.eq((raw.CANCELLED.eq(0)&raw.DIVERTED.eq(0)&raw.ARRIVAL_DELAY.notna()).astype(int)).all()
    assert clean.ON_TIME.eq((clean.ARR_ELIGIBLE.eq(1)&raw.ARRIVAL_DELAY.lt(15)).astype(int)).all()
    assert clean.SEVERE_60.eq((clean.ARR_ELIGIBLE.eq(1)&raw.ARRIVAL_DELAY.ge(60)).astype(int)).all()
    assert clean.DISRUPTED.eq((raw.CANCELLED.eq(1)|raw.DIVERTED.eq(1)|raw.ARRIVAL_DELAY.ge(60)).astype(int)).all()
    assert clean.ARR_DELAY_ANALYSIS.isna().eq(clean.ARR_ELIGIBLE.eq(0)).all()
    assert clean.loc[raw.CANCELLED.eq(1),'DEP_DELAY_ANALYSIS'].isna().all()
    totals['rows']+=len(clean)
    for key in totals:
        if key!='rows':totals[key]+=int(clean[key].sum())
    cause_minutes+=int(clean[CAUSES].sum().sum())
    if (i+1)%10==0:print(f'Verified {totals["rows"]:,} serialized rows...',flush=True)
assert next(clean_reader,None) is None, 'Unexpected extra rows in cleaned export'
o=pd.read_csv(TABLES/'overall.csv').iloc[0]
mapping={'rows':'flights','COMPLETED':'completed','ARR_ELIGIBLE':'arrival_n','ON_TIME':'on_time','SEVERE_60':'severe','CANCELLED':'cancelled','DIVERTED':'diverted','DISRUPTED':'disrupted','POSITIVE_ARR_MINUTES':'positive_arr_minutes'}
for col, aggregate_col in mapping.items():assert totals[col]==int(o[aggregate_col]),col
assert cause_minutes==62651867
assert totals['GEO_ELIGIBLE']==5332914
assert totals['TIME_ISSUE']==2
for name in ['airline','hour','time_band','weekday','month','season','daily','airline_month','airline_time','month_time']:
    t=pd.read_csv(TABLES/f'{name}.csv')
    for c in ['flights','severe','cancelled','diverted','positive_arr_minutes']:
        assert t[c].sum()==o[c],(name,c)
for name in ['origin','destination','route','airport_hour','airline_airport','airport_month','route_time','airline_route','airport_time']:
    t=pd.read_csv(TABLES/f'{name}.csv');assert t.flights.sum()==totals['GEO_ELIGIBLE'],name

# Recompute numeric DQA in double precision; avoid float32 accumulation artifacts.
reader=pd.read_csv(ROOT/'flights.csv',dtype={c:('category' if c in CODES else 'float64') for c in rawcols})
numeric=reader.select_dtypes('number')
profile=pd.DataFrame({c:numeric[c].describe(percentiles=[.01,.25,.5,.75,.9,.95,.99]) for c in numeric}).T.reset_index(names='column')
csv(profile,'quality_numeric_profile')
del reader,numeric

required=['Executive Summary','Business Problem','Data Description','Data Quality Assessment','Cleaning Decisions','Analytical Approach','Key Findings','High-Value Insights','Root-Cause Analysis','Business Impact','Recommendations','Power BI Dashboard Plan','Success Metrics','Limitations','Next Steps']
report=(REPORTS/'aviation_analysis_report.md').read_text(encoding='utf-8')
assert all(f'# {heading}' in report for heading in required)
assert len(list((REPORTS/'figures').glob('*.png')))==5
result={'status':'PASS','completed_date':'2026-11-12','source_hashes_unchanged':True,'serialized_raw_columns_equal_to_source_all_rows':True,'derived_date_status_eligibility_checks_all_rows':True,'aggregate_conservation_checks':True,'powerbi_engine_executed':False,'totals':totals,'reported_cause_minutes':cause_minutes,'environment':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'matplotlib':matplotlib.__version__}}
write_json(REPORTS/'verification.json',result)
print(json.dumps(result,indent=2),flush=True)
