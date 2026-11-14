"""Phase 1: exhaustive quality inspection before any business analysis."""
from common import *
from datetime import datetime, timezone
import uuid

setup()
print('Reading all source rows...', flush=True)
df = read_flights()
ap, al = read_dimensions()
n = len(df)
dt = dates(df)
complete = df.CANCELLED.eq(0) & df.DIVERTED.eq(0)
print(f'Loaded {n:,} rows x {df.shape[1]} columns', flush=True)
hashes = {name: sha256(ROOT / name) for name in ['flights.csv', 'airports.csv', 'airlines.csv']}
run_id = str(uuid.uuid4())
manifest = {'sha256': hashes, 'profile_run_id': run_id, 'profile_started_at_utc': datetime.now(timezone.utc).isoformat(), 'source_files': {p.name: p.stat().st_size for p in ROOT.glob('*.csv')}}
miss = pd.DataFrame({'column': df.columns, 'dtype': [str(t) for t in df.dtypes], 'missing_rows': df.isna().sum().values})
miss['missing_pct'] = miss.missing_rows / n * 100
for label, mask in [('completed', complete), ('cancelled', df.CANCELLED.eq(1)), ('diverted', df.DIVERTED.eq(1))]:
    miss[f'{label}_missing'] = df.loc[mask].isna().sum().values
csv(miss, 'quality_missingness')
numeric = df.select_dtypes('number')
summary = pd.DataFrame({c: numeric[c].astype('float64').describe(percentiles=[.01, .25, .5, .75, .9, .95, .99]) for c in numeric}).T.reset_index(names='column')
csv(summary, 'quality_numeric_profile')
checks = {}
checks['exact_duplicate_excess'] = int(df.duplicated().sum())
keydups = df.duplicated(KEY, keep=False)
checks['duplicate_key_rows'] = int(keydups.sum())
csv(df.loc[keydups].head(1000), 'quality_duplicate_key_examples')
checks['invalid_dates'] = int(dt.isna().sum())
checks['weekday_mismatch'] = int(((dt.dt.dayofweek + 1) != df.DAY_OF_WEEK).sum())
checks['invalid_status'] = int((~df.CANCELLED.isin([0, 1]) | ~df.DIVERTED.isin([0, 1])).sum())
checks['cancelled_and_diverted'] = int((df.CANCELLED.eq(1) & df.DIVERTED.eq(1)).sum())
checks['unknown_airline'] = int((~df.AIRLINE.isin(al.IATA_CODE)).sum())
checks['noninteger_numeric_cells'] = int(((numeric % 1).ne(0) & numeric.notna()).sum().sum())
checks['whitespace_code_cells'] = sum(int(df[c].astype('string').str.strip().ne(df[c].astype('string')).sum()) for c in CODES)
checks['nonfinite_numeric_cells'] = int((~np.isfinite(numeric) & numeric.notna()).sum().sum())
checks['complete_missing_arrival'] = int((complete & df.ARRIVAL_DELAY.isna()).sum())
checks['complete_missing_departure'] = int((complete & df.DEPARTURE_DELAY.isna()).sum())
checks['cancelled_arrival_present'] = int((df.CANCELLED.eq(1) & df.ARRIVAL_DELAY.notna()).sum())
checks['noncancelled_reason_present'] = int((df.CANCELLED.eq(0) & df.CANCELLATION_REASON.notna()).sum())
checks['cancelled_reason_missing'] = int((df.CANCELLED.eq(1) & df.CANCELLATION_REASON.isna()).sum())
checks['invalid_cancellation_reason'] = int((df.CANCELLATION_REASON.notna() & ~df.CANCELLATION_REASON.isin(list('ABCD'))).sum())
for c in TIMES:
    checks[f'invalid_{c}'] = int((~valid_time(df[c])).sum())
    checks[f'rollover_2400_{c}'] = int(df[c].eq(2400).sum())
for c in ['TAXI_OUT', 'TAXI_IN', 'SCHEDULED_TIME', 'ELAPSED_TIME', 'AIR_TIME', 'DISTANCE'] + CAUSES:
    checks[f'negative_{c}'] = int(df[c].lt(0).sum())
checks['zero_distance'] = int(df.DISTANCE.eq(0).sum())
checks['same_origin_destination'] = int(df.ORIGIN_AIRPORT.astype(str).eq(df.DESTINATION_AIRPORT.astype(str)).sum())
checks['elapsed_vs_components_mismatch'] = int((complete & df.ELAPSED_TIME.notna() & (df.ELAPSED_TIME - df.AIR_TIME - df.TAXI_IN - df.TAXI_OUT).abs().gt(1)).sum())
checks['arrival_delay_identity_mismatch'] = int((complete & (df.ARRIVAL_DELAY - df.DEPARTURE_DELAY - df.ELAPSED_TIME + df.SCHEDULED_TIME).abs().gt(1)).sum())
inconsistent = complete & (df.ARRIVAL_DELAY - df.DEPARTURE_DELAY - df.ELAPSED_TIME + df.SCHEDULED_TIME).abs().gt(1)
csv(df.loc[inconsistent], 'quality_inconsistent_duration_rows')
for actual, sched, delay in [('DEPARTURE_TIME', 'SCHEDULED_DEPARTURE', 'DEPARTURE_DELAY'), ('ARRIVAL_TIME', 'SCHEDULED_ARRIVAL', 'ARRIVAL_DELAY')]:
    residual = (minutes(df[actual]) - minutes(df[sched]) - df[delay]) % 1440
    checks[f'{delay}_clock_mismatch'] = int((df[delay].notna() & df[actual].notna() & residual.ne(0)).sum())
cause_present = df[CAUSES].notna().all(axis=1)
cause_sum = df[CAUSES].sum(axis=1, min_count=5)
checks['cause_partial_rows'] = int((df[CAUSES].notna().any(axis=1) & ~cause_present).sum())
checks['late_arrival_missing_cause'] = int((complete & df.ARRIVAL_DELAY.ge(15) & ~cause_present).sum())
checks['cause_outside_late_arrival'] = int((cause_present & ~(complete & df.ARRIVAL_DELAY.ge(15))).sum())
checks['cause_sum_mismatch'] = int((cause_present & (cause_sum - df.ARRIVAL_DELAY).abs().gt(1)).sum())
checks['extreme_dep_gt360'] = int(df.DEPARTURE_DELAY.gt(360).sum())
checks['extreme_arr_gt360'] = int(df.ARRIVAL_DELAY.gt(360).sum())
checks['early_arr_lt_minus60'] = int(df.ARRIVAL_DELAY.lt(-60).sum())
checks['missing_tail'] = int(df.TAIL_NUMBER.isna().sum())
airport_rows = []
for c in ['ORIGIN_AIRPORT', 'DESTINATION_AIRPORT']:
    known = df[c].isin(ap.IATA_CODE)
    numeric_code = df[c].astype(str).str.fullmatch(r'\d+')
    checks[f'unresolved_{c}'] = int((~known).sum())
    checks[f'numeric_{c}'] = int(numeric_code.sum())
    t = pd.crosstab(df.MONTH, known).rename(columns={False: 'unresolved', True: 'resolved'}).reset_index()
    t['field'] = c
    airport_rows.append(t)
    csv(df.loc[~known, c].value_counts().rename_axis('code').reset_index(name='rows'), f'quality_unknown_{c.lower()}')
csv(pd.concat(airport_rows), 'quality_airport_coverage')
daily = dt.value_counts().sort_index()
csv(daily.rename_axis('date').reset_index(name='flights'), 'quality_daily_coverage')
csv(df.groupby(['MONTH', 'CANCELLATION_REASON'], observed=True).size().reset_index(name='flights'), 'quality_cancellation_codes')
dimchecks = {
    'airports_rows': len(ap), 'airlines_rows': len(al),
    'airports_duplicate_keys': int(ap.IATA_CODE.duplicated().sum()),
    'airlines_duplicate_keys': int(al.IATA_CODE.duplicated().sum()),
    'airports_missing_cells': ap.isna().sum().to_dict(),
    'airlines_missing_cells': al.isna().sum().to_dict(),
    'invalid_latitude': int((ap.LATITUDE.notna() & ~ap.LATITUDE.between(-90,90)).sum()),
    'invalid_longitude': int((ap.LONGITUDE.notna() & ~ap.LONGITUDE.between(-180,180)).sum()),
}
result = {'rows': n, 'columns': len(df.columns), 'date_min': str(dt.min().date()), 'date_max': str(dt.max().date()), 'days': len(daily), 'checks': checks, 'dimensions': dimchecks, 'monthly_rows': df.MONTH.value_counts().sort_index().to_dict(), 'schema': {c: str(t) for c,t in df.dtypes.items()}}
result['source_sha256'] = {name: value for name, value in hashes.items() if name.endswith('.csv')}
result['profile_run_id'] = run_id
write_json(REPORTS / 'data_profile.json', result)
write_json(REPORTS / 'source_manifest.json', manifest)
print(json.dumps(result, indent=2, default=int), flush=True)
