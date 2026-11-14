# Data Dictionary

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
