# Phân tích chậm chuyến và độ tin cậy vận hành

Dự án phân tích **5.819.079 chuyến theo lịch năm 2015** bằng Python/pandas và Power BI. Mục tiêu là tìm nơi, thời điểm, phân khúc gặp vấn đề và ưu tiên điều tra vận hành, không xây mô hình dự báo.

**Chưa công khai file PBIX:** hai file có dữ liệu chuyến bay nhúng và đang được giữ trên máy, chờ xác nhận quyền phân phối cùng phê duyệt công khai dữ liệu nhúng. Repository hiện có ảnh đủ 7 trang mỗi ngôn ngữ, mã và định nghĩa mô hình/báo cáo. Xem [trạng thái phân phối](docs/PBIX_DISTRIBUTION.md).

- [Báo cáo tiếng Việt đầy đủ](reports/final_analysis_report_vi.md)
- [Bản Power BI tiếng Việt](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0)
- [Báo cáo tiếng Anh](reports/final_analysis_report_en.md)
- [README tiếng Anh và cách chạy](README.md)

## Năm phát hiện chính

1. Mean đến chậm 4,41 phút che khuất **430.662 chuyến gián đoạn**, tương đương 7,40% lịch bay.
2. Rủi ro chậm nặng lúc 17–21h là **8,49%**, so với **3,61%** lúc 06–11h; cần điều tra phân khúc cuối ngày, chưa thể quy nguyên nhân.
3. ORD nổi bật về tổng phút chậm, LGA về rủi ro; phân tích địa lý chỉ gồm **11 tháng đủ mã**.
4. Tháng 2 nổi bật về hủy, tháng 6 về chậm nặng. Nhãn thời tiết trong hủy và phút nguyên nhân có mẫu số khác nhau.
5. NK giữ chênh lệch bất lợi trong các cấu hình đã thử; MQ nhạy với tập chuyến được giữ. Phải tách chọn tập đối chiếu khỏi chuẩn hóa cơ cấu.

Power BI có hai bản ngôn ngữ, **7 trang mỗi bản**, 21 KPI DAX mỗi bản đã đối soát. Ảnh từng trang nằm trong `powerbi/desktop/screenshots_vi/` và `screenshots_en/`.

Dữ liệu năm 2015 không đại diện hiện tại. Không có bằng chứng giảm chậm hoặc tiết kiệm chi phí sau can thiệp. Repository là dự án portfolio có AI hỗ trợ, không phải hệ thống đã triển khai vận hành. CSV nguồn lớn không đưa vào Git; cần cung cấp tệp đúng schema và kiểm tra hash theo [hướng dẫn dữ liệu](docs/DATA_SETUP.md). PBIX có dữ liệu nhúng và được phân phối qua Releases.
