"""Create shareable figures, business report, and a concrete Power BI story."""
from common import *
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

require_quality_gate()

FIG=REPORTS/'figures'; FIG.mkdir(exist_ok=True)
def table(name): return pd.read_csv(TABLES/f'{name}.csv')
def md(frame):
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))
def fmt(n): return f'{n:,.0f}'
def pct(n): return f'{n*100:.2f}%'
def save(name):
    plt.savefig(FIG/f'{name}.png',dpi=170,bbox_inches='tight');plt.close()

plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.titlesize':12})
o=table('overall').iloc[0]; h=table('hour'); m=table('month'); a=table('airline')
orig=table('origin'); dest=table('destination'); routes=table('route'); causes=table('cause_totals'); canc=table('cancellation_causes')
tb=table('time_band').set_index('TIME_BAND'); early=tb.loc['06-11']; evening=tb.loc['17-21']
matched=json.loads((REPORTS/'matched_airline_origin_month.json').read_text())
robust=json.loads((REPORTS/'robustness_summary.json').read_text())
summary=json.loads((REPORTS/'analysis_summary.json').read_text())
val=json.loads((REPORTS/'cleaning_validation.json').read_text())

fig,ax=plt.subplots(1,2,figsize=(12,4.3))
ax[0].plot(h.DEP_HOUR,h.avg_arr,'o-',label='Mean arrival delay',color='#167a94')
ax[0].plot(h.DEP_HOUR,h.median_arr,'--',label='Median',color='#6b7280')
ax[0].axhline(0,color='#ddd');ax[0].set(xlabel='Scheduled departure hour (local)',ylabel='Minutes',title='Mean and median show different parts of the story');ax[0].legend()
ax[1].plot(h.DEP_HOUR,h.severe_rate,'o-',color='#c45138',label='Arrival delay >=60 min')
ax[1].yaxis.set_major_formatter(PercentFormatter(1));ax[1].set(xlabel='Scheduled departure hour (local)',title='Severe-delay risk increases through the day');ax[1].legend()
fig.suptitle('2015, all 12 months | arrival metrics exclude cancellations/diversions');fig.tight_layout();save('time_of_day')

fig,ax=plt.subplots(figsize=(10,4.5))
ax.plot(m.MONTH,m.severe_rate,'o-',label='Severe / completed arrivals',color='#c45138');ax.plot(m.MONTH,m.cancel_rate,'o-',label='Cancelled / scheduled flights',color='#167a94')
ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set(xticks=range(1,13),xlabel='Month (2015)',title='February cancellation risk and June severe delays are different problems');ax.legend();save('monthly_disruptions')

fig,ax=plt.subplots(figsize=(10,5))
eligible=orig[orig.flights.ge(10000)].copy()
ax.scatter(eligible.flights,eligible.severe_rate,s=45,alpha=.65,color='#167a94')
for code in ['ORD','LGA','ATL','LAX','JFK','EWR','DFW']:
    row=orig[orig.ORIGIN_KEY.eq(code)].iloc[0];ax.annotate(code,(row.flights,row.severe_rate),xytext=(4,4),textcoords='offset points')
ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set(xlabel='Scheduled departures (11 resolved months)',ylabel='Arrival severe-delay rate',title='Prioritize both risk and flight volume — not a single airport rank');save('airport_risk_volume')

fig,ax=plt.subplots(1,2,figsize=(12,4.5))
labels={'LATE_AIRCRAFT_DELAY':'Late aircraft','AIRLINE_DELAY':'Airline','AIR_SYSTEM_DELAY':'NAS','WEATHER_DELAY':'Weather','SECURITY_DELAY':'Security'}
c=causes.sort_values('share_reported_minutes');ax[0].barh(c.cause.map(labels),c.share_reported_minutes,color='#167a94');ax[0].xaxis.set_major_formatter(PercentFormatter(1));ax[0].set_title('Share of 62.65m REPORTED cause minutes')
cc=canc.assign(share=canc.flights/canc.flights.sum()).sort_values('share');ax[1].barh(cc.reason.map({'A':'Airline','B':'Weather','C':'NAS','D':'Security'}),cc.share,color='#c45138');ax[1].xaxis.set_major_formatter(PercentFormatter(1));ax[1].set_title('Share of 89,884 recorded cancellations')
fig.suptitle('Recorded categories are not independently verified root causes');fig.tight_layout();save('recorded_causes')

fig,ax=plt.subplots(figsize=(10,4.5))
bands=table('arrival_delay_bands');ax.bar(bands.arrival_delay_band,bands.flights/1e6,color=['#167a94','#499ca9','#e1ad52','#db8150','#c45138','#933441']);ax.set(xlabel='Arrival delay band (minutes)',ylabel='Million flights',title='Arrival delay: mean 4.41 min, median -5 min, p95 66 min');save('delay_distribution')

air=a.sort_values('severe_rate',ascending=False)[['AIRLINE','flights','arrival_n','avg_arr','median_arr','severe_rate','cancel_rate']].copy()
for c in ['flights','arrival_n']:air[c]=air[c].map(fmt)
for c in ['avg_arr','median_arr']:air[c]=air[c].map(lambda x:f'{x:.2f}')
for c in ['severe_rate','cancel_rate']:air[c]=air[c].map(pct)
route_table=routes[routes.flights.ge(1000)].sort_values('severe_rate',ascending=False).head(8)[['ROUTE','flights','arrival_n','severe_rate','cancel_rate','median_arr']].copy()
for c in ['severe_rate','cancel_rate']:route_table[c]=route_table[c].map(pct)
pareto=table('pareto_origin');top10=pareto.head(10);pr=table('pareto_route');top20=pr.head(math.ceil(len(pr)*.2))
ordrow=orig[orig.ORIGIN_KEY.eq('ORD')].iloc[0];lga=orig[orig.ORIGIN_KEY.eq('LGA')].iloc[0]
nk=a[a.AIRLINE.eq('NK')].iloc[0];mq=a[a.AIRLINE.eq('MQ')].iloc[0]
weather=canc[canc.reason.eq('B')].flights.iloc[0]/canc.flights.sum()
late_share=causes[causes.cause.eq('LATE_AIRCRAFT_DELAY')].share_reported_minutes.iloc[0]

report=f'''# Aviation Operations — Client Analysis Report

Ngày hoàn tất: 12/11/2026. Kỳ dữ liệu: **01/01–31/12/2015**. Ngôn ngữ báo cáo: tiếng Việt. Phân tích toàn bộ dữ liệu, không lấy mẫu. Không sửa `AGENTS.md` hoặc dữ liệu nguồn.

# Executive Summary

Hiệu suất trung bình tạo cảm giác khá ổn: đến chậm **{o.avg_arr:.2f} phút**, median **{o.median_arr:.0f} phút** (đến sớm). Tuy nhiên có **{fmt(o.severe)} chuyến đến chậm từ 60 phút**, **{fmt(o.cancelled)} chuyến hủy** và **{fmt(o.diverted)} chuyến đổi hướng. Tổng **{fmt(o.disrupted)} chuyến**, tương đương **{pct(o.disruption_rate)}** lịch bay, thuộc ít nhất một trong ba nhóm gián đoạn này.

Năm phát hiện chính:

1. **Rủi ro tăng rõ vào cuối ngày:** 17–21h có severe-delay rate {pct(evening.severe_rate)} so với {pct(early.severe_rate)} lúc 6–11h; chênh lệch vẫn còn khi so cùng hãng–sân bay–tháng.
2. **Ưu tiên theo cả quy mô và tỷ lệ:** ORD có nhiều phút chậm dương nhất trong các sân bay đi nhận diện được; LGA có tỷ lệ chậm nặng {pct(lga.severe_rate)} và hủy {pct(lga.cancel_rate)} trong nhóm sân bay >=10.000 chuyến. Phạm vi địa lý chỉ gồm 11 tháng.
3. **Hủy chuyến và chậm nặng có mùa khác nhau:** tháng 2 có tỷ lệ hủy 4,78%, tháng 6 có tỷ lệ chậm nặng 8,15%. Weather là mã của {pct(weather)} chuyến hủy; không thể dùng tỷ trọng weather-delay minutes nhỏ để kết luận thời tiết không quan trọng.
4. **Cách xếp hạng hãng thay đổi quyết định:** NK cao nhất về tỷ lệ chậm nặng ({pct(nk.severe_rate)}); MQ cao nhất về hủy ({pct(mq.cancel_rate)}). MQ có chênh lệch nhỏ trong tập tuyến–tháng–nhóm giờ đủ điều kiện; cần tách tác động chọn tập chuyến khỏi chuẩn hóa cơ cấu và kiểm tra theo từng giờ trước khi quy kết.
5. **Mean không phản ánh trải nghiệm phần đuôi:** p95 arrival delay 66 phút, p99 167 phút, trong khi median đến sớm 5 phút. Ngoại lệ >360 phút chỉ chiếm khoảng 0,11% chuyến hoàn tất nhưng tạo {pct(summary['extreme_positive_minutes_share'])} phút chậm dương.

Ưu tiên quản trị: xác nhận các mẫu này bằng dữ liệu mới; kiểm tra lịch quay đầu/nguồn lực phục hồi cuối ngày tại ORD và LGA; tách kế hoạch ứng phó hủy chuyến mùa đông khỏi xử lý chậm dây chuyền mùa hè; giám sát kết quả bằng rate, volume và tail metrics cùng lúc. Đây là khuyến nghị điều tra/pilot có bằng chứng lịch sử, không phải chỉ đạo thay lịch hiện tại dựa trên dữ liệu 2015.

# Business Problem

Câu hỏi trong prompt vẫn là placeholder. Giả định đã dùng: **điều tra chậm chuyến và gián đoạn, tìm nơi/thời điểm/phân khúc bị ảnh hưởng, đánh giá driver được ghi nhận và đề xuất ưu tiên cải thiện độ tin cậy**. Quyết định cần hỗ trợ là phân bổ năng lực điều tra và phục hồi vận hành, không dự báo từng chuyến hoặc tối ưu lợi nhuận khi chưa có chi phí.

# Data Description

| Tệp | Quy mô | Grain / vai trò |
|---|---:|---|
| flights.csv | 5.819.079 × 31 | Một chuyến theo lịch, một ngày, một chặng |
| airports.csv | 322 × 7 | Một IATA airport code; tên/vị trí |
| airlines.csv | 14 × 2 | Một airline code; tên |

Đủ 365 ngày, 12 tháng năm 2015; không có ngày trống. Không có duplicate trên khóa ngày + hãng + số chuyến + sân bay đi + sân bay đến + giờ khởi hành theo lịch. `FLIGHT_NUMBER` riêng lẻ không phải primary key. `FLIGHT_ID` là surrogate key theo thứ tự dòng nguồn, không phải mã nghiệp vụ ổn định giữa các lần thay nguồn. Airport và airline là dimension many-to-one; hai vai trò airport phải được phân biệt.

Sân bay/tuyến: **{fmt(summary['geographic_flights'])} chuyến / 11 tháng**. Tháng 10 có 486.165 chuyến dùng mã sân bay số ở cả hai đầu. Không có crosswalk đã kiểm chứng trong repo; không đoán IATA từ tên hoặc tần suất. Các chuyến này vẫn có trong KPI hãng/toàn hệ thống/thời gian.

Xem [data dictionary](data_dictionary.md) và [bảng schema/missingness](tables/quality_missingness.csv). Cột thời gian lịch là local HHMM, delay/duration là phút theo diễn giải định dạng và identities được kiểm tra. Đơn vị DISTANCE chưa có metadata nguồn xác thực; không dùng để đưa ra kết luận kinh doanh. Không có timezone/actual date offsets, aircraft type, hành khách, crew, maintenance, chi phí, thời tiết đo thực hay công suất sân bay.

# Data Quality Assessment

**READY WITH WARNINGS** cho phân tích hệ thống/hãng/thời gian. **NOT READY** cho xếp hạng tên sân bay/tuyến đủ 12 tháng hoặc mô hình quay vòng máy bay theo UTC. Chỉ phân tích địa lý trên phạm vi nhận diện được. Báo cáo chất lượng và quality gate được ghi trước EDA.

Không có trùng dòng, trùng khóa ghép, ngày/weekday lỗi, giờ HHMM sai, airline ngoài danh mục, negative duration/distance hoặc status không hợp lệ. Có 2 dòng mâu thuẫn thời gian được gắn cờ; 3 sân bay thiếu tọa độ; 6 dòng thiếu scheduled duration, tất cả thuộc hủy/đổi hướng.

105.071 giá trị ARRIVAL_DELAY thiếu khớp chính xác 89.884 hủy + 15.187 đổi hướng. Các chuyến hoàn tất có arrival delay đầy đủ. 4.755.640 NULL ở **mỗi** cột nguyên nhân là thiếu theo điều kiện báo cáo, không phải 81,72% chuyến bị mất nguyên nhân ngẫu nhiên. Tất cả 1.063.439 chuyến arrival delay >=15 có đủ năm nguyên nhân; tổng các nguyên nhân khớp arrival delay từng dòng.

Xem [đánh giá đầy đủ từng vấn đề, số dòng, rủi ro và quyết định](data_quality_report.md), [gate](quality_gate.json) và [profile](data_profile.json).

# Cleaning Decisions

- Giữ nguyên mọi dòng và giá trị nguồn; không drop NULL/duplicate/outlier hoặc impute trung bình.
- Thêm DATE từ năm/tháng/ngày, kiểm chứng đủ 365 ngày; giờ lịch dùng DEP_HOUR và TIME_BAND. HHMM=2400 hợp lệ; không thay bằng timestamp cùng ngày hoặc tự suy UTC.
- Thêm khóa airport `__UNRESOLVED__` cho tháng 10; giữ mã gốc; cờ GEO_ELIGIBLE quyết định phạm vi địa lý. FK tới dimension xử lý có 0 giá trị không nối được, nhưng điều này không đồng nghĩa đã xác định tên sân bay tháng 10.
- Thêm TIME_ISSUE cho 2 dòng. Chuyến NK 1012 ngày 24/12 đã hủy có departure clock không khớp delay; vốn không được đưa vào mẫu số departure. Chuyến F9 1360 ngày 04/07 có duration identity lệch 2 phút, giữ arrival delay vì khớp giờ đến; không dùng để suy rotation. Sensitivity bỏ dòng này không thay đổi kết luận.
- Thêm ARR_ELIGIBLE/ON_TIME/SEVERE_60/DISRUPTED và delay analysis. ARR_DELAY_ANALYSIS chỉ chứa chuyến hoàn tất; DEP_DELAY_ANALYSIS loại hủy và departure clock lỗi, có giữ chuyến đổi hướng đã khởi hành.

Sau xử lý: **5.819.079 dòng**, xóa 0; missingness nguồn không đổi; duplicates trước/sau đều 0; toàn bộ hủy/đổi hướng và 6.089 arrival delay >360 phút được bảo toàn. Đó là kết quả có chủ đích, không phải cleaning thất bại. Xem [validation](cleaning_validation.json); dữ liệu xuất được kiểm tra lại độc lập bằng `verify_outputs.py`.

# Analytical Approach

Đo KPI tổng thể, distribution và percentiles; phân đoạn theo hãng, hai đầu sân bay, tuyến, giờ lịch, thứ, tháng/mùa, tail; xem tương tác airport × hour, airline × airport, route × time và airline × route. Xếp hạng sân bay chỉ khi >=10.000 chuyến, tuyến >=1.000 chuyến; mọi bảng giữ sample size. Ngưỡng là quy tắc tránh nhóm rất nhỏ, không bảo đảm loại hết nhiễu.

Chậm nặng được định nghĩa **arrival delay >=60 phút** để phục vụ điều hành; không gán là chuẩn BTS. On-time **<15 phút** theo [định nghĩa BTS](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays). On-time/severe có mẫu số chuyến hoàn tất có delay; cancellation/diversion/disruption dùng toàn bộ lịch. Disruption là hợp không trùng của hủy, đổi hướng hoặc severe arrival.

Đây là mô tả toàn bộ tệp và chuẩn hóa phân tầng; không dùng p-value để biến chênh lệch nhỏ thành kết luận quan trọng. Không có thiết kế nhân quả. Không ép ML vì câu hỏi mang tính mô tả/chẩn đoán và các cause fields chỉ có sau kết quả, dễ gây leakage.

# Key Findings

| KPI | Giá trị | Mẫu số / phạm vi |
|---|---:|---|
| Total flights | {fmt(o.flights)} | Toàn lịch, 12 tháng |
| Completed / arrival eligible | {fmt(o.arrival_n)} | Không hủy/không đổi hướng |
| On-time arrival | {pct(o.on_time_rate)} | {fmt(o.on_time)} / {fmt(o.arrival_n)} |
| On-time trên toàn lịch | {pct(o.on_time_scheduled_rate)} | {fmt(o.on_time)} / {fmt(o.flights)} |
| Cancellation / diversion | {pct(o.cancel_rate)} / {pct(o.divert_rate)} | Toàn lịch |
| Severe arrival >=60 | {pct(o.severe_rate)} | {fmt(o.severe)} / {fmt(o.arrival_n)} |
| Any major disruption | {pct(o.disruption_rate)} | {fmt(o.disrupted)} / toàn lịch |
| Departure mean / median | {o.avg_dep:.2f} / {o.median_dep:.0f} phút | {fmt(o.dep_n)} không hủy, delay hợp lệ |
| Arrival mean / median | {o.avg_arr:.2f} / {o.median_arr:.0f} phút | Completed |
| Arrival p90 / p95 / p99 | 34 / 66 / 167 phút | Completed |
| Arrival min / max / std | -87 / 1.971 / 39,27 phút | Completed |
| Positive arrival minutes | {fmt(o.positive_arr_minutes)} | Không bù trừ bằng phút đến sớm |

![Phân phối chậm đến](figures/delay_distribution.png)

## Airline comparison — descriptive, chưa điều chỉnh cơ cấu

{md(air)}

US chỉ xuất hiện tháng 1–6; không diễn giải thay đổi số chuyến giữa AA/US là tăng trưởng hữu cơ hoặc suy giảm vận hành. Hãng khác nhau về sân bay/tuyến/khung giờ; xem kiểm chứng ở insight 4.

## Route comparison — 11 tháng, threshold >=1.000 chuyến

{md(route_table)}

Tuyến ORD → JFK có severe rate 13,59% trên 1.538 chuyến hoàn tất, nhưng không có nghĩa đây là tuyến gây tổng tổn thất lớn nhất. Theo tổng phút chậm dương, SFO → LAX dẫn đầu (222.421 phút; 13.744 chuyến theo lịch), cho thấy rate và volume trả lời hai câu hỏi khác nhau.

# High-Value Insights

## 1. Cuối ngày là phân khúc cần điều tra trước; khác biệt không chỉ do cơ cấu hãng/tháng

**Observation / Evidence:** Nhóm 6–11h có {fmt(early.flights)} chuyến theo lịch ({fmt(early.arrival_n)} hoàn tất); mean arrival {early.avg_arr:.2f} phút, median -7, severe {pct(early.severe_rate)}. Nhóm 17–21h có {fmt(evening.flights)} chuyến ({fmt(evening.arrival_n)} hoàn tất); mean {evening.avg_arr:.2f}, median -2, severe {pct(evening.severe_rate)} — khoảng {evening.severe_rate/early.severe_rate:.2f} lần. Tỷ lệ gián đoạn gồm cả hủy/đổi hướng cũng tăng từ {pct(early.disruption_rate)} lên {pct(evening.disruption_rate)}.

**Pattern / Context:** Mean buổi tối cao hơn ở 12/12 tháng và 14/14 hãng. Trong {matched['strata']:,} phân tầng chung hãng × sân bay đi × tháng, mỗi nhóm giờ có >=30 arrival, chuẩn hóa bằng trọng số min(n_sáng,n_tối), chênh lệch mean vẫn **{matched['weighted_mean_difference']:.2f} phút**, severe **{matched['weighted_severe_rate_difference']*100:.2f} điểm phần trăm**. Có {fmt(matched['early_flights'])} arrival sáng và {fmt(matched['evening_flights'])} arrival tối trong phần so sánh này; {pct(matched['strata_with_positive_mean_difference_share'])} strata cùng chiều. So cùng tuyến × tháng cũng còn chênh lệch 10,52 phút. Đây là hai kiểm chứng riêng, không phải mô hình đã đồng thời kiểm soát mọi yếu tố.

**Challenge:** Bỏ arrival delay >360 phút vẫn có mean -0,49 phút sáng và 9,10 phút tối; median cũng dịch từ -7 sang -2. Điều này bác bỏ giải thích đơn giản rằng vài chuyến cực đoan tạo ra toàn bộ chênh lệch. Khung giờ khác nhau còn route mix/crew/demand; kết quả vẫn là association.

**Likely Driver:** Late-aircraft là nhóm phút nguyên nhân lớn nhất và tăng tỷ trọng vào cuối ngày, phù hợp giả thuyết chậm dây chuyền. Không chứng minh rotation cụ thể vì thiếu UTC/actual flight-date offsets và dữ liệu quay đầu.

**Business Impact / Action:** Chậm cuối ngày làm tăng nhu cầu phục hồi lịch, rủi ro nối chuyến và gián đoạn tổ bay; chưa lượng hóa được hành khách/chi phí. Sau khi xác nhận bằng kỳ dữ liệu mới, thử review rotation/buffer/khả năng phục hồi 17–21h ở các phân khúc ưu tiên. Theo dõi severe/disruption rate và p95, không chỉ mean.

**Bài học:** Vì tỷ lệ được so cùng hãng/sân bay/tháng và còn sau bỏ đuôi cực đoan, kết luận mạnh hơn so với việc vẽ một đường mean theo giờ. Câu hỏi kế tiếp là rotation nào có ít recovery buffer, không phải mặc định mọi sân bay đều thiếu năng lực.

![Thời điểm trong ngày](figures/time_of_day.png)

## 2. ORD nổi bật về quy mô, LGA về rủi ro; không có bằng chứng một nhóm nhỏ sân bay gây gần hết vấn đề

**Evidence:** Trong 11 tháng nhận diện được, ORD có {fmt(ordrow.flights)} chuyến, {fmt(ordrow.positive_arr_minutes)} phút chậm dương (6,86% tổng phạm vi địa lý), severe rate {pct(ordrow.severe_rate)}. LGA có {fmt(lga.flights)} chuyến, {fmt(lga.arrival_n)} arrival, severe {pct(lga.severe_rate)}, hủy {pct(lga.cancel_rate)}, disruption {pct(lga.disruption_rate)}. LGA đến cũng có severe 9,44% trên 94.527 arrival.

**Pattern:** Ở LGA, disruption tăng từ 8,51% sáng lên 19,64% tối; mean arrival từ -1,30 lên 14,85 phút. ORD tăng từ 8,20% lên 14,80% disruption. Có tương tác địa điểm × giờ, không nên áp một biện pháp đồng loạt cả ngày.

**Challenge / Context:** Top 10 sân bay theo phút chậm tạo {pct(top10.positive_arr_minutes.sum()/pareto.positive_arr_minutes.sum())} phút chậm nhưng cũng chiếm {pct(top10.flights.sum()/pareto.flights.sum())} chuyến. Đây chủ yếu là quy mô lớn, không phải quy luật 80/20 mạnh. Top 20% tuyến theo phút chậm chiếm 61,30% severe và 56,67% chuyến trong phạm vi địa lý. Tuyến volume cao cần ưu tiên khác tuyến rate cao. Airport-origin metrics là kết quả của các chuyến đi từ đó, **không tự chứng minh sân bay đi là nơi phát sinh nguyên nhân**.

**Business Impact / Action:** ORD phù hợp ưu tiên năng lực điều tra tác động lớn; LGA phù hợp kiểm tra độ tin cậy cuối ngày và hủy. Đào sâu hãng × airport × khung giờ trước khi kết luận cần tăng công suất sân bay. Chỉ dùng các kết quả này như danh sách ứng viên lịch sử vì tháng 10 chưa được nối mã.

**Bài học:** Một ranking duy nhất trộn rate và volume sẽ trả lời sai quyết định phân bổ nguồn lực. Luôn đặt cạnh nhau N, rate và contribution.

![Rủi ro và quy mô sân bay](figures/airport_risk_volume.png)

## 3. Kế hoạch ứng phó hủy chuyến cần khác kế hoạch giảm chậm nặng

**Evidence:** Tháng 2 có 20.517/429.191 chuyến bị hủy (**4,78%**); tháng 6 chỉ 1,81% hủy nhưng severe arrival cao nhất **8,15%** (40.171/492.847 arrival). Tháng 10 có severe rate 3,36%, cancellation 0,50%; tháng này được giữ trong so sánh toàn hệ thống.

**Driver / Context:** Mã hủy B-weather ghi nhận **48.851/89.884 ({pct(weather)})**; A-airline 25.262; C-NAS 15.749; D-security 22. Đây là nhóm nguyên nhân do báo cáo vận hành ghi nhận. Nhóm WEATHER_DELAY riêng chỉ chiếm 4,95% **phút nguyên nhân của chuyến đến chậm >=15**. Mẫu số và loại gián đoạn khác nhau; NAS hoặc late-aircraft cũng có thể chứa tác động thời tiết gián tiếp theo [BTS FAQ](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays).

**Challenge:** Phân tích median, severity và cancellation song song tránh thiên lệch chỉ nhìn chuyến còn hoạt động. Không gắn tháng 2 với một bão cụ thể khi không có weather observation/event log. Một năm chưa đủ chứng minh quy luật mùa lặp lại qua nhiều năm.

**Business Impact / Action:** Tách hai playbook: khả năng quyết định hủy/phục hồi/đổi hành trình trong các đợt gián đoạn lớn; và kiểm tra chậm dây chuyền để bảo vệ lịch còn khai thác. Đo cancel rate, disruption rate, p95 và thời gian phục hồi, bổ sung passenger/connection data để đo hậu quả thực.

**Bài học:** Category cause không có cùng độ phủ với dữ liệu gián đoạn; một cột weather nhỏ không chứng minh thời tiết là yếu tố thứ yếu.

![Hủy và chậm nặng theo tháng](figures/monthly_disruptions.png)

## 4. NK có rủi ro chậm nặng còn sau so cùng tuyến; MQ cần chú trọng hủy và cơ cấu khai thác

**Evidence:** NK: {fmt(nk.flights)} chuyến, {fmt(nk.arrival_n)} arrival, severe {pct(nk.severe_rate)}. MQ: {fmt(mq.flights)} chuyến, hủy {pct(mq.cancel_rate)}, severe {pct(mq.severe_rate)}. Chỉ xét delay của chuyến hoàn tất sẽ bỏ qua nhóm hủy lớn của MQ.

**Challenge:** So cùng tuyến đi–đến × tháng × nhóm giờ, mỗi carrier và nhóm hãng khác đều >=10 arrival, dùng min(n_carrier,n_other) làm trọng số. NK có {robust['NK_matched']['strata']:,} strata, {fmt(robust['NK_matched']['carrier_n'])} arrival NK và {fmt(robust['NK_matched']['other_n'])} comparator; NK còn cao hơn **{robust['NK_matched']['severe_gap']*100:.2f} điểm % severe**, **{robust['NK_matched']['mean_gap']:.2f} phút mean**. MQ trong {robust['MQ_matched']['strata']:,} strata chỉ cao hơn **{robust['MQ_matched']['severe_gap']*100:.2f} điểm % severe**, mean còn thấp hơn **{abs(robust['MQ_matched']['mean_gap']):.2f} phút**. Mức thay đổi so với aggregate bao gồm cả chọn tập chuyến và chuẩn hóa; không thể gán toàn bộ cho cơ cấu tuyến/thời gian. Xem [kiểm chứng bổ sung](skill_review/analysis_improvement_review.md) về độ phủ và độ nhạy theo từng giờ.

**Limitation:** Comparator là nhóm hãng còn lại gộp; chỉ có common-support subset, loại tháng 10; BAND OTHER gộp ngoài sáng/tối. Đây không phải causal effect hoặc chứng minh toàn bộ hoạt động của NK yếu. Kiểm chứng MQ chỉ điều chỉnh chậm ở chuyến hoàn tất, **chưa điều chỉnh chênh lệch cancellation**.

**Business Impact / Action:** NK là ứng viên review độ tin cậy theo tuyến cụ thể; MQ là ứng viên review hủy/khôi phục lịch và lý do hủy theo airport/tháng. Không quy vấn đề cho chất lượng kỹ thuật tàu bay từ tail ranking: N219FR có severe 13,94% trên 1.306 arrival nhưng chưa kiểm soát lịch tuyến, cũng không có maintenance logs.

**Bài học:** Khi xếp hạng thay đổi sau segmentation, nên thay đổi câu hỏi điều tra. Hãng có mean cao không mặc nhiên là nguyên nhân; cancellation và route mix phải được kiểm tra.

## 5. Mức trung bình thấp che khuất phần đuôi, nhưng vài ngoại lệ không giải thích hết vấn đề

**Evidence:** Mean arrival 4,41 phút, median -5; p90 34, p95 66, p99 167; max 1.971. Có 6.089 chuyến >360 phút, khoảng 0,11% arrival, đóng góp 4,64% phút chậm dương. Loại nhóm này, mean giảm xuống 3,85 phút và severe rate còn 5,60%, so với 5,70% ban đầu.

**Interpretation:** Median cho biết chuyến điển hình; p95 và severe rate phản ánh phần trải nghiệm kém. Cả hai cần thiết. Giá trị rất lớn có ý nghĩa về phục hồi vận hành, không nên loại để làm KPI đẹp. Tổng phút chậm dương là 69,10 triệu, trong khi mean có dấu đã được bù trừ bởi các chuyến đến sớm.

**Business Impact / Action:** Có nhiều chuyến cần hỗ trợ phục hồi dù chuyến điển hình vẫn sớm; giám sát severe/disruption, p95/p99 cùng volume. Phút chậm là flight-minutes cộng qua các chuyến, không phải passenger-minutes, giờ tổ bay hay số giờ tàu bay thực mất; chậm dây chuyền có thể được ghi ở nhiều chặng.

**Bài học:** Không chọn mean hoặc median làm một “sự thật duy nhất”. Đặt chúng cạnh tỷ lệ sự kiện nghiêm trọng và tail percentiles để thấy cả tần suất lẫn mức độ.

# Root-Cause Analysis

| Hypothesis | Evidence strength | Kết quả / giới hạn |
|---|---|---|
| Late aircraft / propagation | Strong Evidence cho nhóm nguyên nhân ghi nhận; Moderate Evidence cho cơ chế lan truyền | 24.961.931 phút, 39,84% tổng phút nguyên nhân; pattern tối bền theo phân tầng. Thiếu linked rotation/UTC để kiểm chứng từng chuỗi |
| Airline operations | Strong Evidence cho nhóm báo cáo; Insufficient Data cho crew vs maintenance | 20.172.956 phút, 32,20%; không có logs để phân biệt cơ chế |
| NAS / capacity | Strong Evidence cho nhóm NAS; Weak Evidence cho giả thuyết “tắc nghẽn” cụ thể | 14.335.762 phút, 22,88%; NAS gồm nhiều yếu tố, không đồng nhất với thiếu capacity |
| Weather | Strong Evidence cho nhãn hủy; Insufficient Data cho attribution độc lập | 54,35% chuyến hủy mang mã weather; không có weather observation và sự kiện để xác minh |
| Time-of-day accumulation | Strong Evidence cho association; Moderate Evidence cho driver vận hành | So cùng hãng–origin–month còn +10,06 phút; không loại hết nhiễu và selection |
| Một vài extreme outliers tạo toàn bộ vấn đề | Not Supported | Bỏ >360 phút vẫn còn severe 5,60% và chênh lệch giờ |
| Airport code issue gây mọi pattern | Not Supported cho trend toàn hệ thống | Có lỗi join tháng 10, nhưng thời gian/hãng vẫn phân tích được đủ năm; địa lý đã giới hạn phạm vi |
| Aircraft-specific maintenance failure | Insufficient Data | Tail có khác biệt; không có loại máy bay, maintenance/crew hoặc phân bổ lịch đã kiểm soát |

62.651.867 phút nguyên nhân chỉ phủ **90,66%** 69.103.367 phút chậm dương, vì các chuyến chậm 1–14 phút không có báo cáo cause. Late-aircraft + airline chiếm 72,04% **reported cause minutes**; không tự quy 72,04% toàn bộ thiệt hại cho hai nhóm này. Các nhãn xác nhận được nội dung báo cáo, không xác nhận quan hệ nhân quả độc lập.

![Nguyên nhân được ghi nhận](figures/recorded_causes.png)

# Business Impact

430.662 chuyến thuộc nhóm gián đoạn nghiêm trọng theo định nghĩa của nghiên cứu; 325.591 chuyến hoàn tất chậm >=60 phút là quy mô cần chú ý về phục hồi lịch và trải nghiệm hành khách. Dữ liệu không có hành khách hay connections nên không tính số người trễ nối chuyến, compensation hoặc doanh thu mất. Không gán mọi phút chậm vào chi phí hay suy ra lợi nhuận.

Các cơ chế có thể bị ảnh hưởng: tăng khối lượng xử lý đổi hành trình, áp lực quay vòng tàu bay/tổ bay và lịch cuối ngày, giảm độ tin cậy giờ đến. Đây là tác động hợp lý để điều tra, chưa phải lượng thiệt hại đã đo. Muốn định lượng tài chính cần passenger manifests/loads, nối chuyến, crew duty, aircraft rotations, recovery actions và đơn giá phù hợp.

# Recommendations

| Priority / Problem | Evidence | Recommended Action | Expected Business Effect | Success Metric | Confidence / effort |
|---|---|---|---|---|---|
| High: tính cập nhật và mã sân bay | Năm 2015; thiếu geography của 486.165 chuyến tháng 10 | Data owner lấy kỳ dữ liệu mới và crosswalk airport ID có nguồn xác minh, kiểm định lại counts/ranks trước quyết định hiện tại | Tránh ưu tiên sai vì dữ liệu cũ hoặc tách mã | Airport resolution 100% hoặc documented exceptions; đủ ngày; quality gate trước refresh | Cao về nhu cầu; effort vừa |
| High: rủi ro cuối ngày | 8,49% severe tối vs 3,61% sáng; +10,06 phút sau phân tầng | Ops control review rotation, scheduled turn/buffer và recovery resources tại ORD/LGA 17–21h; pilot trên các tuyến common-support sau tái xác nhận bằng dữ liệu mới | Giảm lan truyền chậm và bất ổn cuối ngày | Severe/disruption/p95 theo airport-route-hour; cancellation không tăng khi mean giảm | Vừa về cơ chế; effort vừa |
| High: hủy khác chậm nặng | Tháng 2 hủy 4,78%; weather label 54,35% annual cancellations | Ops + customer recovery tách playbook hủy/phục hồi khỏi chương trình giảm delay của chuyến còn hoạt động; review lý do hủy theo ngày/airport | Phục hồi có trọng tâm; hạn chế chuyển vấn đề từ delay sang cancel | Cancellation + disruption đồng thời; phục hồi lịch và thời gian đổi hành trình khi bổ sung dữ liệu | Vừa; effort vừa |
| Medium: carrier/route reliability | NK còn +5,47 điểm % severe sau so tuyến-tháng-band; MQ hủy 5,10% | Airline performance team điều tra routes NK có matched excess và hủy MQ theo airport/month; không kết luận từ rank thô | Chọn đúng phạm vi sửa quy trình | Matched severe gap; cancellation adjusted mix; sample/coverage ổn định | Vừa cho NK; thấp-vừa cho cơ chế MQ; effort vừa |
| Medium: KPI che mất đuôi | Mean 4,41 nhưng p95 66 phút; 430.662 disruptions | BI owner hiển thị N, on-time hai mẫu số, cancel/divert, severe, p95 và positive minutes trong cùng dashboard | Nhận diện sớm khi chuyến điển hình ổn nhưng tail xấu | Reconciliation với fact; alerts theo baseline mới và control limits đã thỏa thuận | Cao về đo lường; effort thấp |
| Further Investigation: cơ chế thật và tác động | Không có UTC, weather/crew/cost/passenger | Nối weather thực, airport timezone/date offsets, tail rotations, maintenance/crew và connections; kiểm tra bằng pilot/control | Phân biệt driver khả thi và lượng hóa tác động | Linkage completeness; rotation propagation; passengers affected; cost model có bằng chứng | Chưa đủ dữ liệu; effort cao |

Các tác động kỳ vọng là giả thuyết can thiệp, không phải dự báo mức tiết kiệm. Không khuyến nghị tăng buffer toàn mạng trước khi biết trade-off utilization và kết quả pilot.

# Power BI Dashboard Plan

Đã tạo **đặc tả 7 trang**, DAX, Power Query importer và dimension CSV. Bản Desktop và bằng chứng kiểm định được quản lý riêng tại [Aviation_Insights.pbix](../powerbi/desktop/Aviation_Insights.pbix) và [desktop_verification.json](../powerbi/desktop/desktop_verification.json). Chạy script sinh báo cáo này không refresh hoặc kiểm định lại Desktop; sau thay dữ liệu phải đối soát bản Desktop riêng. Xem [đặc tả từng visual](powerbi_dashboard_plan.md), [hướng dẫn mô hình/đối soát](../powerbi/README.md), [measures DAX](../powerbi/measures.dax).

1. Executive Overview: quy mô và mức nghiêm trọng; hai mẫu số on-time, cancellation, severe, tail.
2. Airline Performance: xếp hạng descriptive có N và nguyên nhân cần điều tra; tránh kết luận từ rank thô.
3. Airport Performance: phân biệt rate/volume; 11 tháng, không gồm October.
4. Route Analysis: route risk và contribution, sample threshold, drill-through đúng phạm vi.
5. Time Analysis: late-day và monthly contrast; thể hiện calendar/local time.
6. Root Cause: nhóm nguyên nhân được ghi nhận, mẫu số rõ, bằng chứng/hypothesis tách riêng.
7. Recommendations: hành động, owner đề xuất, độ tin cậy, trạng thái chưa triển khai, KPI theo dõi.

# Success Metrics

Trước can thiệp cần tái lập baseline bằng dữ liệu đủ mới. Đề xuất pilot 4–8 tuần với nhóm tuyến/khung giờ can thiệp và comparator cùng điều kiện; cần điều chỉnh seasonality, volume và network mix. Đây là thiết kế đề xuất, không có kết quả can thiệp trong tệp.

Primary: severe arrival rate và disruption rate ở phân khúc mục tiêu. Guardrails: cancellation/diversion không tăng; volume/coverage giữ được; p95 không xấu đi; theo dõi aircraft utilization khi có. Secondary: recorded late-aircraft minutes trên scheduled flight, on-time scheduled rate, thời gian phục hồi. Không đưa mục tiêu % giảm hoặc tiền tiết kiệm không có bằng chứng; management chốt mục tiêu sau đo baseline/pilot khả thi. Nhãn “thành công” cần cả mức cải thiện vận hành và độ tin cậy đo lường, không chỉ thay đổi mean.

# Limitations

- Dữ liệu 2015, không nói lên tình hình 2026; provenance gốc và process thu thập chưa có trong repo. Phạm vi đại diện là các dòng trong tệp, không tự khẳng định toàn ngành hoặc mọi hãng/flight.
- Tháng 10 chiếm 8,35% chuyến, thiếu airport crosswalk. Loại tháng này làm mean arrival từ 4,41 tăng lên 4,89 và severe từ 5,70% lên 5,91%; geography không phải baseline đủ năm. Không ngoại suy 11 tháng thành 12 tháng.
- Arrival/causes thiếu theo outcome; không missing-at-random. Chuyến hủy không có arrival delay, nên theo dõi cancellation riêng để tránh survivorship bias.
- Chỉ một năm: tháng không đủ để chứng minh mùa lặp lại. Thay đổi coverage US/AA ảnh hưởng so sánh hãng.
- Không có UTC/actual date offsets, weather observations, duty/maintenance logs, passenger/financial data. Không thể xác minh nhân quả hoặc quantification tổn thất.
- Phân tầng chỉ dùng common support và một số biến quan sát; có selection và unmeasured confounding. So route-month và airline-origin-month là các kiểm chứng riêng.
- Các nguyên nhân là nhãn reporting; NAS có nhiều cơ chế và weather có thể lan sang late-aircraft. Không diễn giải tỷ trọng như đóng góp nhân quả thuần.

# Next Steps

1. Data owner xác minh provenance/coverage và airport-ID crosswalk; refresh dữ liệu gần kỳ quyết định, giữ source immutable và rerun gate.
2. Analyst kiểm tra độ bền của các phân khúc cuối ngày, ORD/LGA, NK/MQ trên dữ liệu mới; nếu không còn lặp lại thì điều chỉnh ưu tiên.
3. Nối timezone/date offsets và rotations để kiểm tra chuyến đến trước có liên quan thế nào tới chuyến đi sau; không nối tail theo HHMM thô.
4. Nối weather thực, crew/maintenance và passenger connections để kiểm tra driver và tác động.
5. BI owner dựng Power BI theo bộ tệp cung cấp, đối soát KPI không slicer và slicer tháng 10, sau đó quản lý pilot bằng guardrail.

**Bài học quan trọng nhất:** Insight có giá trị phải sống sót qua kiểm tra mẫu số, cơ cấu, ngoại lệ và phạm vi dữ liệu. Việc tìm ra MQ không còn chậm nặng hơn nhiều sau so cùng tuyến/tháng/giờ là kết quả có ích ngang với tìm ra một “hãng xếp cuối”.

## Evidence and Reproduction

Toàn bộ số liệu có trong `reports/tables/`; `overall`, `delay_distributions`, `time_band`, `month`, `airline`, `origin`, `destination`, `route`, `cause_totals`, `cancellation_causes`, `sensitivity`, `matched_*`, `robust_*`, `pareto_*`. [Source manifest](source_manifest.json) ghi SHA-256 của nguồn và AGENTS.md; `verification.json` xác nhận readback toàn bộ cleaned export và nguồn không đổi. [README](../README.md) mô tả lệnh tái chạy.
'''
(REPORTS/'aviation_analysis_report.md').write_text(report,encoding='utf-8')

pages=[
('Executive Overview','Quy mô vấn đề?', 'KPI cards + line chart + distribution bars','DimDate[DATE]; delay band trong chart bổ trợ','Total Flights; On-Time Rate; On-Time Scheduled Rate; Average/Median/P95 Arrival Delay; Severe Delay Rate; Cancellation Rate; Disruption Rate','Metric name (series)','Arrival Eligible Flights; Cancelled Flights; Diverted Flights; Geographic Coverage','Date; airline; hour — mặc định đủ 12 tháng','Mean 4,41 không phủ nhận 325.591 severe; p95 66','Quyết định cần ưu tiên điều tra độ tin cậy; không nhìn mean một mình'),
('Airline Performance','Hãng nào cần review loại gián đoạn nào?', 'Clustered bar + scatter + matrix','DimAirline[AIRLINE] / IATA_CODE','Severe Delay Rate; Cancellation Rate; Positive Arrival Minutes; Total Flights','Loại KPI (severe/cancel)','Total Flights; Arrival Eligible Flights; median; tháng hiện hữu','Date; airline; time band','NK severe 10,64%; MQ cancellation 5,10%; US chỉ có 6 tháng','Chọn carrier/route để review, không quy rank thô thành nguyên nhân'),
('Airport Performance','Nơi nào rủi ro cao và nơi nào tác động lớn?', 'Scatter + ranked bar + airport-hour matrix','DimOrigin[IATA_CODE]; DEP_HOUR trong matrix; DimDestination ở visual riêng','Airport Rate With Sample Threshold; Total Flights; Positive Arrival Minutes','Origin vs destination ở visual tách biệt','Arrival Eligible Flights; Cancellation Rate; median; coverage; tháng','GEO_ELIGIBLE=1 bắt buộc; date; airline; origin/destination','ORD volume/phút lớn; LGA rate cao; 11 tháng, thiếu October','Ưu tiên nguồn lực theo volume và risk; review cuối ngày'),
('Route Analysis','Tuyến nào rủi ro cao hoặc đóng góp nhiều phút chậm?', 'Matrix + Pareto bar + route-time matrix','FactFlight[ROUTE]; TIME_BAND','Route Rate With Sample Threshold; Positive Arrival Minutes; Severe Flights','TIME_BAND cho so khung giờ','Total Flights; Arrival Eligible Flights; Cancellation Rate; Median Arrival Delay','GEO_ELIGIBLE=1 bắt buộc; date; origin; destination; airline','ORD→JFK rate cao không đồng nghĩa impact cao nhất; SFO→LAX nhiều phút nhất','Chọn route pilot dựa trên sample, rate và contribution; chưa suy tiết kiệm'),
('Time Analysis','Khi nào phải tăng khả năng phục hồi?', 'Line chart + monthly combo chart + weekday heatmap','DimHour[DEP_HOUR]; DimDate[MONTH]; DAY_OF_WEEK','Average/Median Arrival Delay; Severe Delay Rate; Cancellation Rate','Metric name; airline cho drilldown','Total Flights; Arrival Eligible Flights; p95; Disruption Rate','Date; airline; TIME_BAND; nếu lọc airport phải bật GEO_ELIGIBLE=1','17–21h severe 8,49% vs 3,61% sáng; February hủy khác June chậm nặng','Review buffer/recovery đúng khung giờ; tách playbook cancellation'),
('Root Cause','Bằng chứng đang ủng hộ cơ chế nào?', 'Five-measure bar + cause-by-hour matrix + evidence text table','Tên 5 measures; DEP_HOUR trong matrix','Late Aircraft Minutes; Airline Minutes; NAS Minutes; Weather Minutes; Security Minutes','Reported cause category','Reported Cause Minutes; Cause Reported Flights; Total Flights; Positive Arrival Minutes','Date; airline; hour; airport chỉ trên dữ liệu đủ mã','Late aircraft 39,84% reported minutes; weather 54,35% cancellation; không trộn mẫu số','Ưu tiên kiểm tra rotation, airline processes; lấy dữ liệu ngoài để xác minh'),
('Recommendations','Ai làm gì và đo thế nào?', 'Action table + status cards + prospective KPI trend','Priority; proposed owner; action từ bảng Recommendations trong báo cáo nhập bằng Enter Data','Evidence; Success Metric; Confidence; Status=Proposed','Priority / confidence','Scope; baseline; limitation; expected mechanism','Priority; proposed owner; status','Các hành động chưa triển khai; không có before/after trong nguồn','Chốt data refresh và pilot; chỉ thêm kết quả can thiệp khi có thực')]
text='# Power BI Dashboard Plan\n\nĐặc tả 7 trang sau phân tích; chưa tạo `.pbix`. Cấu trúc mô hình và DAX: [powerbi/README](../powerbi/README.md). Câu chuyện: How Big → Where → When → Who → Why → Action. Page 2 giúp so hãng; flow điều tra có thể dùng navigation buttons để xem 1→3→5→2→6→7.\n\n'
for i,p in enumerate(pages,1):
    title,q,visual,axis,value,legend,tooltip,slicers,insight,decision=p
    text+=f'## Page {i} — {title}\n\n- **Business Question:** {q}\n- **Visual Type:** {visual}\n- **Axis:** {axis}\n- **Value:** {value}\n- **Legend:** {legend}\n- **Tooltip:** {tooltip}\n- **Slicers:** {slicers}\n- **Insight the Visual Should Reveal:** {insight}\n- **Business Decision Supported:** {decision}\n\n'
text+='''## Thiết kế, drill-through và tooltip

Header mỗi trang: kỳ 2015, ngày refresh, scope đầy đủ hay 11 tháng, định nghĩa >=60 phút. Card N cạnh mọi tỷ lệ. Định dạng % hai số lẻ, delay phút một–hai số lẻ, count số nguyên. Không dùng map khi tọa độ thiếu; bảng vẫn giữ đủ sân bay. Không dùng màu xanh cho NULL/không đủ dữ liệu.

Drill-through từ airport → route → airline/time trên cùng context; Page 3/4 giữ GEO_ELIGIBLE=1. Tooltip page chung chứa N scheduled/arrival eligible, cancel/divert, severe, mean/median/p95 và scope. Dùng cross-filter một chiều dimension→fact. Không tự nhân bản fact để unpivot nguyên nhân. Cho phép xem báo cáo chất lượng riêng bằng link đến data_quality_report.md.

Các charts nhiều visual ở cùng trang nên tách axis/value tương ứng: thẻ KPI không có axis/legend; line theo DATE/DEP_HOUR có series là measure; scatter airport có X=Total Flights, Y=Severe Delay Rate, Details=airport. Distribution bars là hình bổ trợ hiện có; nếu cần tương tác trong Desktop, tạo delay band ở Power Query với ranh giới <0, 0–14, 15–59, 60–119, 120–359, >=360 và giữ NULL cho hủy/đổi hướng. Không diễn giải UNKNOWN như một sân bay thật.

**Acceptance:** Tổng không filter phải khớp bảng đối soát; filter October có 486.165 chuyến global, geography 0; percent of total không được lấy mẫu số từ bảng đã Top-N mà quên các nhóm còn lại. Nếu làm Pareto bằng DAX, xác định rõ toàn bộ selected population bằng ALLSELECTED trên dimension thích hợp và kiểm chứng với pareto_*.csv; các CSV chứa cumulative share đã tính để đối chiếu. Không công bố dashboard là đã refresh/kiểm thử trong Desktop cho đến khi chạy thực tế.
'''
(REPORTS/'powerbi_dashboard_plan.md').write_text(text,encoding='utf-8')

dictionary='''# Data Dictionary

Grain: một scheduled flight leg trong một ngày. Raw CSV giữ nguyên; fact xử lý giữ giá trị nguồn theo kiểu ngữ nghĩa (HHMM có thể mất số 0 dẫn đầu khi xuất số nguyên; không mất nghĩa). Delay có thể âm. NA không được hiểu là 0.

| Field / group | Meaning / unit | Use / caution |
|---|---|---|
| YEAR, MONTH, DAY | Thành phần ngày khởi hành theo lịch | Tạo DATE; không phải ngày UTC của sự kiện đến |
| DAY_OF_WEEK | Thứ, Monday=1 … Sunday=7 | Đã đối chiếu DATE |
| AIRLINE | Mã hãng; text | Nối airlines.IATA_CODE; không khẳng định marketing network/code-share |
| FLIGHT_NUMBER | Số chuyến | Không unique một mình |
| TAIL_NUMBER | Đăng ký tàu bay | Không phải aircraft type; thiếu ở một số chuyến hủy |
| ORIGIN_AIRPORT, DESTINATION_AIRPORT | Mã hai đầu chặng | Text; tháng 10 numeric IDs chưa có crosswalk |
| SCHEDULED_DEPARTURE, SCHEDULED_ARRIVAL | Giờ lịch local HHMM | 2400 hợp lệ; không trừ giữa hai timezone |
| DEPARTURE_TIME, ARRIVAL_TIME | Giờ gate thực local HHMM | Không có actual date offsets |
| WHEELS_OFF, WHEELS_ON | Giờ cất/hạ cánh local HHMM | Không thay thế gate time |
| DEPARTURE_DELAY, ARRIVAL_DELAY | Phút lệch giờ lịch, âm= sớm | Arrival thiếu khi hủy/đổi hướng |
| TAXI_OUT, TAXI_IN | Phút lăn trước/sau bay | Không âm; kiểm tra cộng thành elapsed |
| SCHEDULED_TIME, ELAPSED_TIME, AIR_TIME | Phút lịch gate-to-gate, thực gate-to-gate, airborne | Kiểm tra identities khi đủ trường |
| DISTANCE | Giả định statute miles theo dạng dữ liệu BTS | Chưa xác thực metadata; không dùng cho kết luận chi phí |
| CANCELLED, DIVERTED | Cờ 0/1 | Hai nhóm không chồng lấn trong dữ liệu |
| CANCELLATION_REASON | A airline, B weather, C NAS, D security | Chỉ áp dụng khi hủy; nhãn báo cáo |
| AIR_SYSTEM_DELAY, SECURITY_DELAY, AIRLINE_DELAY, LATE_AIRCRAFT_DELAY, WEATHER_DELAY | Phút nguyên nhân ghi nhận | Có đủ năm trường chỉ cho arrival >=15; không phải feature có sẵn trước chuyến |
| airports.IATA_CODE / airlines.IATA_CODE | Khóa dimension | Đã kiểm tra unique |
| airports.AIRPORT, CITY, STATE, COUNTRY | Tên và vị trí | Historical labels; không tự chuẩn hóa sang tên hiện tại |
| LATITUDE, LONGITUDE | Tọa độ decimal degrees | 3 sân bay thiếu cả hai; không điền |
| FLIGHT_ID | Surrogate 1…N | Ổn định theo thứ tự dòng tệp nguồn hiện tại |
| DATE, DEP_HOUR, TIME_BAND, SEASON | Ngày, giờ và phân đoạn theo lịch | DJF là các tháng 12/1/2 trong cùng tệp, không một mùa đông liên tục |
| ORIGIN_KEY, DESTINATION_KEY, GEO_ELIGIBLE, ROUTE | Khóa dimensional và phạm vi địa lý | __UNRESOLVED__ bảo toàn tháng 10; xếp hạng chỉ GEO_ELIGIBLE=1 |
| COMPLETED, ARR_ELIGIBLE | Không hủy/đổi hướng, arrival delay có thể dùng | Trong tệp này hai count bằng nhau |
| DEP_DELAY_ANALYSIS, ARR_DELAY_ANALYSIS | Delay đủ điều kiện dùng | DEP loại hủy và departure clock lỗi; ARR chỉ hoàn tất |
| ON_TIME, DELAYED_15, SEVERE_60 | Flags arrival <15, >=15, >=60 | ON_TIME đòi ARR_ELIGIBLE; severe là định nghĩa điều hành |
| DISRUPTED | CANCELLED or DIVERTED or SEVERE_60 | Hợp không trùng; mẫu số toàn lịch |
| POSITIVE_ARR_MINUTES | max(ARR_DELAY_ANALYSIS,0) | Không bù trừ sớm/chậm; NA giữ nguyên |
| CAUSE_REPORTED, LATE_AIRCRAFT_POSITIVE | Đủ năm nguyên nhân, late-aircraft minutes>0 | Không cộng count nhiều cause thành tổng flights |
| TIME_ISSUE | Flag consistency của time/duration | 2 dòng; giữ raw, không đoán sửa |
'''
(REPORTS/'data_dictionary.md').write_text(dictionary,encoding='utf-8')
print('Created client report, data dictionary, Power BI plan and 5 PNG figures.')
