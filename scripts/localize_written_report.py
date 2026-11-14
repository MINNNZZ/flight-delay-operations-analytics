"""Publish a Vietnamese edition while retaining the original report as evidence."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/'reports'
HEADINGS={
    '# Aviation Operations — Client Analysis Report':'# Chậm chuyến và hủy chuyến — Báo cáo khách hàng',
    '# Executive Summary':'# Tóm tắt điều hành', '# Business Problem':'# Bài toán kinh doanh',
    '# Dataset Overview':'# Tổng quan dữ liệu', '# Data Quality Assessment':'# Đánh giá chất lượng dữ liệu',
    '# Cleaning Decisions':'# Quyết định làm sạch', '# Analytical Approach':'# Phương pháp phân tích',
    '# Key Findings':'# Kết quả chính', '# High-Value Insights':'# Những phát hiện có giá trị',
    '# Root-Cause Analysis':'# Điều tra nguyên nhân', '# Business Impact':'# Tác động kinh doanh',
    '# Recommendations':'# Khuyến nghị', '# Power BI Story':'# Câu chuyện Power BI',
    '# Success Metrics':'# Chỉ tiêu đánh giá thành công', '# Limitations':'# Giới hạn', '# Next Steps':'# Bước tiếp theo',
    '## Airline comparison — descriptive, chưa điều chỉnh cơ cấu':'## So sánh hãng — mô tả, chưa điều chỉnh cơ cấu',
    '## Route comparison — 11 tháng, threshold >=1.000 chuyến':'## So sánh tuyến — 11 tháng, ngưỡng >=1.000 chuyến',
    '**Observation / Evidence:**':'**Quan sát / Bằng chứng:**', '**Pattern / Context:**':'**Mẫu hình / Bối cảnh:**',
    '**Challenge:**':'**Kiểm chứng thay thế:**', '**Likely Driver:**':'**Yếu tố khả dĩ:**',
    '**Business Impact / Action:**':'**Ý nghĩa kinh doanh / Hành động:**', '**Evidence:**':'**Bằng chứng:**',
    '**Pattern:**':'**Mẫu hình:**', '**Challenge / Context:**':'**Kiểm chứng / Bối cảnh:**',
    '**Driver / Context:**':'**Yếu tố / Bối cảnh:**','**Limitation:**':'**Giới hạn:**',
    '**Interpretation:**':'**Diễn giải:**', '| KPI | Giá trị | Mẫu số / phạm vi |':'| Chỉ tiêu | Giá trị | Mẫu số / phạm vi |',
    '| Hypothesis | Evidence strength | Kết quả / giới hạn |':'| Giả thuyết | Mức bằng chứng | Kết quả / giới hạn |'
}

APPENDIX='''

# Kiểm chứng bổ sung và hai bản ngôn ngữ

Bản này và [bản tiếng Anh](final_analysis_report_en.md) dùng cùng dữ liệu, định nghĩa và kết luận. Dấu phân cách số có thể theo quy ước khác nhau; mã hãng/sân bay, tên cột và công thức kỹ thuật được giữ nguyên. Các số trong bảng là điểm phần trăm khi so chênh lệch tỷ lệ, không phải phần trăm thay đổi tương đối.

## 6. Khác biệt cuối ngày giữ hướng qua kiểm chứng theo khối ngày

Chênh lệch thô tối trừ sáng là 9,27 phút về mean arrival, 4,88 điểm phần trăm về tỷ lệ chậm nặng, 2,35 lần về tỷ số rủi ro và 5,25 điểm phần trăm về tỷ lệ gián đoạn. Lấy lại mẫu theo khối ngày vòng tròn trong từng tháng, giữ cặp sáng/tối cùng ngày, với 3.000 lần và seed 20261112:

| Chênh lệch | Khoảng phân vị 2,5–97,5%, khối 7 ngày |
| --- | --- |
| Mean arrival tối trừ sáng | +8,41 đến +10,13 phút |
| Tỷ lệ chậm nặng | +4,37 đến +5,40 điểm phần trăm |
| Tỷ số rủi ro chậm nặng | 2,24 đến 2,46 lần |
| Tỷ lệ gián đoạn | +4,65 đến +5,87 điểm phần trăm |

Khối 1 và 14 ngày vẫn giữ hướng: khoảng mean lần lượt là +8,56 đến +10,02 và +8,46 đến +10,09 phút. Đây là độ ổn định lịch sử năm 2015 theo giả định lấy lại mẫu, không phải sai số đếm toàn bộ file, dự báo hoặc tác động nhân quả. Nối vòng cuối–đầu tháng và không giữ phụ thuộc xuyên tháng là các xấp xỉ. Khoảng áp dụng cho chênh lệch thô 9,27 phút, không áp dụng cho chênh lệch chuẩn hóa 10,06 phút hoặc so hãng.

## Cập nhật quan trọng khi diễn giải MQ và NK

| Hãng | Chênh lệch severe thô trên 11 tháng đủ mã | Chênh lệch thô sau chọn tập đối chiếu | Chênh lệch chuẩn hóa trong tập đó |
| --- | --- | --- | --- |
| NK | +5,26 điểm | +5,36 điểm | +5,47 điểm |
| MQ | +1,94 điểm | +0,12 điểm | +0,17 điểm |

Phần lớn mức giảm của MQ đã xuất hiện khi chọn tập chuyến, trước chuẩn hóa. Không được gán toàn bộ thay đổi cho việc điều chỉnh cơ cấu tuyến/tháng/giờ.

| Hãng | Cấu hình cùng tuyến × tháng | Chênh lệch severe chuẩn hóa | Số chuyến hãng giữ lại | Độ phủ hãng trong 11 tháng đủ mã |
| --- | --- | --- | --- | --- |
| NK | Nhóm giờ, ít nhất 10 mỗi phía | +5,47 điểm | 81.016 | 77,1% |
| NK | Nhóm giờ, ít nhất 30 mỗi phía | +4,61 điểm | 48.758 | 46,4% |
| NK | Từng giờ, ít nhất 10 mỗi phía | +5,50 điểm | 44.403 | 42,3% |
| MQ | Nhóm giờ, ít nhất 10 mỗi phía | +0,17 điểm | 110.498 | 43,0% |
| MQ | Nhóm giờ, ít nhất 30 mỗi phía | +0,09 điểm | 48.369 | 18,8% |
| MQ | Từng giờ, ít nhất 10 mỗi phía | +1,23 điểm | 28.526 | 11,1% |

Phép so từng giờ của MQ chỉ có 28.561 chuyến đối chiếu, bằng 0,57% chuyến hoàn tất của các hãng khác trong phạm vi đủ mã. Cấu hình chi tiết hơn giảm gộp giờ nhưng mất nhiều độ phủ; không tự động tốt hơn về khả năng khái quát. NK giữ hướng bất lợi trong ba cấu hình; MQ chưa thể được coi ngang bằng toàn mạng. Các phép so này chưa điều chỉnh khác biệt hủy chuyến.

Bài học cho analyst: phân biệt tác động chọn tập chuyến, chuẩn hóa, liên hệ quan sát và nguyên nhân. Kết quả mạnh hơn khi đã thách thức cách giải thích ban đầu; câu hỏi tiếp theo cần gắn với phân khúc và dữ liệu còn thiếu.

## Power BI theo ngôn ngữ

- [Bản tiếng Việt](../powerbi/desktop/Aviation_Insights_vi.pbix).
- [Bản tiếng Anh](../powerbi/desktop/Aviation_Insights_en.pbix).

Hai bản có cùng dữ liệu và mô hình nhúng, 7 trang và 51 thành phần trực quan; công thức DAX và mã kỹ thuật giữ nguyên. Trang hành động dùng nội dung tĩnh tương đương ở hai ngôn ngữ. Nhãn nguyên nhân trong dữ liệu có thể giữ thuật ngữ nguồn; ngôn ngữ menu Desktop theo cài đặt ứng dụng. Các bảng độ nhạy và khoảng ổn định mới nằm trong báo cáo chữ, chưa thành visual bổ sung. Trạng thái kiểm định riêng của hai bản nằm trong [localization_verification.json](../powerbi/desktop/localization_verification.json); đối soát Desktop trước đó thuộc bản gốc.

Bằng chứng bổ sung: [kiểm chứng thống kê](skill_review/statistical_review.json), [độ nhạy theo hãng](skill_review/carrier_comparison_sensitivity.csv), [độ ổn định theo khối](skill_review/time_block_stability.csv).
'''

def main():
    source=REPORTS/'final_analysis_report.md'
    text=source.read_text(encoding='utf-8')
    # The original is retained as an audit snapshot, not used as a language index.
    for old,new in HEADINGS.items():
        text=text.replace(old,new)
    text=text.replace('15,187 chuyến đổi hướng. Tổng **430,662','15,187 chuyến đổi hướng**. Tổng **430,662')
    text=text.replace('Đã dựng và mở lại [báo cáo Power BI Desktop 7 trang]', 'Bản gốc đã được dựng và mở lại dưới dạng [báo cáo Power BI Desktop 7 trang]')
    (REPORTS/'final_analysis_report_vi.md').write_text(text+APPENDIX,encoding='utf-8')
    out={'status':'WRITTEN_EDITIONS_CREATED','source_report_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'vi':'final_analysis_report_vi.md','en':'final_analysis_report_en.md','note':'English is an edited full client edition, not a machine-generated translation. Both retain baseline and updated robustness conclusions.'}
    (REPORTS/'language_editions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Vietnamese edition created; English client edition retained.')

if __name__=='__main__':main()
