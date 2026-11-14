# Power BI: mô hình và kiểm định

Đã dựng và mở [Aviation_Insights.pbix](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0) bằng Power BI Desktop trên máy, có nhúng dữ liệu và đủ **7 trang**. [Kiểm định Desktop](desktop/desktop_verification.json) xác nhận 21 chỉ tiêu DAX khớp kết quả Python, 51 thành phần trực quan và mô hình dữ liệu đầy đủ. Có thêm [dự án PBIP](desktop/Aviation_Insights.pbip) và [ảnh từng trang](desktop/screenshots_en/page_1.png).

Bản Desktop sử dụng thẻ KPI, biểu đồ line/bar/column, bảng hành động và diễn giải tiếng Việt. Dùng chọn điểm dữ liệu và Filter pane để khám phá; chưa triển khai mọi scatter/heatmap/slicer/drill-through được đề xuất trong kế hoạch ban đầu. Danh sách top sân bay/tuyến cố định theo dữ liệu nền 2015. Các bước dưới đây cũng dùng làm tài liệu tái dựng và đối soát.

1. Tạo query `FactFlight` bằng `FactFlight.pq`. Thay `ProjectRoot` nếu chuyển máy. Nếu máy thiếu RAM để giải nén trong Power Query, giải nén CSV một lần và dùng trình nhập Text/CSV. Không thay file nguồn ban đầu.
2. Nhập `dim_airline.csv`, `dim_date.csv`, `dim_hour.csv` từ `data/processed/` và đặt tên query lần lượt `DimAirline`, `DimDate`, `DimHour`. Nhập `dim_airport.csv` hai lần thành `DimOrigin`, `DimDestination`; giữ `IATA_CODE` làm khóa ở cả hai bảng.
3. Kiểu dữ liệu: DATE là Date; khóa mã là Text; các cột số nguyên và cờ là Whole number; LATITUDE/LONGITUDE là Decimal number. Đánh dấu DimDate làm date table bằng DATE. HHMM gốc là mã giờ, không phải số giờ thập phân; giờ lịch địa phương dùng DEP_HOUR.
4. Tạo quan hệ one-to-many, active, hướng lọc từ dimension đến fact: DimDate[DATE] → FactFlight[DATE]; DimAirline[IATA_CODE] → FactFlight[AIRLINE]; DimHour[DEP_HOUR] → FactFlight[DEP_HOUR]; DimOrigin[IATA_CODE] → FactFlight[ORIGIN_KEY]; DimDestination[IATA_CODE] → FactFlight[DESTINATION_KEY]. Không nối hai dimension airport với nhau. Thành viên `__UNRESOLVED__` bảo toàn các chuyến tháng 10.
5. Tạo measures trong `measures.dax`, mỗi định nghĩa riêng. Tỷ lệ định dạng %; phút 1–2 số lẻ; count số nguyên. Không SUM delay có dấu để đo tổn thất: dùng Positive Arrival Minutes. Không lấy trung bình các tỷ lệ từ bảng aggregate; chia tổng tử số cho tổng mẫu số.
6. Page 3/4 và mọi drill-through có tên sân bay/tuyến: bắt buộc `GEO_ELIGIBLE=1`, chú thích **11 tháng, không gồm tháng 10/2015**. Page 1/2/5/6 giữ đủ 12 tháng; cần banner phạm vi và card Geographic Coverage (91,65% ở toàn hệ thống). Slicer tháng 10 trên trang địa lý sẽ trả rỗng, phải hiển thị thông báo không có mã đã xác minh.
7. Tooltip chung: Total Flights, Arrival Eligible Flights, Severe Delay Rate, Cancellation Rate, Average Arrival Delay, Median Arrival Delay, Time Issue Flights, phạm vi tháng. Drill-through theo airline+origin+route+time band; không gắn mã số tháng 10 vào airport đoán.
8. Với biểu đồ nguyên nhân, dùng 5 measures tương ứng làm series/value (hoặc field parameter trong Desktop). Không unpivot và nhân bản fact chính: sẽ nhân số chuyến 5 lần. Mẫu số share nguyên nhân là Reported Cause Minutes, không phải toàn bộ phút chậm dương. Chuyến có nhiều nguyên nhân không được cộng count từng nguyên nhân để thành tổng chuyến.

## Kiểm định sau refresh

| Check, không slicer | Kỳ vọng |
|---|---:|
| Total Flights | 5.819.079 |
| Completed / Arrival Eligible Flights | 5.714.008 |
| Cancelled Flights | 89.884 |
| Diverted Flights | 15.187 |
| On-Time Flights | 4.650.569 |
| Severe Flights | 325.591 |
| Disrupted Flights | 430.662 |
| Positive Arrival Minutes | 69.103.367 |
| Reported Cause Minutes | 62.651.867 |
| On-Time Rate / On-Time Scheduled Rate | 81,3889% / 79,9193% |
| Cancellation Rate / Severe Delay Rate | 1,5446% / 5,6981% |
| Average / Median Arrival Delay | 4,407057 / -5 phút |
| Geographically Resolved Flights | 5.332.914 |
| Time Issue Flights | 2 |

Kiểm tra bộ lọc tháng 10: toàn hệ thống 486.165 chuyến, địa lý không có chuyến nhận diện được (COUNTROWS của tập rỗng trả BLANK). Kiểm tra airline NK: 117.379 chuyến, arrival_n=115.193; MQ: 294.632 chuyến, cancelled=15.025. Không tự quy hủy/đổi hướng thành on-time do DAX coi BLANK giống 0 trong một số phép so sánh: numerator dùng ON_TIME được xác định trước. Tháng/hãng ít chuyến hiển thị N và không xếp hạng khi dưới ngưỡng. US chỉ có dữ liệu tháng 1–6; kết quả hãng chưa điều chỉnh cơ cấu phải mang nhãn descriptive.

## Tài liệu chính thức

- [Microsoft: star schema, role-playing dimensions](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Microsoft: active/inactive relationships](https://learn.microsoft.com/en-us/power-bi/guidance/relationships-active-inactive)
- [Microsoft: CALCULATE](https://learn.microsoft.com/en-us/dax/calculate-function-dax/)
- [Microsoft: DIVIDE](https://learn.microsoft.com/en-us/dax/divide-function-dax)
- [Microsoft: Binary.Decompress](https://learn.microsoft.com/en-us/powerquery-m/binary-decompress)

Xem [đặc tả visual từng trang](../reports/powerbi_dashboard_plan.md).
