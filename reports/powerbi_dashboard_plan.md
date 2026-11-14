# Power BI Dashboard Plan

Đặc tả 7 trang sau phân tích; chưa tạo `.pbix`. Cấu trúc mô hình và DAX: [powerbi/README](../powerbi/README.md). Câu chuyện: How Big → Where → When → Who → Why → Action. Page 2 giúp so hãng; flow điều tra có thể dùng navigation buttons để xem 1→3→5→2→6→7.

## Page 1 — Executive Overview

- **Business Question:** Quy mô vấn đề?
- **Visual Type:** KPI cards + line chart + distribution bars
- **Axis:** DimDate[DATE]; delay band trong chart bổ trợ
- **Value:** Total Flights; On-Time Rate; On-Time Scheduled Rate; Average/Median/P95 Arrival Delay; Severe Delay Rate; Cancellation Rate; Disruption Rate
- **Legend:** Metric name (series)
- **Tooltip:** Arrival Eligible Flights; Cancelled Flights; Diverted Flights; Geographic Coverage
- **Slicers:** Date; airline; hour — mặc định đủ 12 tháng
- **Insight the Visual Should Reveal:** Mean 4,41 không phủ nhận 325.591 severe; p95 66
- **Business Decision Supported:** Quyết định cần ưu tiên điều tra độ tin cậy; không nhìn mean một mình

## Page 2 — Airline Performance

- **Business Question:** Hãng nào cần review loại gián đoạn nào?
- **Visual Type:** Clustered bar + scatter + matrix
- **Axis:** DimAirline[AIRLINE] / IATA_CODE
- **Value:** Severe Delay Rate; Cancellation Rate; Positive Arrival Minutes; Total Flights
- **Legend:** Loại KPI (severe/cancel)
- **Tooltip:** Total Flights; Arrival Eligible Flights; median; tháng hiện hữu
- **Slicers:** Date; airline; time band
- **Insight the Visual Should Reveal:** NK severe 10,64%; MQ cancellation 5,10%; US chỉ có 6 tháng
- **Business Decision Supported:** Chọn carrier/route để review, không quy rank thô thành nguyên nhân

## Page 3 — Airport Performance

- **Business Question:** Nơi nào rủi ro cao và nơi nào tác động lớn?
- **Visual Type:** Scatter + ranked bar + airport-hour matrix
- **Axis:** DimOrigin[IATA_CODE]; DEP_HOUR trong matrix; DimDestination ở visual riêng
- **Value:** Airport Rate With Sample Threshold; Total Flights; Positive Arrival Minutes
- **Legend:** Origin vs destination ở visual tách biệt
- **Tooltip:** Arrival Eligible Flights; Cancellation Rate; median; coverage; tháng
- **Slicers:** GEO_ELIGIBLE=1 bắt buộc; date; airline; origin/destination
- **Insight the Visual Should Reveal:** ORD volume/phút lớn; LGA rate cao; 11 tháng, thiếu October
- **Business Decision Supported:** Ưu tiên nguồn lực theo volume và risk; review cuối ngày

## Page 4 — Route Analysis

- **Business Question:** Tuyến nào rủi ro cao hoặc đóng góp nhiều phút chậm?
- **Visual Type:** Matrix + Pareto bar + route-time matrix
- **Axis:** FactFlight[ROUTE]; TIME_BAND
- **Value:** Route Rate With Sample Threshold; Positive Arrival Minutes; Severe Flights
- **Legend:** TIME_BAND cho so khung giờ
- **Tooltip:** Total Flights; Arrival Eligible Flights; Cancellation Rate; Median Arrival Delay
- **Slicers:** GEO_ELIGIBLE=1 bắt buộc; date; origin; destination; airline
- **Insight the Visual Should Reveal:** ORD→JFK rate cao không đồng nghĩa impact cao nhất; SFO→LAX nhiều phút nhất
- **Business Decision Supported:** Chọn route pilot dựa trên sample, rate và contribution; chưa suy tiết kiệm

## Page 5 — Time Analysis

- **Business Question:** Khi nào phải tăng khả năng phục hồi?
- **Visual Type:** Line chart + monthly combo chart + weekday heatmap
- **Axis:** DimHour[DEP_HOUR]; DimDate[MONTH]; DAY_OF_WEEK
- **Value:** Average/Median Arrival Delay; Severe Delay Rate; Cancellation Rate
- **Legend:** Metric name; airline cho drilldown
- **Tooltip:** Total Flights; Arrival Eligible Flights; p95; Disruption Rate
- **Slicers:** Date; airline; TIME_BAND; nếu lọc airport phải bật GEO_ELIGIBLE=1
- **Insight the Visual Should Reveal:** 17–21h severe 8,49% vs 3,61% sáng; February hủy khác June chậm nặng
- **Business Decision Supported:** Review buffer/recovery đúng khung giờ; tách playbook cancellation

## Page 6 — Root Cause

- **Business Question:** Bằng chứng đang ủng hộ cơ chế nào?
- **Visual Type:** Five-measure bar + cause-by-hour matrix + evidence text table
- **Axis:** Tên 5 measures; DEP_HOUR trong matrix
- **Value:** Late Aircraft Minutes; Airline Minutes; NAS Minutes; Weather Minutes; Security Minutes
- **Legend:** Reported cause category
- **Tooltip:** Reported Cause Minutes; Cause Reported Flights; Total Flights; Positive Arrival Minutes
- **Slicers:** Date; airline; hour; airport chỉ trên dữ liệu đủ mã
- **Insight the Visual Should Reveal:** Late aircraft 39,84% reported minutes; weather 54,35% cancellation; không trộn mẫu số
- **Business Decision Supported:** Ưu tiên kiểm tra rotation, airline processes; lấy dữ liệu ngoài để xác minh

## Page 7 — Recommendations

- **Business Question:** Ai làm gì và đo thế nào?
- **Visual Type:** Action table + status cards + prospective KPI trend
- **Axis:** Priority; proposed owner; action từ bảng Recommendations trong báo cáo nhập bằng Enter Data
- **Value:** Evidence; Success Metric; Confidence; Status=Proposed
- **Legend:** Priority / confidence
- **Tooltip:** Scope; baseline; limitation; expected mechanism
- **Slicers:** Priority; proposed owner; status
- **Insight the Visual Should Reveal:** Các hành động chưa triển khai; không có before/after trong nguồn
- **Business Decision Supported:** Chốt data refresh và pilot; chỉ thêm kết quả can thiệp khi có thực

## Thiết kế, drill-through và tooltip

Header mỗi trang: kỳ 2015, ngày refresh, scope đầy đủ hay 11 tháng, định nghĩa >=60 phút. Card N cạnh mọi tỷ lệ. Định dạng % hai số lẻ, delay phút một–hai số lẻ, count số nguyên. Không dùng map khi tọa độ thiếu; bảng vẫn giữ đủ sân bay. Không dùng màu xanh cho NULL/không đủ dữ liệu.

Drill-through từ airport → route → airline/time trên cùng context; Page 3/4 giữ GEO_ELIGIBLE=1. Tooltip page chung chứa N scheduled/arrival eligible, cancel/divert, severe, mean/median/p95 và scope. Dùng cross-filter một chiều dimension→fact. Không tự nhân bản fact để unpivot nguyên nhân. Cho phép xem báo cáo chất lượng riêng bằng link đến data_quality_report.md.

Các charts nhiều visual ở cùng trang nên tách axis/value tương ứng: thẻ KPI không có axis/legend; line theo DATE/DEP_HOUR có series là measure; scatter airport có X=Total Flights, Y=Severe Delay Rate, Details=airport. Distribution bars là hình bổ trợ hiện có; nếu cần tương tác trong Desktop, tạo delay band ở Power Query với ranh giới <0, 0–14, 15–59, 60–119, 120–359, >=360 và giữ NULL cho hủy/đổi hướng. Không diễn giải UNKNOWN như một sân bay thật.

**Acceptance:** Tổng không filter phải khớp bảng đối soát; filter October có 486.165 chuyến global, geography 0; percent of total không được lấy mẫu số từ bảng đã Top-N mà quên các nhóm còn lại. Nếu làm Pareto bằng DAX, xác định rõ toàn bộ selected population bằng ALLSELECTED trên dimension thích hợp và kiểm chứng với pareto_*.csv; các CSV chứa cumulative share đã tính để đối chiếu. Không công bố dashboard là đã refresh/kiểm thử trong Desktop cho đến khi chạy thực tế.
