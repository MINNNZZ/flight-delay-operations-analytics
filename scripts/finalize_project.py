from pathlib import Path
import json
p=Path(__file__).resolve().parents[1]
v=json.loads((p/'reports/verification.json').read_text(encoding='utf-8'))
assert v['status']=='PASS'
s=(p/'reports/aviation_analysis_report.md').read_text(encoding='utf-8').replace('# Data Description','# Dataset Overview').replace('# Power BI Dashboard Plan','# Power BI Story')
intro="""# Phạm vi và giả định

Tên dự án flight delays and cancellations project. Yêu cầu để trống câu hỏi kinh doanh; tiếp tục điều tra chậm chuyến và độ tin cậy trên dữ liệu hiện có. Đã chạy lại profiling, làm sạch, phân tích nhiều chiều và kiểm định toàn bộ bản xuất. Không sửa AGENTS.md. Không có context hoặc skill aviation-data-analysis riêng khi kiểm tra. Power BI là bản sao kiểm định trước đó; lượt này không refresh Desktop. Kiểm chứng bổ sung nằm trong báo cáo chữ.

"""
(p/'reports/final_analysis_report.md').write_text(intro+s,encoding='utf-8')
(p/'context/analysis_lessons.md').write_text("# Reusable lessons\n\n- Separate original, retained-subset and standardized contrasts; selection changes the estimand.\n- Finer strata require coverage checks.\n- Operational stability resampling should respect paired days and short-run dependence.\n- Match quality gates to source fingerprints and completed profile run IDs.\n- Recorded cause labels are not verified causal mechanisms.\n",encoding='utf-8')
(p/'context/metric_definitions.md').write_text("# Metric rules\n\n- Severe arrival: ARRIVAL_DELAY >=60 among completed flights with valid arrival delay.\n- Cancellation/diversion denominators are scheduled flights.\n- Pool rates using summed numerators and denominators.\n- Separate signed delay, positive delay minutes and reported cause minutes.\n",encoding='utf-8')
(p/'context/known_data_issues.md').write_text("# Reusable checks\n\n- Validate airport joins by month; never guess numeric-code crosswalks.\n- Local HHMM differences need timezone/date offsets.\n- Cancellation outcome missingness may be structural.\n- Calendar assembly requires sufficient numeric precision.\n",encoding='utf-8')
(p/'outputs/completion.json').write_text(json.dumps({'status':'PASS','full_export_verified':True,'powerbi_refreshed':False,'report':'reports/final_analysis_report.md'},indent=2))
print('Final client report saved.')
