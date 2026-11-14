# Kế hoạch điều tra chậm chuyến

## Business Question

Câu hỏi gốc còn placeholder. Giả định làm việc: điều tra chậm chuyến và gián đoạn vận hành trong ba tệp `flights.csv`, `airports.csv`, `airlines.csv`; xác định phân khúc, thời điểm và nguyên nhân được ghi nhận để ưu tiên cải thiện độ tin cậy. Đây là nghiên cứu lịch sử, không phải đánh giá tình hình vận hành hiện tại.

## Data Required → Data Quality Checks

Đọc toàn bộ dữ liệu; kiểm tra schema, kiểu dữ liệu, khóa chuyến bay, bản ghi trùng, thiếu dữ liệu theo trạng thái, mã sân bay/hãng, ngày, giờ HHMM và giá trị 2400, tính nhất quán các khoảng thời gian, cờ hủy/đổi hướng, nguyên nhân, ngoại lệ và độ phủ. Không suy đoán mã sân bay hoặc múi giờ. Chỉ phân tích sau khi có báo cáo chất lượng và gate theo phạm vi sử dụng.

## KPIs

On-time arrival: ARRIVAL_DELAY < 15 phút trong các chuyến không hủy/không đổi hướng có số liệu đến hợp lệ. Severe delay: ARRIVAL_DELAY >= 60 phút (ngưỡng phục vụ điều hành, không phải định nghĩa BTS). Hủy và đổi hướng có mẫu số toàn bộ chuyến theo lịch. Báo cáo thêm tỷ lệ đến đúng giờ trên toàn lịch, gián đoạn tổng hợp, mean, median, p90/p95/p99 và phút chậm dương; không bù trừ phút chậm bằng phút đến sớm.

## Dimensions → Methods

Hãng; sân bay đi/đến; tuyến; giờ khởi hành theo lịch địa phương; thứ; tháng/mùa; số đăng ký tàu bay; nguyên nhân ghi nhận; trạng thái. Kiểm tra airport × hour, airline × airport, route × time; Pareto; độ bền theo tháng/hãng/sân bay; phân tầng để hạn chế nhiễu; phân tích nhạy cảm với ngoại lệ, tháng mã sân bay lỗi và chuyến bị hủy. Luôn kèm cỡ mẫu và quy định ngưỡng trước khi xếp hạng (sân bay >= 10.000 chuyến, tuyến >= 1.000 chuyến; mô tả, không suy diễn nhân quả).

## Expected Business Output

Dữ liệu đã xử lý riêng; báo cáo chất lượng trước/sau; bảng EDA và phân đoạn; kết quả kiểm chứng giả thuyết; hình minh họa có thể chia sẻ; mô hình sao, DAX và thiết kế 7 trang Power BI; báo cáo khách hàng bằng tiếng Việt. Không ép dùng ML và không quy đổi chi phí khi thiếu dữ liệu tài chính.
