# Rà soát và cải thiện phân tích bằng skill data-analysis

Phạm vi: 5.819.079 chuyến theo lịch năm 2015. Báo cáo này bổ sung cho [bản diễn giải chi tiết](../bao_cao_insight_chi_tiet.md), không thay dữ liệu lịch sử bằng dữ liệu hiện tại. Mọi chênh lệch tỷ lệ dưới đây tính bằng **điểm phần trăm**, không phải phần trăm thay đổi tương đối.

## 1. Câu hỏi kinh doanh

Các kết luận về rủi ro cuối ngày và khác biệt hãng có đủ vững để lựa chọn phạm vi điều tra vận hành không? Cần cải thiện phương pháp, cách diễn giải và khả năng tái chạy ở đâu?

Kết luận điều hành: ưu tiên điều tra vận hành cuối ngày vẫn có cơ sở. NK tiếp tục có chênh lệch chậm nặng cùng chiều qua các cấu hình được thử. Riêng MQ, kết luận “điều chỉnh cơ cấu làm chênh lệch biến mất” cần được sửa: chọn tập chuyến đối chiếu đã làm kết quả thay đổi lớn, và kết quả nhạy với cách chia giờ. Không có bằng chứng can thiệp để khẳng định mức tiết kiệm hay hiệu quả cải thiện đã đạt được.

## 2. Chất lượng dữ liệu và độ tươi

Đã chạy lại profiling toàn bộ nguồn và xác nhận các SHA-256 của ba CSV giống nguồn dùng cho phân tích trước. Trạng thái tiếp tục là **READY WITH WARNINGS** cho KPI hệ thống; **NOT READY** cho địa lý có tên sân bay đủ 12 tháng. Có 486.165 chuyến tháng 10 chưa nối được mã sân bay số với danh mục; các phép so tuyến dưới đây chỉ dùng 11 tháng đủ mã.

Đã bổ sung kiểm tra bắt buộc trước khi tái sử dụng profile/gate: nguồn phải khớp hash, profile và manifest phải có cùng `profile_run_id`, gate phải xác định đúng ba tệp nguồn và có trạng thái cho phép. Nguồn thay đổi hoặc lần profiling công bố dở sẽ bị chặn. Kiểm tra này xác minh sự tương ứng giữa tệp và đánh giá chất lượng; nó không tự làm dữ liệu trở nên đúng hoặc cập nhật đến 2026.

## 3. Quyết định làm sạch

Giữ nguyên CSV nguồn và bản cleaned export. Không xóa outlier, không điền giá trị thiếu và không tự suy mã sân bay tháng 10. Chuyến hủy/chuyển hướng vẫn thuộc mẫu số scheduled/disruption; tỷ lệ severe và mean arrival chỉ dùng chuyến hoàn tất có `ARRIVAL_DELAY`. Severe được định nghĩa là đến chậm ít nhất 60 phút. Xem [quyết định làm sạch gốc](../data_quality_report.md).

## 4. Kiểm tra tổng quan và thời gian

So nhóm giờ khởi hành dự kiến 17–21 với 06–11, theo giờ địa phương:

| Chỉ tiêu tối trừ sáng | Quan sát toàn năm | Khoảng phân vị 2,5–97,5% khi lấy lại mẫu khối 7 ngày |
| --- | ---: | ---: |
| Mean arrival delay | +9,27 phút | +8,41 đến +10,13 phút |
| Severe rate | +4,88 điểm phần trăm | +4,37 đến +5,40 điểm |
| Tỷ số severe rate tối/sáng | 2,35 lần | 2,24 đến 2,46 lần |
| Disruption rate | +5,25 điểm phần trăm | +4,65 đến +5,87 điểm |

Đây là **kiểm tra độ ổn định trong lịch sử 2015**, với 3.000 lần lấy lại mẫu, seed `20261112`. Hai nhóm sáng/tối luôn lấy cùng ngày để giữ các cú sốc chung. Lấy các khối ngày liên tiếp theo vòng tròn trong từng tháng và giữ số ngày của từng tháng; tổng hợp theo số chuyến, không lấy trung bình ngang bằng các tỷ lệ ngày.

Khối 1 ngày cho khoảng mean +8,56 đến +10,02 phút; khối 14 ngày cho +8,46 đến +10,09 phút. Khoảng severe tương ứng là +4,46 đến +5,33 và +4,39 đến +5,39 điểm. Trong các lựa chọn này, hướng khác biệt cuối ngày giữ nguyên. Đây không phải cam kết về các lựa chọn phương pháp khác.

Giả định là phụ thuộc ngắn hạn trong tháng được mô phỏng đủ tốt bởi các khối đã chọn; nối vòng cuối–đầu tháng và không giữ phụ thuộc xuyên tháng là những xấp xỉ. Khối 1 ngày vẫn lấy theo ngày, không coi từng chuyến là độc lập. Các khoảng không mô tả sai số đếm của file đầy đủ, không phải dự báo năm sau và không đo tác động nhân quả của chuyển giờ bay. Chúng áp dụng cho **chênh lệch thô 9,27 phút**, không phải chênh lệch điều chỉnh 10,06 phút trong báo cáo gốc.

Phương pháp tham khảo [tài liệu bootstrap chuỗi thời gian của arch](https://bashtage.github.io/arch/doc/bootstrap/timeseries-bootstraps.html). Mã thực tế triển khai bằng NumPy trong [review_analysis.py](../../scripts/review_analysis.py), không gọi thư viện arch.

## 5. So sánh nhiều chiều: chọn mẫu và chuẩn hóa là hai bước

Mỗi hãng được so với nhóm tất cả hãng còn lại, trên cùng tuyến × tháng × nhóm giờ. Chỉ giữ ô có ít nhất 10 chuyến hoàn tất ở mỗi phía; chuẩn hóa bằng trọng số `min(n_carrier, n_other)` trên chênh lệch trong ô.

| Hãng | Chênh lệch severe thô trên 11 tháng đủ mã | Chênh lệch thô sau chọn tập đối chiếu | Chênh lệch chuẩn hóa trên tập đó | Số chuyến hãng / đối chiếu được giữ |
| --- | ---: | ---: | ---: | ---: |
| NK | +5,26 điểm | +5,36 điểm | +5,47 điểm | 81.016 / 296.019 |
| MQ | +1,94 điểm | +0,12 điểm | +0,17 điểm | 110.498 / 125.398 |

Với MQ, mức giảm từ +1,94 xuống +0,12 xảy ra trước bước chuẩn hóa. Sau đó chuẩn hóa cho +0,17, hơi lớn hơn chênh lệch thô trong tập được giữ. Vì thế, không thể diễn giải toàn bộ sự thu hẹp so với aggregate là thành quả điều chỉnh cơ cấu. Đây là phân biệt các đại lượng đo được, không phải phân rã nhân quả thành các nguyên nhân độc lập.

## 6. Insight mới: NK bền về hướng, MQ nhạy với tập đối chiếu

| Hãng | Cấu hình trong cùng tuyến × tháng | Chênh lệch severe chuẩn hóa | Chuyến hãng được giữ | Độ phủ hãng trong 11 tháng đủ mã |
| --- | --- | ---: | ---: | ---: |
| NK | Nhóm giờ, ngưỡng 10 mỗi phía | +5,47 điểm | 81.016 | 77,1% |
| NK | Nhóm giờ, ngưỡng 30 mỗi phía | +4,61 điểm | 48.758 | 46,4% |
| NK | Từng giờ, ngưỡng 10 mỗi phía | +5,50 điểm | 44.403 | 42,3% |
| MQ | Nhóm giờ, ngưỡng 10 mỗi phía | +0,17 điểm | 110.498 | 43,0% |
| MQ | Nhóm giờ, ngưỡng 30 mỗi phía | +0,09 điểm | 48.369 | 18,8% |
| MQ | Từng giờ, ngưỡng 10 mỗi phía | +1,23 điểm | 28.526 | 11,1% |

Nhóm giờ gồm 06–11, 17–21 và OTHER cho các giờ còn lại. Cấu hình từng giờ giảm gộp giờ nhưng cũng làm mất nhiều chuyến khỏi phạm vi so sánh. Riêng MQ theo từng giờ chỉ có 28.561 chuyến đối chiếu, tương đương 0,57% tổng chuyến hoàn tất của các hãng khác trong 11 tháng đủ mã. Vì vậy, đối chiếu này không đại diện toàn bộ mạng hãng còn lại.

Với NK, cả ba cấu hình đều gợi ý ưu tiên điều tra các phân khúc quan sát được. Với MQ, kết quả không hỗ trợ kết luận ngang bằng toàn mạng; đồng thời cũng chưa chứng minh một cơ chế vận hành gây ra chênh lệch. Nâng ngưỡng hoặc chia giờ không tự động làm mọi mặt của phân tích tốt hơn: độ tương đồng, số chuyến và khả năng khái quát phải được cân nhắc cùng nhau.

## 7. Chẩn đoán nguyên nhân và mức bằng chứng

- **Quan sát trực tiếp:** khác biệt cuối ngày dương; các kết quả chọn mẫu/chuẩn hóa và độ phủ ở trên được tính trên dữ liệu thực.
- **Liên hệ thống kê:** mô hình khác biệt cuối ngày giữ hướng qua các phép lấy lại mẫu đã thử; NK giữ chênh lệch dương trong ba cấu hình.
- **Giả thuyết:** tích lũy chậm qua rotation, mạng tuyến hoặc quy trình khai thác có thể góp phần. Kiểm chứng mới không xác minh các cơ chế này.
- **Chưa đủ dữ liệu:** tác động độc lập của hãng/giờ bay, thời tiết thực tế, bảo dưỡng, crew, hành khách nối chuyến và chi phí. Các phép so carrier chỉ xét chuyến hoàn tất, chưa điều chỉnh sự khác nhau về hủy.

## 8. Ý nghĩa kinh doanh

Rủi ro lớn của cách diễn giải cũ là phân bổ nguồn lực theo một kết luận quá chắc: cho rằng đã giải thích được MQ bằng cơ cấu hoặc quy chênh lệch NK thành lỗi nội bộ. Kết quả mới giúp khoanh phạm vi điều tra, đồng thời giữ riêng vấn đề hủy của MQ. Không có dữ liệu tài chính để lượng hóa thiệt hại hoặc mức tiết kiệm.

## 9. Hành động và thước đo thành công

| Ưu tiên | Hành động / người phụ trách đề xuất | Bằng chứng và cách theo dõi |
| --- | --- | --- |
| Ngay | Analyst/BI owner công bố N, phạm vi tháng và độ phủ cạnh kết quả so hãng; chạy kiểm tra nguồn trước tái sử dụng | Không dùng gate cũ khi nguồn đổi; mọi so sánh có mẫu số và phạm vi rõ |
| Tiếp theo | Airline performance team xác định tuyến–tháng–giờ NK còn chênh lệch; dùng dữ liệu gần hiện tại trước quyết định vận hành | Theo dõi matched severe gap, cancellation/diversion và độ phủ trên tập so cố định |
| Tiếp theo | Nhóm quản lý lịch MQ phân tích hủy theo tuyến/giờ/nguyên nhân riêng với arrival | Cancellation trên scheduled flights; tránh cải thiện mean bằng cách loại chuyến không hoàn tất |
| Điều tra chiến lược | Operations team thử can thiệp rotation/buffer tại nhóm cuối ngày đã xác minh, có đối chứng phù hợp | Severe, p95, disruption, utilization; xác định mục tiêu sau khi có baseline hiện tại |

## 10. Kế hoạch Power BI sau rà soát

Đề xuất bổ sung vào trang Airline Performance bảng ba bước: aggregate → tập đối chiếu chưa chuẩn hóa → chuẩn hóa, kèm số chuyến và độ phủ. Tooltip ghi rõ 11 tháng, ngưỡng chuyến và nhóm giờ. Trang Time Analysis có thể thêm bảng khoảng ổn định lịch sử với chú thích phương pháp; tránh biểu diễn như dự báo.

**Trạng thái thực tế:** lượt rà soát này không sửa hoặc refresh [Aviation_Insights.pbix](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0). Bản 7 trang và [21 đối soát DAX PASS trước đó](../../powerbi/desktop/desktop_verification.json) vẫn là bản đã kiểm định trước rà soát; các khoảng bootstrap và bảng độ nhạy mới chưa có trong Desktop. Các point estimate gốc được tính lại khớp, nhưng bằng chứng Desktop trước đó không xác nhận những bổ sung mới này.

## 11. Skill đã cài và kiểm định công việc

Skill lấy từ [claude-office-skills/skills, revision cố định](https://github.com/claude-office-skills/skills/tree/9c4c7d5cd2813a8936bf2c9fdb174ea883b85a11/data-analysis), giấy phép MIT. Do `node`/`npm`/`npx` không có trên PATH khi kiểm tra, đã dùng installer đi kèm Codex thay cho lệnh `npx`. Bản gốc được giữ để tra cứu và ghi nhận nguồn.

Bản upstream là hướng dẫn tổng quát; dự án đã đáp ứng phần lớn các mục về chất lượng, phân phối, segmentation và business report. Không nên coi việc thêm skill là tự động nâng chất lượng kết quả. Những bổ sung kỹ thuật ở đây là lựa chọn áp dụng cho rủi ro cụ thể của dự án.

Đã chuyển frontmatter về định dạng Codex hợp lệ, bỏ phụ thuộc bắt buộc vào MCP Office và tuyên bố không thể chạy mã; thêm kiểm tra nguồn, mẫu số, độ phủ so sánh và mức độ diễn giải. File chính có thể xem tại [skills/data-analysis/SKILL.md](../../docs/ANALYSIS_METHODS.md), hướng dẫn hàng không nằm riêng trong references. Bản đã cài tại `a local Codex skill installation`; cả bản trong dự án và bản cài đều qua validator. Skill đã xuất hiện trong danh mục của phiên tiếp tục này.

Kiểm định: 10 unit tests đạt PASS, bao gồm chặn nguồn thay đổi/profile dở/gate không hợp lệ, tổng hợp theo số chuyến, bootstrap ghép ngày, seed tái lập và tách chọn mẫu khỏi chuẩn hóa. Trên dữ liệu thực, kiểm chứng mới đạt PASS, tái lập số chuyến và severe gap của hai phép matched NK/MQ gốc cùng chênh lệch thời gian. Lần chạy test trong sandbox gặp lỗi quyền tạo fixture trong thư mục tạm; chạy lại ngoài sandbox đạt đủ 10/10.

## 12. Câu hỏi và phân tích tiếp theo

Cần dữ liệu mới để đánh giá hiện tại, crosswalk tháng 10 đã xác minh để phục hồi địa lý đủ năm, và định nghĩa nhóm hãng đối chiếu phù hợp từng quyết định. Nếu cần khẳng định mức chênh lệch của hãng ổn định theo thời gian, phải kiểm tra theo ngày/khối cho chính contrast đã chuẩn hóa, giữ rõ quần thể mục tiêu; khoảng của so sáng–tối không thể chuyển sang dùng cho so hãng.

Các bằng chứng máy đọc được: [statistical_review.json](statistical_review.json), [bảng độ nhạy carrier](carrier_comparison_sensitivity.csv), [khoảng ổn định theo khối](time_block_stability.csv), [panel ngày ghép cặp](daily_paired_time_panel.csv), [source manifest](../source_manifest.json). Các bảng này được sinh bởi `python scripts/review_analysis.py` sau khi profiling và quality gate hợp lệ.
