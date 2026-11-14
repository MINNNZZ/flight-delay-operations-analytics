# Data Quality Assessment

**Gate: READY WITH WARNINGS** cho phân tích hệ thống/hãng/thời gian; **NOT READY** cho xếp hạng sân bay/tuyến đủ 12 tháng có tên, phân tích rotation UTC hoặc suy diễn tình hình hiện tại. Kiểm định đã thực hiện trước EDA.

Nguồn: 5,819,079 dòng × 31 cột; 365 ngày năm 2015; airports: 322 dòng; airlines: 14 dòng. Không có duplicate toàn dòng hoặc khóa ghép; ngày, thứ, giờ HHMM và cờ trạng thái hợp lệ. HHMM=2400 là nửa đêm hợp lệ, không phải 24:00 trong cùng ngày.

| Issue | Affected Rows | % toàn bộ | Possible Explanation / Business Meaning | Analytical Risk | Cleaning Decision / Validation |
|---|---:|---:|---|---|---|
| Mã sân bay số tháng 10, cả hai đầu | 486165 | 8.3547 | Thay đổi cách mã hóa; chưa có crosswalk được xác minh | Tách một sân bay thành hai thực thể; sai xếp hạng | Giữ mã gốc, thêm khóa __UNRESOLVED__, GEO_ELIGIBLE=0; không đoán mã IATA; kiểm tra FK sau xử lý |
| ARRIVAL_DELAY thiếu | 105071 | 1.8056 | 89884 hủy + 15187 đổi hướng | Điền 0 sẽ tạo on-time giả | Giữ NULL; mẫu số ARR_ELIGIBLE; 100% chuyến hoàn tất có arrival delay |
| Mỗi cột nguyên nhân thiếu | 4755640 | 81.7250 | Chỉ có nguyên nhân cho chuyến đến chậm >=15 phút | Không thể dùng như biến giải thích dự báo độc lập | Giữ NULL; tổng nguyên nhân khớp arrival delay trong từng dòng được ghi nhận |
| TAIL_NUMBER thiếu | 14721 | 0.2530 | Tất cả thuộc chuyến hủy | Xóa NULL làm mất gián đoạn thật | Giữ các chuyến; phân tích tail chỉ với tail hiện hữu |
| SCHEDULED_TIME thiếu | 6 | 0.000103 | 5 hủy, 1 đổi hướng | Không thể suy ra đủ planned duration | Không điền; loại khỏi kiểm tra duration khi không đủ dữ liệu |
| Mâu thuẫn thời gian | 2 | 0.000034 | Một chuyến F9 lệch identity 2 phút; một chuyến NK đã hủy có departure delay không khớp đồng hồ | Sai phân tích thời lượng/rotation | Gắn TIME_ISSUE=1, giữ nguồn; NK không thuộc mẫu số departure vì đã hủy; kiểm chứng sensitivity bỏ cả hai |
| Arrival delay >360 phút | 6089 | 0.1046 | Có thể là gián đoạn vận hành thực | Mean lệch đuôi phải | Giữ toàn bộ; so sánh <=360, median và p95/p99 |
| Arrival delay < -60 phút | 392 | 0.0067 | Đến sớm hoặc lịch có buffer; không đủ bằng chứng gọi là lỗi | Mean che khuất phút chậm | Giữ; báo cáo thêm tổng phút chậm dương |
| Tọa độ thiếu | 3 sân bay | 0.9317% danh mục | Thiếu metadata | Map không đầy đủ | Giữ sân bay trong bảng/xếp hạng, không bịa tọa độ |

## Trước và sau xử lý

Không xóa dòng, không điền NULL, không sửa giá trị nguồn, không giảm duplicate vì trước xử lý không có. Bổ sung DATE, cờ chất lượng/eligibility, trạng thái, phân đoạn thời gian, khóa ngoại có thành viên chưa xác định và trường KPI. Missingness nguồn không giảm: đây là lựa chọn đúng với dữ liệu thiếu mang ý nghĩa vận hành. Số hàng được gắn cờ địa lý: 486165; thời gian: 2. Các cờ có thể chồng lấn. Mọi hủy/đổi hướng/ngoại lệ được giữ. Xem `cleaning_validation.json`, `data_profile.json` và các bảng `quality_*.csv` để kiểm tra số liệu đầy đủ.

## Độ tươi, đơn vị và múi giờ

Dữ liệu phủ 2015-01-01 đến 2015-12-31, đã khoảng 11 năm; không đại diện 2026. Dữ liệu nguồn không có provenance/metadata đơn vị đầy đủ: delay/time duration được diễn giải là phút theo ngữ nghĩa cột và kiểm tra identities. DISTANCE giả định mile theo định dạng BTS, không dùng cho kết luận định lượng kinh doanh. Giờ là local HHMM; không trừ trực tiếp giờ sân bay đi khỏi sân bay đến hoặc suy ra UTC. Không có dữ liệu type máy bay, hành khách, công suất, chi phí hay thời tiết đo thực tế.

## Tài liệu định nghĩa

[BTS technical directive #22](https://www.bts.gov/topics/airlines-and-airports/number-22-technical-directive-time-reporting-effective-jan-1-2013) giải thích HHMM/local time và mã hủy A/B/C/D. [BTS FAQ](https://www.bts.gov/explore-topics-and-geography/topics/airline-time-performance-and-causes-flight-delays) định nghĩa on-time <15 phút và các nhóm nguyên nhân. Tài liệu được dùng để diễn giải; không khẳng định provenance của ba tệp đã được xác thực độc lập.
