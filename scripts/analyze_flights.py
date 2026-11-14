"""Clean, validate and execute full-population descriptive/diagnostic analysis."""
from common import *
import sys

setup()
profile = require_current_profile()
checks = profile['checks']
blocking = ['invalid_dates', 'weekday_mismatch', 'invalid_status', 'cancelled_and_diverted', 'unknown_airline', 'duplicate_key_rows', 'nonfinite_numeric_cells', 'complete_missing_arrival']
if any(checks[k] for k in blocking):
    write_json(REPORTS / 'quality_gate.json', {'quality_status': 'NOT_READY', 'critical_issues': {k: checks[k] for k in blocking if checks[k]}})
    sys.exit('Blocking quality issue: inspect profile before analysis')
df = read_flights()
ap, al = read_dimensions()
n = len(df)
original_columns = list(df.columns)
print('Cleaning and validating derived fields...', flush=True)
df['FLIGHT_ID'] = np.arange(1, n+1, dtype='int64')
df['DATE'] = dates(df)
df['DEP_HOUR'] = (df.SCHEDULED_DEPARTURE // 100).astype('int8')
df['TIME_BAND'] = pd.Categorical(np.select([df.DEP_HOUR.lt(6), df.DEP_HOUR.lt(12), df.DEP_HOUR.lt(17), df.DEP_HOUR.lt(22)], ['00-05', '06-11', '12-16', '17-21'], default='22-23'))
df['SEASON'] = pd.Categorical(df.MONTH.map({1:'DJF',2:'DJF',3:'MAM',4:'MAM',5:'MAM',6:'JJA',7:'JJA',8:'JJA',9:'SON',10:'SON',11:'SON',12:'DJF'}))
known_origin = df.ORIGIN_AIRPORT.isin(ap.IATA_CODE)
known_dest = df.DESTINATION_AIRPORT.isin(ap.IATA_CODE)
df['ORIGIN_KEY'] = df.ORIGIN_AIRPORT.cat.add_categories(['__UNRESOLVED__']).where(known_origin, '__UNRESOLVED__')
df['DESTINATION_KEY'] = df.DESTINATION_AIRPORT.cat.add_categories(['__UNRESOLVED__']).where(known_dest, '__UNRESOLVED__')
df['GEO_ELIGIBLE'] = (known_origin & known_dest).astype('int8')
df['ROUTE'] = pd.Categorical(df.ORIGIN_KEY.astype(str) + ' > ' + df.DESTINATION_KEY.astype(str))
df['COMPLETED'] = (df.CANCELLED.eq(0) & df.DIVERTED.eq(0)).astype('int8')
clock_bad = df.DEPARTURE_DELAY.notna() & df.DEPARTURE_TIME.notna() & ((minutes(df.DEPARTURE_TIME)-minutes(df.SCHEDULED_DEPARTURE)-df.DEPARTURE_DELAY)%1440).ne(0)
duration_bad = df.COMPLETED.eq(1) & (df.ARRIVAL_DELAY-df.DEPARTURE_DELAY-df.ELAPSED_TIME+df.SCHEDULED_TIME).abs().gt(1)
df['TIME_ISSUE'] = (clock_bad | duration_bad).astype('int8')
df['ARR_DELAY_ANALYSIS'] = df.ARRIVAL_DELAY.astype('float64').where(df.COMPLETED.eq(1))
df['DEP_DELAY_ANALYSIS'] = df.DEPARTURE_DELAY.astype('float64').where(df.CANCELLED.eq(0) & ~clock_bad)
df['ARR_ELIGIBLE'] = df.ARR_DELAY_ANALYSIS.notna().astype('int8')
df['ON_TIME'] = (df.ARR_ELIGIBLE.eq(1) & df.ARR_DELAY_ANALYSIS.lt(15)).astype('int8')
df['DELAYED_15'] = df.ARR_DELAY_ANALYSIS.ge(15).astype('int8')
df['SEVERE_60'] = df.ARR_DELAY_ANALYSIS.ge(60).astype('int8')
df['DISRUPTED'] = (df.CANCELLED.eq(1) | df.DIVERTED.eq(1) | df.SEVERE_60.eq(1)).astype('int8')
df['POSITIVE_ARR_MINUTES'] = df.ARR_DELAY_ANALYSIS.clip(lower=0)
df['CAUSE_REPORTED'] = df[CAUSES].notna().all(axis=1).astype('int8')
for c in CAUSES:
    df[c] = df[c].astype('float64')
df['LATE_AIRCRAFT_POSITIVE'] = df.LATE_AIRCRAFT_DELAY.gt(0).astype('int8')
csv(df.loc[df.TIME_ISSUE.eq(1), original_columns], 'quality_time_issue_rows')

validation = {
    'source_rows': n, 'cleaned_rows': len(df), 'rows_removed': 0,
    'raw_values_changed': 0, 'duplicates_before': checks['exact_duplicate_excess'], 'duplicates_after': checks['exact_duplicate_excess'],
    'arrival_missing_before': int(df.ARRIVAL_DELAY.isna().sum()), 'arrival_missing_after': int(df.ARRIVAL_DELAY.isna().sum()),
    'unresolved_airport_rows_preserved': int(df.GEO_ELIGIBLE.eq(0).sum()),
    'unknown_dimension_keys_added': 1, 'time_issue_rows_flagged': int(df.TIME_ISSUE.sum()),
    'cancelled_preserved': int(df.CANCELLED.sum()), 'diverted_preserved': int(df.DIVERTED.sum()),
    'extreme_arr_gt360_preserved': int(df.ARRIVAL_DELAY.gt(360).sum()),
    'date_invalid_after': int(df.DATE.isna().sum()), 'day_coverage_after': int(df.DATE.nunique()),
    'origin_fk_unmatched_after': int((~df.ORIGIN_KEY.isin(list(ap.IATA_CODE)+['__UNRESOLVED__'])).sum()),
    'destination_fk_unmatched_after': int((~df.DESTINATION_KEY.isin(list(ap.IATA_CODE)+['__UNRESOLVED__'])).sum()),
    'cause_minutes_equal_recorded_late_arrival_minutes': bool(df.loc[df.CAUSE_REPORTED.eq(1), CAUSES].sum(axis=1).eq(df.loc[df.CAUSE_REPORTED.eq(1), 'ARRIVAL_DELAY']).all()),
}
assert validation['source_rows'] == validation['cleaned_rows']
assert validation['date_invalid_after'] == validation['origin_fk_unmatched_after'] == validation['destination_fk_unmatched_after'] == 0
assert df.ON_TIME.sum()+df.DELAYED_15.sum() == df.ARR_ELIGIBLE.sum()
assert df.COMPLETED.sum()+df.CANCELLED.sum()+df.DIVERTED.sum() == n
assert validation['cause_minutes_equal_recorded_late_arrival_minutes']
write_json(REPORTS / 'cleaning_validation.json', validation)
gate = {'quality_status':'READY_WITH_WARNINGS', 'source_sha256':profile['source_sha256'], 'critical_issues_for_system_analysis':[],
    'scope':{'system_airline_time':'READY_WITH_WARNINGS: all 12 months', 'airport_route':'READY_WITH_WARNINGS: 11 resolved months only', 'full_year_named_airport_route':'NOT_READY: missing verified airport ID crosswalk', 'utc_aircraft_rotation':'NOT_READY: no airport timezone / actual date offsets', 'current_2026_operations':'NOT_READY: historical 2015 data'},
    'warnings':['486165 October flights have unresolved numeric airport codes; retain in global analysis, exclude from named geography analysis.', '2 temporal inconsistencies flagged, not guessed or overwritten.', 'Outcome-dependent cause missingness; never replace missing causes with zero in source data.', 'No passenger, cost, weather observation, crew, timezone or aircraft type tables.'],
    'missing_arrival_rate': float(df.ARRIVAL_DELAY.isna().mean()), 'arrival_completeness_completed':1.0, 'duplicates':0}
write_json(REPORTS / 'quality_gate.json', gate)
(REPORTS / 'data_quality_report.md').write_text(f'''# Data Quality Assessment

**Gate: READY WITH WARNINGS** cho phân tích hệ thống/hãng/thời gian; **NOT READY** cho xếp hạng sân bay/tuyến đủ 12 tháng có tên, phân tích rotation UTC hoặc suy diễn tình hình hiện tại. Kiểm định đã thực hiện trước EDA.

Nguồn: {n:,} dòng × 31 cột; 365 ngày năm 2015; airports: 322 dòng; airlines: 14 dòng. Không có duplicate toàn dòng hoặc khóa ghép; ngày, thứ, giờ HHMM và cờ trạng thái hợp lệ. HHMM=2400 là nửa đêm hợp lệ, không phải 24:00 trong cùng ngày.

| Issue | Affected Rows | % toàn bộ | Possible Explanation / Business Meaning | Analytical Risk | Cleaning Decision / Validation |
|---|---:|---:|---|---|---|
| Mã sân bay số tháng 10, cả hai đầu | 486165 | {486165/n*100:.4f} | Thay đổi cách mã hóa; chưa có crosswalk được xác minh | Tách một sân bay thành hai thực thể; sai xếp hạng | Giữ mã gốc, thêm khóa __UNRESOLVED__, GEO_ELIGIBLE=0; không đoán mã IATA; kiểm tra FK sau xử lý |
| ARRIVAL_DELAY thiếu | 105071 | {105071/n*100:.4f} | 89884 hủy + 15187 đổi hướng | Điền 0 sẽ tạo on-time giả | Giữ NULL; mẫu số ARR_ELIGIBLE; 100% chuyến hoàn tất có arrival delay |
| Mỗi cột nguyên nhân thiếu | 4755640 | {4755640/n*100:.4f} | Chỉ có nguyên nhân cho chuyến đến chậm >=15 phút | Không thể dùng như biến giải thích dự báo độc lập | Giữ NULL; tổng nguyên nhân khớp arrival delay trong từng dòng được ghi nhận |
| TAIL_NUMBER thiếu | 14721 | {14721/n*100:.4f} | Tất cả thuộc chuyến hủy | Xóa NULL làm mất gián đoạn thật | Giữ các chuyến; phân tích tail chỉ với tail hiện hữu |
| SCHEDULED_TIME thiếu | 6 | {6/n*100:.6f} | 5 hủy, 1 đổi hướng | Không thể suy ra đủ planned duration | Không điền; loại khỏi kiểm tra duration khi không đủ dữ liệu |
| Mâu thuẫn thời gian | 2 | {2/n*100:.6f} | Một chuyến F9 lệch identity 2 phút; một chuyến NK đã hủy có departure delay không khớp đồng hồ | Sai phân tích thời lượng/rotation | Gắn TIME_ISSUE=1, giữ nguồn; NK không thuộc mẫu số departure vì đã hủy; kiểm chứng sensitivity bỏ cả hai |
| Arrival delay >360 phút | 6089 | {6089/n*100:.4f} | Có thể là gián đoạn vận hành thực | Mean lệch đuôi phải | Giữ toàn bộ; so sánh <=360, median và p95/p99 |
| Arrival delay < -60 phút | 392 | {392/n*100:.4f} | Đến sớm hoặc lịch có buffer; không đủ bằng chứng gọi là lỗi | Mean che khuất phút chậm | Giữ; báo cáo thêm tổng phút chậm dương |
| Tọa độ thiếu | 3 sân bay | 0.9317% danh mục | Thiếu metadata | Map không đầy đủ | Giữ sân bay trong bảng/xếp hạng, không bịa tọa độ |

## Trước và sau xử lý

Không xóa dòng, không điền NULL, không sửa giá trị nguồn, không giảm duplicate vì trước xử lý không có. Bổ sung DATE, cờ chất lượng/eligibility, trạng thái, phân đoạn thời gian, khóa ngoại có thành viên chưa xác định và trường KPI. Missingness nguồn không giảm: đây là lựa chọn đúng với dữ liệu thiếu mang ý nghĩa vận hành. Số hàng được gắn cờ địa lý: 486165; thời gian: 2. Các cờ có thể chồng lấn. Mọi hủy/đổi hướng/ngoại lệ được giữ. Xem `cleaning_validation.json`, `data_profile.json` và các bảng `quality_*.csv` để kiểm tra số liệu đầy đủ.

## Độ tươi, đơn vị và múi giờ

Dữ liệu phủ 2015-01-01 đến 2015-12-31, đã khoảng 11 năm; không đại diện 2026. Dữ liệu nguồn không có provenance/metadata đơn vị đầy đủ: delay/time duration được diễn giải là phút theo ngữ nghĩa cột và kiểm tra identities. DISTANCE giả định mile theo định dạng BTS, không dùng cho kết luận định lượng kinh doanh. Giờ là local HHMM; không trừ trực tiếp giờ sân bay đi khỏi sân bay đến hoặc suy ra UTC. Không có dữ liệu type máy bay, hành khách, công suất, chi phí hay thời tiết đo thực tế.

## Tài liệu định nghĩa

[BTS technical directive #22](https://www.bts.gov/topics/airlines-and-airports/number-22-technical-directive-time-reporting-effective-jan-1-2013) giải thích HHMM/local time và mã hủy A/B/C/D. [BTS FAQ](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays) định nghĩa on-time <15 phút và các nhóm nguyên nhân. Tài liệu được dùng để diễn giải; không khẳng định provenance của ba tệp đã được xác thực độc lập.
''', encoding='utf-8')
print('Quality report + gate written. Beginning business analysis.', flush=True)

def aggregate(frame, keys):
    result = frame.groupby(keys, observed=True, dropna=False).agg(
        flights=('FLIGHT_ID','size'), completed=('COMPLETED','sum'), arrival_n=('ARR_ELIGIBLE','sum'),
        cancelled=('CANCELLED','sum'), diverted=('DIVERTED','sum'),
        on_time=('ON_TIME','sum'), delayed15=('DELAYED_15','sum'), severe=('SEVERE_60','sum'), disrupted=('DISRUPTED','sum'),
        avg_dep=('DEP_DELAY_ANALYSIS','mean'), median_dep=('DEP_DELAY_ANALYSIS','median'), dep_n=('DEP_DELAY_ANALYSIS','count'),
        avg_arr=('ARR_DELAY_ANALYSIS','mean'), median_arr=('ARR_DELAY_ANALYSIS','median'),
        positive_arr_minutes=('POSITIVE_ARR_MINUTES','sum'), late_aircraft_flights=('LATE_AIRCRAFT_POSITIVE','sum'),
        **{c.lower(): (c,'sum') for c in CAUSES}
    ).reset_index()
    for col, num, den in [('cancel_rate','cancelled','flights'),('divert_rate','diverted','flights'),('on_time_rate','on_time','arrival_n'),('on_time_scheduled_rate','on_time','flights'),('severe_rate','severe','arrival_n'),('disruption_rate','disrupted','flights')]:
        result[col] = result[num] / result[den].replace(0,np.nan)
    for num in ['positive_arr_minutes','severe','flights']:
        result[f'{num}_share'] = result[num] / result[num].sum()
    return result

df['_ALL'] = 'ALL'
overall = aggregate(df, ['_ALL'])
csv(overall, 'overall')
tables = {}
geo = df.loc[df.GEO_ELIGIBLE.eq(1)]
specs = [
    ('airline',df,['AIRLINE']), ('origin',geo,['ORIGIN_KEY']), ('destination',geo,['DESTINATION_KEY']),
    ('route',geo,['ROUTE']), ('hour',df,['DEP_HOUR']), ('time_band',df,['TIME_BAND']), ('weekday',df,['DAY_OF_WEEK']),
    ('month',df,['MONTH']), ('season',df,['SEASON']), ('daily',df,['DATE']),
    ('tail',df.loc[df.TAIL_NUMBER.notna()],['TAIL_NUMBER']),
    ('airport_hour',geo,['ORIGIN_KEY','DEP_HOUR']), ('airline_airport',geo,['AIRLINE','ORIGIN_KEY']),
    ('airport_month',geo,['ORIGIN_KEY','MONTH']), ('airline_month',df,['AIRLINE','MONTH']),
    ('route_time',geo,['ROUTE','TIME_BAND']), ('airline_route',geo,['AIRLINE','ROUTE']),
    ('airline_time',df,['AIRLINE','TIME_BAND']), ('month_time',df,['MONTH','TIME_BAND']),
    ('airport_time',geo,['ORIGIN_KEY','TIME_BAND']),
]
for name, frame, keys in specs:
    print(f'Aggregating {name}...', flush=True)
    tables[name] = aggregate(frame,keys)
    if name == 'airline':
        tables[name] = tables[name].merge(al.rename(columns={'IATA_CODE':'AIRLINE','AIRLINE':'AIRLINE_NAME'}),on='AIRLINE',how='left')
    csv(tables[name], name)

distributions=[]
for col in ['DEP_DELAY_ANALYSIS','ARR_DELAY_ANALYSIS']:
    s=df[col].dropna()
    distributions.append({'metric':col,**s.describe(percentiles=[.01,.25,.5,.75,.9,.95,.99]).to_dict(),'skew':float(s.skew())})
csv(pd.DataFrame(distributions), 'delay_distributions')
bands = pd.cut(df.ARR_DELAY_ANALYSIS, bins=[-np.inf,0,15,60,120,360,np.inf],right=False,labels=['early','0-14','15-59','60-119','120-359','360+'])
csv(bands.value_counts(sort=False).rename_axis('arrival_delay_band').reset_index(name='flights'), 'arrival_delay_bands')
cause_totals = df[CAUSES].sum().rename_axis('cause').reset_index(name='reported_minutes')
cause_totals['share_reported_minutes'] = cause_totals.reported_minutes/cause_totals.reported_minutes.sum()
csv(cause_totals,'cause_totals')
csv(df.loc[df.CANCELLED.eq(1)].groupby('CANCELLATION_REASON', observed=True).size().rename_axis('reason').reset_index(name='flights'),'cancellation_causes')

sens=[]
for name,mask in [('all',df.ARR_ELIGIBLE.eq(1)),('arrival_le360',df.ARR_ELIGIBLE.eq(1)&df.ARR_DELAY_ANALYSIS.le(360)),('exclude_october',df.GEO_ELIGIBLE.eq(1)&df.ARR_ELIGIBLE.eq(1)),('exclude_time_issues',df.ARR_ELIGIBLE.eq(1)&df.TIME_ISSUE.eq(0))]:
    s=df.loc[mask,'ARR_DELAY_ANALYSIS']
    sens.append({'scenario':name,'n':len(s),'avg_arr':s.mean(),'median_arr':s.median(),'p95_arr':s.quantile(.95),'severe_rate':s.ge(60).mean(),'positive_minutes':s.clip(lower=0).sum()})
csv(pd.DataFrame(sens),'sensitivity')
extreme = df.ARR_DELAY_ANALYSIS.gt(360)
write_json(REPORTS/'analysis_summary.json',{
    'overall':overall.drop(columns='_ALL').iloc[0].to_dict(), 'geographic_flights':len(geo),
    'extreme_arrivals':int(extreme.sum()),'extreme_positive_minutes_share':float(df.loc[extreme,'POSITIVE_ARR_MINUTES'].sum()/df.POSITIVE_ARR_MINUTES.sum()),
    'cause_reported_flights':int(df.CAUSE_REPORTED.sum()),'reported_cause_minutes':float(cause_totals.reported_minutes.sum()),
    'reported_causes_share_positive_arrival_minutes':float(cause_totals.reported_minutes.sum()/df.POSITIVE_ARR_MINUTES.sum()),
})

# Matched early/evening contrasts: common strata, minimum 30 arrivals per band,
# equal stratum weights proportional to min(n_early,n_evening). Descriptive only.
for label, strata in [('airline_origin_month',['AIRLINE','ORIGIN_KEY','MONTH']),('route_month',['ROUTE','MONTH'])]:
    g=geo.loc[geo.ARR_ELIGIBLE.eq(1)&geo.TIME_BAND.isin(['06-11','17-21'])].groupby(strata+['TIME_BAND'],observed=True).agg(n=('ARR_DELAY_ANALYSIS','count'),mean=('ARR_DELAY_ANALYSIS','mean'),severe=('SEVERE_60','mean')).reset_index()
    pivot=g.pivot(index=strata,columns='TIME_BAND',values=['n','mean','severe'])
    pivot=pivot.loc[(pivot['n']['06-11']>=30)&(pivot['n']['17-21']>=30)].copy()
    weights=np.minimum(pivot['n']['06-11'],pivot['n']['17-21'])
    effects=pd.DataFrame(index=pivot.index)
    effects['early_n']=pivot['n']['06-11']; effects['evening_n']=pivot['n']['17-21']; effects['weight']=weights
    effects['mean_difference']=pivot['mean']['17-21']-pivot['mean']['06-11']
    effects['severe_rate_difference']=pivot['severe']['17-21']-pivot['severe']['06-11']
    csv(effects.reset_index(),f'matched_{label}')
    write_json(REPORTS/f'matched_{label}.json',{'strata':len(pivot),'early_flights':int(effects.early_n.sum()),'evening_flights':int(effects.evening_n.sum()),'weighted_mean_difference':float(np.average(effects.mean_difference,weights=weights)), 'weighted_severe_rate_difference':float(np.average(effects.severe_rate_difference,weights=weights)), 'strata_with_positive_mean_difference_share':float(effects.mean_difference.gt(0).mean())})

# Pareto contribution with documented geography scope.
for name in ['origin','route','airline_airport']:
    rank=tables[name].sort_values('positive_arr_minutes',ascending=False).copy()
    rank['rank']=np.arange(1,len(rank)+1)
    rank['cumulative_minutes_share']=rank.positive_arr_minutes.cumsum()/rank.positive_arr_minutes.sum()
    csv(rank,f'pareto_{name}')

print('Writing cleaned data in chunks (raw columns preserved)...',flush=True)
df.drop(columns='_ALL',inplace=True)
# Deterministic gzip header, no timestamp; %.0f preserves the integer raw values.
df.to_csv(PROCESSED/'flights_cleaned.csv.gz',index=False,compression={'method':'gzip','compresslevel':1,'mtime':0},float_format='%.0f',date_format='%Y-%m-%d',chunksize=100000)
ap_out=pd.concat([ap,pd.DataFrame([{'IATA_CODE':'__UNRESOLVED__','AIRPORT':'Unresolved airport code','CITY':'Unknown','STATE':'Unknown','COUNTRY':'Unknown'}])],ignore_index=True)
ap_out.to_csv(PROCESSED/'dim_airport.csv',index=False,encoding='utf-8-sig')
al.to_csv(PROCESSED/'dim_airline.csv',index=False,encoding='utf-8-sig')
cal=pd.DataFrame({'DATE':pd.date_range(df.DATE.min(),df.DATE.max())})
cal['YEAR']=cal.DATE.dt.year;cal['MONTH']=cal.DATE.dt.month;cal['DAY_OF_WEEK']=cal.DATE.dt.dayofweek+1
cal.to_csv(PROCESSED/'dim_date.csv',index=False,date_format='%Y-%m-%d')
pd.DataFrame({'DEP_HOUR':range(24)}).to_csv(PROCESSED/'dim_hour.csv',index=False)
print('Analysis and cleaned data export complete.',flush=True)
