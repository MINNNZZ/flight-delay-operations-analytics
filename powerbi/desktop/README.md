> Public release: the embedded PBIX files are not attached. Review screenshots_en/ and screenshots_vi/ plus source definitions. See [distribution status](../../docs/PBIX_DISTRIBUTION.md).

# Báo cáo Power BI Desktop

Mở [Aviation_Insights.pbix](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0) bằng Power BI Desktop: báo cáo có nhúng dữ liệu, 7 trang và biểu đồ native. Đã mở lại chính bản `.pbix` và đối soát 21 chỉ tiêu DAX: **PASS**. Xem [kết quả kiểm định](desktop_verification.json). Tệp khoảng 234 MB; không cần refresh để xem dữ liệu đã nhúng.

`Aviation_Insights.pbip` là bản dự án có thể sửa định nghĩa báo cáo/mô hình. Đường dẫn nguồn refresh hiện trỏ tới workspace trên máy này. Giữ nguyên toàn bộ thư mục `.Report` và `.SemanticModel` nếu chuyển PBIP.

Các trang: tổng quan; hãng; sân bay; tuyến; thời gian; nguyên nhân; hành động. Nhấp vào thanh/cột/điểm để lọc chéo các visual cùng trang; nhấp vùng trống để bỏ chọn. Các danh sách top sân bay/tuyến được chọn trên dữ liệu nền 2015, không phải danh sách top tự xếp hạng lại theo mọi tương tác.

Phạm vi: dữ liệu lịch sử 2015. Sân bay/tuyến giới hạn 11 tháng nhận diện được, không gồm tháng 10; trang toàn hệ thống/hãng/thời gian giữ đủ 12 tháng. Tooltip có cỡ mẫu và mẫu số arrival. Nguyên nhân là nhãn ghi nhận, không phải chứng minh nhân quả. Không có kết quả can thiệp thực tế trong nguồn.

Mô hình và biểu đồ được tạo bằng `../build_desktop_report.py`, kiểm tra bằng `../validate_desktop_report.py`, sau đó đã nạp và kiểm tra trong Power BI Desktop. `verify_model.dax` đối soát KPI trực tiếp bằng engine DAX; `native_dax_results.json` chứa kết quả từ chính bản `.pbix` đã mở lại. Xem ảnh ở `screenshots/`. `../verify_native_outputs.py` kiểm tra KPI, số trang, mô hình nhúng và ảnh. Sau khi thay dữ liệu/định nghĩa phải kiểm định lại, không dùng kết quả PASS cũ.

Lần nạp đầu qua giao diện gặp trạng thái chờ Syncing schema. Đã xử lý bằng refresh đầy đủ qua TOM của chính engine Desktop, xuất cache bằng ImageSave và mở lại; cả 9 bảng sau refresh đều Ready. Bản `.pbix` bàn giao đã được Desktop lưu và mở lại thành công. Refresh toàn bộ CSV gzip có thể mất vài phút; script tạo mô hình đã bổ sung số cột CSV tường minh cho lần tái dựng sau.

Khi chuyển sang máy khác, cập nhật đường dẫn file trong Power Query. Không chỉnh AGENTS.md hoặc CSV nguồn khi dựng báo cáo.
