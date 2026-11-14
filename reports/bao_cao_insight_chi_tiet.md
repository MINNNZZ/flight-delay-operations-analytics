# Báo cáo diễn giải chi tiết: chậm chuyến và độ tin cậy vận hành

Ngày viết: 12/11/2026. Phạm vi: dữ liệu chuyến bay năm 2015 trong dự án. Đây là bản diễn giải bằng chữ từ kết quả phân tích đã đối soát, dành cho người đọc muốn hiểu insight và ý nghĩa kinh doanh mà không cần đọc mã, bảng số hoặc biểu đồ.

Bản cập nhật áp dụng skill `data-analysis` bổ sung kiểm tra độ bền theo ngày và tách ảnh hưởng chọn tập chuyến khi so sánh hãng. Xem phần cập nhật dưới đây và [báo cáo rà soát kèm bằng chứng](skill_review/analysis_improvement_review.md).

## Tóm tắt điều hành

Điều đáng chú ý nhất trong bộ dữ liệu này là sự khác biệt giữa chuyến bay điển hình và nhóm chuyến gặp gián đoạn nghiêm trọng. Chuyến điển hình đến sớm, nhưng vẫn có hàng trăm nghìn chuyến đến chậm ít nhất một giờ. Vì vậy, doanh nghiệp có thể đạt một mức chậm trung bình khá thấp mà vẫn phải xử lý khối lượng lớn sự cố, đổi lịch và phục hồi vận hành.

Rủi ro cũng không phân bố đều. Nhóm khởi hành từ 17 đến 21 giờ có tỷ lệ chậm nặng cao hơn nhiều so với nhóm 6 đến 11 giờ. Sự khác biệt này còn xuất hiện sau khi so sánh các nhóm chuyến có cùng hãng, sân bay đi và tháng. Kết quả phù hợp với giả thuyết chậm tích lũy hoặc lan truyền trong ngày, nhưng chưa đủ để xác định từng chuỗi quay vòng máy bay gây ra vấn đề.

Ở góc độ địa điểm, ORD nổi bật vì tổng số phút chậm lớn, còn LGA nổi bật vì tỷ lệ gián đoạn cao. Ở góc độ thời gian trong năm, tháng 2 nổi bật về hủy chuyến, còn tháng 6 nổi bật về chậm nặng. Ở góc độ hãng, NK có rủi ro chậm nặng cao ngay cả trong một số so sánh có điều chỉnh cơ cấu, trong khi MQ cần được xem xét kỹ về hủy chuyến và khác biệt mạng khai thác.

Những phát hiện này hỗ trợ một cách ưu tiên cụ thể: xác minh lại bằng dữ liệu đủ mới, sau đó tập trung điều tra vào khả năng phục hồi cuối ngày, các sân bay/tuyến có quy mô tác động lớn và những phân khúc có rủi ro cao. Chưa có cơ sở để đưa ra mức tiết kiệm tài chính, kết luận lỗi kỹ thuật tàu bay hoặc thay đổi lịch toàn mạng.

## Câu hỏi kinh doanh và cách đọc báo cáo

Câu hỏi làm việc là: gián đoạn chuyến bay đang nghiêm trọng đến đâu, tập trung ở đâu và khi nào, nhóm nào bị ảnh hưởng, bằng chứng đang ủng hộ cơ chế nào, và quản lý nên điều tra hoặc thử nghiệm hành động gì trước?

Một chuyến được gọi là “chậm nặng” trong báo cáo nếu đến chậm từ 60 phút trở lên. Đây là ngưỡng phục vụ điều hành của nghiên cứu. “Đến đúng giờ” được xác định là đến sớm hoặc chậm dưới 15 phút. Tỷ lệ chậm nặng và đúng giờ được tính trên các chuyến hoàn tất có số liệu đến; tỷ lệ hủy, đổi hướng và gián đoạn tổng hợp dùng toàn bộ số chuyến theo lịch.

“Gián đoạn tổng hợp” ở đây gồm chuyến hủy, chuyến đổi hướng hoặc chuyến hoàn tất đến chậm từ 60 phút. Trong dữ liệu, các nhóm này không chồng lấn. Không nên hiểu tỷ lệ này là tỷ lệ hành khách bị ảnh hưởng: một chuyến có thể chở nhiều hoặc ít khách, mà dữ liệu không có số khách để quy đổi.

Khi báo cáo nói một mối liên hệ “còn tồn tại sau kiểm chứng”, điều đó có nghĩa là một số lời giải thích thay thế đã được kiểm tra. Nó không có nghĩa đã loại bỏ tất cả yếu tố gây nhiễu hoặc chứng minh quan hệ nhân quả.

## Dữ liệu đủ tin cậy ở phần nào?

Phân tích sử dụng 5.819.079 dòng chuyến bay, danh mục 322 sân bay và 14 hãng. Dữ liệu phủ đủ 365 ngày năm 2015. Kiểm tra trước phân tích không phát hiện trùng toàn dòng, trùng khóa chuyến ghép, ngày sai, thứ sai hoặc cờ hủy/đổi hướng ngoài giá trị hợp lệ. Toàn bộ dữ liệu xuất đã được đọc lại và đối chiếu các cột nguồn, số dòng và các tổng quan trọng; kết quả kiểm định là PASS.

Tuy nhiên, chất lượng được phân loại READY WITH WARNINGS. Hạn chế lớn nhất là 486.165 chuyến của tháng 10 sử dụng mã sân bay dạng số ở cả hai đầu, trong khi danh mục đi kèm sử dụng mã IATA. Chưa có bảng đối chiếu được xác minh để biết chính xác các mã số tương ứng với sân bay nào. Vì vậy, những chuyến này vẫn được giữ trong số liệu toàn hệ thống, hãng và thời gian, nhưng không được đưa vào xếp hạng sân bay/tuyến có tên.

Điều này có ý nghĩa thực tế: mọi kết luận địa lý trong báo cáo chỉ đại diện cho 11 tháng nhận diện được, không phải xếp hạng đủ cả năm. Tháng 10 có hiệu suất tốt hơn mức trung bình năm; khi loại tháng này, mức chậm đến trung bình tăng từ 4,41 lên 4,89 phút và tỷ lệ chậm nặng tăng từ 5,70% lên 5,91%. Không thể ngoại suy rằng các sân bay sẽ giữ nguyên vị trí nếu bổ sung được tháng còn thiếu.

Một điểm quan trọng khác là dữ liệu thiếu có ý nghĩa nghiệp vụ. Có 105.071 dòng thiếu ARRIVAL_DELAY, khớp chính xác 89.884 chuyến hủy cộng 15.187 chuyến đổi hướng. Điền những giá trị này bằng 0 sẽ biến chuyến hủy hoặc đổi hướng thành chuyến “không chậm” trong một phép tính sai. Vì thế, dữ liệu thiếu được giữ nguyên và mẫu số được xác định riêng cho từng chỉ tiêu.

Hai dòng có mâu thuẫn thời gian đã được gắn cờ, không đoán sửa. Các trường hợp đến rất muộn, hủy chuyến và đổi hướng đều được bảo toàn. Mục tiêu làm sạch là giữ được thông tin có giá trị để hiểu vận hành, đồng thời ngăn thông tin không đáng tin làm sai kết luận.

Cuối cùng, đây là dữ liệu năm 2015, không phản ánh trực tiếp tình hình năm 2026. Những ứng viên ưu tiên bên dưới là kết quả lịch sử cần được tái xác nhận trước khi áp dụng vào vận hành hiện tại.

## Insight 1 — Chuyến bay điển hình khá ổn, nhưng quy mô gián đoạn vẫn lớn

Trong 5.819.079 chuyến theo lịch, có 5.714.008 chuyến hoàn tất mà không bị hủy hoặc đổi hướng. Với nhóm này, mức chậm đến trung bình là 4,41 phút, trong khi trung vị là -5 phút, tức chuyến ở giữa phân phối đến sớm 5 phút.

Hai con số đó không mâu thuẫn. Trung vị mô tả vị trí giữa của các quan sát; trung bình chịu ảnh hưởng của cả các chuyến đến sớm lẫn những chuyến đến rất muộn. Dữ liệu có nhiều chuyến đến sớm nhưng cũng có một phần đuôi chậm dài. Vì vậy, kết luận “vận hành nhìn chung chỉ chậm vài phút” không đủ để mô tả mức độ rủi ro phục hồi.

Cụ thể, 325.591 chuyến hoàn tất đến chậm ít nhất 60 phút, tương đương 5,70% số chuyến hoàn tất. Bên cạnh đó còn 89.884 chuyến hủy và 15.187 chuyến đổi hướng. Cộng ba nhóm không trùng nhau này, có 430.662 chuyến gián đoạn theo định nghĩa nghiên cứu, tương đương 7,40% toàn bộ lịch bay. Có thể hình dung là khoảng 7,4 chuyến trên mỗi 100 chuyến theo lịch thuộc nhóm cần chú ý này, chứ không phải chỉ những chuyến còn xuất hiện trong bảng arrival delay.

Tỷ lệ đến đúng giờ cũng cần được đọc theo hai cách. Trong các chuyến hoàn tất, tỷ lệ này là 81,39%. Nếu giữ cùng số chuyến đúng giờ ở tử số nhưng chia cho toàn bộ lịch bay, tỷ lệ còn 79,92%. Chênh lệch không phải lỗi tính toán; nó cho thấy trải nghiệm hoàn thành lịch đúng giờ thấp hơn mức đúng giờ có điều kiện đã khai thác thành công.

Với doanh nghiệp, phát hiện này gợi ý rằng quản lý độ tin cậy cần theo dõi đồng thời chuyến hoàn tất, chuyến hủy và chuyến đổi hướng. Một chỉ tiêu mean hoặc một tỷ lệ on-time duy nhất có thể không thể hiện đầy đủ khối lượng phục hồi vận hành.

Điều cần làm là đặt cạnh nhau tỷ lệ chậm nặng, tỷ lệ hủy, tỷ lệ đổi hướng, tỷ lệ đúng giờ trên toàn lịch và số chuyến theo lịch. Khi một chỉ tiêu cải thiện, cần kiểm tra xem chỉ tiêu khác có xấu đi hay không. Chẳng hạn, không nên gọi là thành công nếu arrival delay giảm chỉ vì nhiều chuyến khó khai thác đã bị hủy; báo cáo này không khẳng định điều đó đã xảy ra, mà nêu phép kiểm tra cần có.

Bài học phân tích là phải xác định đúng tập đối tượng trước khi giải thích một tỷ lệ. “Đúng giờ trong số chuyến đã hoàn tất” và “hoàn thành đúng giờ trong toàn bộ lịch” là hai câu hỏi kinh doanh khác nhau.

## Insight 2 — Cuối ngày là phân khúc rủi ro cao, và khác biệt không chỉ đến từ cơ cấu chuyến

Nhóm khởi hành theo lịch từ 6 đến 11 giờ có 2.263.032 chuyến, trong đó 2.225.963 chuyến hoàn tất. Mức chậm đến trung bình là 0,20 phút; trung vị đến sớm 7 phút; tỷ lệ chậm nặng là 3,61%.

Nhóm khởi hành từ 17 đến 21 giờ có 1.502.979 chuyến theo lịch, trong đó 1.470.984 chuyến hoàn tất. Mức chậm đến trung bình tăng lên 9,47 phút, trung vị chỉ còn đến sớm 2 phút và tỷ lệ chậm nặng tăng lên 8,49%. Như vậy, rủi ro chậm nặng của nhóm tối khoảng 2,35 lần nhóm sáng, chênh khoảng 4,88 điểm phần trăm. Đây là giờ khởi hành theo lịch tại địa phương, không phải giờ đến hoặc một múi giờ chung cho toàn hệ thống.

Nếu chỉ dừng ở đây, vẫn có thể đặt câu hỏi: có phải buổi tối tập trung những hãng, sân bay hoặc tháng vốn có rủi ro cao hơn? Để kiểm tra, phân tích so nhóm sáng và tối trong cùng hãng, cùng sân bay đi và cùng tháng, chỉ giữ các nhóm có ít nhất 30 chuyến hoàn tất ở mỗi khung giờ. Có 5.401 nhóm đủ điều kiện, gồm 1.791.184 chuyến sáng và 1.257.762 chuyến tối.

Sau khi tổng hợp các chênh lệch trong nhóm với trọng số dựa trên quy mô của phía nhỏ hơn, nhóm tối vẫn có mức chậm trung bình cao hơn 10,06 phút và tỷ lệ chậm nặng cao hơn 5,26 điểm phần trăm. Khoảng 82,26% các nhóm so sánh có chênh lệch mean cùng chiều. Một kiểm chứng riêng theo cùng tuyến và tháng cũng cho chênh lệch mean 10,52 phút. Hai cách kiểm chứng này không đồng thời kiểm soát toàn bộ các biến trong một mô hình duy nhất.

Kết quả còn xuất hiện theo chiều rộng: mean của nhóm tối cao hơn nhóm sáng khi xem riêng từng tháng trong 12 tháng và từng hãng trong 14 hãng. Khi loại các chuyến đến chậm trên 360 phút, mean nhóm sáng là -0,49 phút và nhóm tối là 9,10 phút. Vì vậy, vài chuyến đặc biệt cực đoan không giải thích hết sự khác biệt này.

Nếu tính cả hủy và đổi hướng, tỷ lệ gián đoạn tổng hợp tăng từ 5,19% buổi sáng lên 10,43% buổi tối. Điều này cho thấy phát hiện không chỉ dựa trên nhóm chuyến hoàn tất còn quan sát được arrival delay.

Giả thuyết đáng điều tra là những chậm trễ từ trước tiếp tục lan sang các chuyến sau, trong khi khả năng phục hồi có thể khác nhau theo lịch quay vòng và nguồn lực trong ngày. Đây là giả thuyết phù hợp với dữ liệu, chưa phải kết luận rằng tất cả chênh lệch do thiếu buffer hoặc thiếu máy bay. Dữ liệu chưa có đầy đủ múi giờ, ngày thực tế của từng sự kiện và liên kết rotation để kiểm tra từng chuỗi chuyến.

Hành động phù hợp là chọn các tuyến và khung giờ tối có tác động lớn để kiểm tra lịch quay đầu, thời gian dự phòng và cách bố trí nguồn lực phục hồi. Không nên tăng buffer đồng loạt khi chưa biết ảnh hưởng đến năng suất khai thác. Sau khi có dữ liệu mới và thiết kế thử nghiệm, cần theo dõi tỷ lệ chậm nặng, gián đoạn và mức chậm ở phần đuôi, đồng thời bảo đảm tỷ lệ hủy không tăng.

## Insight 3 — ORD và LGA cần hai cách ưu tiên khác nhau

Trong 11 tháng nhận diện được sân bay, các chuyến khởi hành từ ORD có 285.884 chuyến theo lịch và tạo 4.482.201 phút chậm đến dương. Đây là tổng lớn nhất theo sân bay đi trong phạm vi đã phân tích, chiếm khoảng 6,86% tổng phút chậm dương của phạm vi địa lý. Tỷ lệ chậm nặng là 8,43% trên 276.554 chuyến hoàn tất.

LGA có quy mô nhỏ hơn, với 99.605 chuyến theo lịch và 94.834 chuyến hoàn tất, nhưng tỷ lệ chậm nặng là 8,77% và tỷ lệ hủy là 4,55%. Trong nhóm sân bay đi có ít nhất 10.000 chuyến theo lịch, LGA có tỷ lệ chậm nặng cao nhất. Gián đoạn tổng hợp ở các chuyến khởi hành từ LGA là 13,14%, so với 11,42% ở ORD.

Sự khác biệt có ý nghĩa cho quyết định quản lý. Nếu mục tiêu là điều tra nơi có tổng lượng chậm lớn, ORD là ứng viên quan trọng. Nếu mục tiêu là tìm phân khúc có xác suất gián đoạn cao, LGA đáng chú ý. Hai mục tiêu này có thể dẫn đến thứ tự ưu tiên khác nhau, nên một danh sách “sân bay tệ nhất” duy nhất thường không đủ.

Khi kết hợp địa điểm và thời điểm, rủi ro hiện rõ hơn. Ở LGA, tỷ lệ gián đoạn của nhóm khởi hành sáng là 8,51%, còn nhóm tối là 19,64%. Mean arrival chuyển từ đến sớm 1,30 phút sang đến chậm 14,85 phút. Ở ORD, tỷ lệ gián đoạn tăng từ 8,20% sáng lên 14,80% tối. Do đó, dữ liệu gợi ý kiểm tra các hoạt động cuối ngày tại những địa điểm này thay vì mặc định mọi khung giờ có cùng vấn đề.

Tuy nhiên, kết quả theo sân bay đi phản ánh kết quả của những chuyến khởi hành từ sân bay đó. Nó không tự chỉ ra rằng nguyên nhân phát sinh tại sân bay đi. Một chuyến rời ORD có thể đến chậm vì điều kiện tại điểm đến, vì máy bay từ chặng trước đến muộn hoặc vì các yếu tố khác. Muốn chẩn đoán, cần tiếp tục phân đoạn theo hãng, tuyến, khung giờ và nguyên nhân được ghi nhận.

Đồng thời, phân tích đóng góp cho thấy top 10 sân bay theo phút chậm chiếm 38,30% phút chậm nhưng cũng chiếm 36,33% số chuyến trong phạm vi địa lý. Có sự tập trung về khối lượng, nhưng chưa phải bằng chứng cho một quy luật kiểu “một nhóm sân bay rất nhỏ gây gần hết vấn đề”. Quy mô khai thác giải thích một phần lớn lượng chậm cộng dồn.

Hành động hợp lý là lập danh sách ưu tiên có cả quy mô, tỷ lệ và khung giờ, rồi chọn tổ hợp cụ thể để điều tra. Chưa có cơ sở từ các bảng này để kết luận phải mở rộng sân bay, giảm công suất lịch toàn ngày hoặc quy trách nhiệm chung cho một sân bay.

## Insight 4 — Tuyến có tỷ lệ rủi ro cao chưa chắc là nơi tạo nhiều tác động nhất

Tuyến ORD → JFK có 1.577 chuyến theo lịch và 1.538 chuyến hoàn tất trong 11 tháng nhận diện được. Có 209 chuyến đến chậm ít nhất một giờ, tương đương 13,59% số chuyến hoàn tất. Đây là tuyến có tỷ lệ chậm nặng cao nhất trong nhóm tuyến có ít nhất 1.000 chuyến theo lịch của phân tích này.

Trong khi đó, SFO → LAX có 13.744 chuyến theo lịch và 13.400 chuyến hoàn tất. Tỷ lệ chậm nặng là 8,42%, thấp hơn ORD → JFK, nhưng có 1.128 sự kiện chậm nặng và tổng 222.421 phút chậm dương, nhiều nhất trong các tuyến đã nhận diện. ORD → JFK tạo 36.528 phút chậm dương. Chênh lệch quy mô khiến hai tuyến đại diện cho hai loại ưu tiên khác nhau.

Nếu câu hỏi là “ở tuyến nào xác suất một chuyến hoàn tất bị chậm nặng cao?”, ORD → JFK là tín hiệu mạnh. Nếu câu hỏi là “tuyến nào có khối lượng chậm cộng dồn lớn để điều tra?”, SFO → LAX đáng chú ý. Không thể dùng một tỷ lệ để trả lời câu hỏi thứ hai mà bỏ qua số chuyến.

Tuyến LGA → GSO còn cho thấy vì sao phải giữ hủy chuyến trong bức tranh. Trong 1.295 chuyến theo lịch có 134 chuyến hủy, tương đương 10,35%. Tỷ lệ chậm nặng trong 1.160 chuyến hoàn tất là 13,36%, nhưng tỷ lệ gián đoạn tổng hợp trên toàn lịch lên đến 22,39%. Chỉ nhìn mean hoặc severe của các chuyến đã hoàn tất sẽ chưa thể hiện đủ vấn đề của tuyến này.

Nhóm 20% tuyến đứng đầu theo tổng phút chậm dương gồm 939 trong 4.693 tuyến nhận diện được. Nhóm này tạo 60,37% phút chậm dương, nhưng cũng chiếm 56,67% số chuyến. Điều đó cho phép ưu tiên một danh sách tuyến có tác động cộng dồn lớn, nhưng không nên quảng diễn thành bằng chứng rằng một nhóm nhỏ khai thác kém là nguyên nhân chính của toàn mạng.

Để chọn tuyến thử nghiệm, doanh nghiệp cần đặt cạnh nhau tổng khối lượng, xác suất gián đoạn, khả năng can thiệp và mức độ tin cậy của bằng chứng. Không thể từ số phút chậm suy trực tiếp ra lợi ích tài chính của việc sửa tuyến khi chưa có tải khách, chi phí và phương án can thiệp.

## Insight 5 — Tháng có nhiều hủy chuyến không đồng nhất với tháng có nhiều chậm nặng

Tháng 2 có 20.517 chuyến hủy trên 429.191 chuyến theo lịch, tương đương 4,78%, cao nhất trong các tháng của dữ liệu. Tỷ lệ gián đoạn tổng hợp là 11,93%, cho thấy vấn đề không chỉ nằm ở mức chậm của các chuyến vẫn khai thác được.

Tháng 6 có tỷ lệ hủy thấp hơn, 1,81%, nhưng tỷ lệ chậm nặng cao nhất, 8,15% trên 492.847 chuyến hoàn tất. Có 40.171 chuyến hoàn tất đến chậm ít nhất một giờ trong tháng này. Mean arrival là 9,60 phút, trong khi trung vị vẫn đến sớm 3 phút. Điều này tiếp tục cho thấy một phần lớn chuyến có thể hoạt động khá ổn trong khi nhóm gặp sự cố chịu chậm đáng kể.

Từ đây, doanh nghiệp nên tách câu hỏi “làm thế nào bảo vệ việc hoàn thành lịch bay?” khỏi “làm thế nào giảm chậm trên các chuyến còn hoạt động?”. Hai câu hỏi có thể đòi hỏi điều tra và quy trình phục hồi khác nhau. Một chỉ tiêu mean chung theo tháng sẽ không chỉ ra rõ sự khác biệt này.

Trong toàn bộ 89.884 chuyến hủy, có 48.851 chuyến mang mã weather, tương đương 54,35%; 25.262 mang mã airline; 15.749 mang mã NAS và 22 mang mã security. Đây là các nhãn ghi nhận trong dữ liệu. Chúng hỗ trợ việc xem xét quy trình ứng phó gián đoạn được báo cáo liên quan đến thời tiết, nhưng không đủ để xác minh một sự kiện khí tượng cụ thể hoặc quy mọi hủy trong tháng 2 cho thời tiết.

Một lỗi diễn giải dễ gặp là thấy WEATHER_DELAY chỉ chiếm 4,95% phút nguyên nhân của nhóm chuyến đến chậm rồi cho rằng thời tiết ít quan trọng. Con số 4,95% và con số 54,35% đang mô tả hai quần thể và hai đại lượng khác nhau: phút nguyên nhân của chuyến chậm so với số chuyến hủy. Không thể dùng một tỷ trọng để phủ nhận tỷ trọng kia. Hơn nữa, các nhóm nguyên nhân báo cáo không phải một phép phân rã nhân quả độc lập của mọi tác động thực tế.

Hành động nên ưu tiên là xây dựng hai hướng theo dõi: hủy và khả năng khôi phục lịch; chậm nặng và khả năng ngăn chậm lan truyền. Dữ liệu mới cần được dùng để xem những mẫu theo tháng này có lặp lại hay không. Một năm quan sát chưa đủ để khẳng định quy luật mùa ổn định qua nhiều năm.

## Insight 6 — Xếp hạng hãng thay đổi khi so sánh trong điều kiện gần giống nhau

Theo danh mục đi kèm, NK là Spirit Air Lines, MQ được ghi là American Eagle Airlines Inc. Các tên này được dùng theo dữ liệu lịch sử, không tự cập nhật thành tên pháp nhân hoặc mạng khai thác hiện tại.

NK có 117.379 chuyến theo lịch và 115.193 chuyến hoàn tất. Tỷ lệ chậm nặng là 10,64%, cao nhất trong 14 mã hãng quan sát được. MQ có 294.632 chuyến theo lịch và tỷ lệ hủy 5,10%, cao nhất trong nhóm hãng; tỷ lệ chậm nặng của các chuyến hoàn tất là 7,40%.

Nếu chỉ nhìn bảng tổng hợp, dễ đi đến kết luận cả hai hãng đều có hiệu suất chậm nặng kém hơn vì một nguyên nhân nội tại tương tự. Nhưng hãng khác nhau khai thác các tuyến, sân bay, thời điểm và tháng khác nhau. Một phần chênh lệch có thể đến từ điều kiện khai thác thay vì cùng một cơ chế nội bộ.

Để thách thức kết luận ban đầu, phân tích so từng hãng với nhóm các hãng còn lại trong cùng tuyến, cùng tháng và cùng nhóm giờ, chỉ giữ những nhóm có ít nhất 10 chuyến hoàn tất ở cả hai phía. Đối với NK, có 2.879 nhóm đủ điều kiện với 81.016 chuyến NK và 296.019 chuyến đối chiếu. Sau tổng hợp có trọng số, NK vẫn có tỷ lệ chậm nặng cao hơn 5,47 điểm phần trăm và mean arrival cao hơn 11,92 phút.

Đối với MQ, 2.875 nhóm đủ điều kiện gồm 110.498 chuyến MQ và 125.398 chuyến đối chiếu. Chênh lệch tỷ lệ chậm nặng chỉ còn 0,17 điểm phần trăm; mean arrival của MQ còn thấp hơn nhóm đối chiếu 2,16 phút. Đây là thay đổi quan trọng so với cách đọc bảng tổng hợp ban đầu.

Kiểm chứng bổ sung cho thấy cần thận trọng hơn với MQ. Trong phạm vi 11 tháng nhận diện được sân bay, chênh lệch chậm nặng ban đầu là +1,94 điểm phần trăm. Khi chỉ giữ tập chuyến đủ điều kiện đối chiếu, chênh lệch thô đã giảm xuống +0,12 điểm; chuẩn hóa trong chính tập đó cho +0,17 điểm. Như vậy, thay đổi lớn xảy ra ngay ở bước chọn tập chuyến. Không thể gán toàn bộ mức giảm cho việc điều chỉnh cơ cấu tuyến và thời gian, hoặc kết luận rằng phép so sánh đã tìm ra nguyên nhân.

Khi chia theo từng giờ thay vì nhóm giờ rộng, chênh lệch chuẩn hóa của MQ là +1,23 điểm phần trăm, với 28.526 chuyến MQ và 28.561 chuyến đối chiếu. Phép so này chỉ giữ 11,1% chuyến MQ hoàn tất trong phạm vi địa lý đủ mã, so với 43,0% ở phép so nhóm giờ ban đầu. Hai kết quả trả lời cho các tập chuyến khác nhau; chưa thể coi MQ ngang bằng toàn mạng hoặc cho rằng độ chính xác cao hơn chỉ vì chia giờ chi tiết hơn. Cả hai vẫn chưa điều chỉnh chênh lệch hủy chuyến.

Với NK, dấu hiệu bất lợi giữ cùng chiều qua ba cấu hình: +5,47 điểm phần trăm ở nhóm giờ với tối thiểu 10 chuyến mỗi phía; +4,61 điểm khi nâng ngưỡng lên 30; +5,50 điểm khi so từng giờ và ngưỡng 10. Tỷ lệ chuyến NK được giữ lần lượt là 77,1%, 46,4% và 42,3%. Điều này củng cố ưu tiên điều tra các phân khúc NK quan sát được, nhưng không xác định lỗi vận hành hay mức chênh lệch nhân quả cho toàn hãng.

Ý nghĩa quản trị là hướng điều tra đối với NK và MQ nên khác nhau. Với NK, cần tiếp tục xác định những tuyến/tháng/khung giờ vẫn có chênh lệch sau so sánh tương đồng. Với MQ, không nên bỏ qua hủy chuyến hoặc mặc định mean của chuyến hoàn tất chứng minh lỗi vận hành nội bộ. Cần phân tích riêng hủy theo địa điểm, thời gian và nguyên nhân ghi nhận.

Đây là một bài học quan trọng: khi một kết luận yếu đi sau phân đoạn, nhà phân tích nên nói rõ điều đó. Tìm ra lời giải thích ban đầu chưa đủ vững cũng là một kết quả có giá trị, vì nó giúp tránh hành động sai.

## Insight 7 — Có bằng chứng về nhóm nguyên nhân, nhưng chưa xác định đủ nguyên nhân gốc

Dữ liệu có 1.063.439 chuyến hoàn tất đến chậm từ 15 phút trở lên và có đầy đủ năm cột nguyên nhân. Tổng phút của năm nhóm bằng đúng arrival delay trong từng dòng thuộc nhóm này, cộng lại là 62.651.867 phút. Sự khớp đó xác nhận tính nhất quán nội bộ của phân bổ nguyên nhân, không xác nhận độc lập rằng việc gán nhãn phản ánh đầy đủ cơ chế thực tế.

Trong số phút nguyên nhân được ghi nhận, late aircraft chiếm 24.961.931 phút, tương đương 39,84%; airline chiếm 20.172.956 phút, tương đương 32,20%; air system/NAS chiếm 14.335.762 phút, tương đương 22,88%; weather chiếm 4,95% và security khoảng 0,13%.

Late aircraft là nhóm lớn nhất, đồng thời dữ liệu cho thấy kết quả xấu hơn ở cuối ngày. Hai bằng chứng cùng hướng làm cho giả thuyết chậm lan truyền và lịch quay vòng trở thành ưu tiên điều tra hợp lý. Tuy nhiên, muốn xác minh chuỗi lan truyền phải biết chuyến trước của cùng tàu bay, thời điểm đến và đi quy về đúng ngày/múi giờ, thời gian quay đầu theo lịch, thay tàu bay và các hành động phục hồi. Chỉ sắp xếp TAIL_NUMBER theo giờ HHMM sẽ không đủ tin cậy.

Nhóm airline cũng cần được mở tiếp. Một nhãn airline trong dữ liệu không cho phép phân biệt chắc chắn lỗi bảo dưỡng, tổ bay, mặt đất hay một quy trình cụ thể. Tương tự, NAS là nhóm tổng hợp; không thể đổi tên toàn bộ 22,88% này thành “tắc nghẽn sân bay” rồi kết luận cần tăng công suất.

Hai nhóm late aircraft và airline cộng lại chiếm 72,04% phút nguyên nhân được ghi nhận. Mẫu số này cần được giữ rõ. Toàn bộ phút chậm đến dương, bao gồm cả chuyến chậm dưới 15 phút, là 69.103.367 phút. Vì vậy, không thể nói 72,04% mọi phút chậm hoặc mọi chi phí được giải thích bởi hai nhóm đó.

Hướng hành động là dùng các nhãn để chọn nơi cần mở hồ sơ điều tra, sau đó đối chiếu với dữ liệu vận hành độc lập. Mức tin cậy cao nhất hiện tại nằm ở việc “đã ghi nhận bao nhiêu phút cho từng nhóm”. Mức tin cậy thấp hơn nằm ở việc “thay đổi quy trình cụ thể nào sẽ giảm được bao nhiêu phút”.

## Insight 8 — Các chuyến cực đoan cần được giữ, nhưng không giải thích toàn bộ vấn đề

Trong nhóm chuyến hoàn tất, phân vị 90 của arrival delay là 34 phút, phân vị 95 là 66 phút và phân vị 99 là 167 phút. Nói đơn giản, khoảng 95% quan sát có mức chậm không vượt quá 66 phút, còn phần đuôi phía trên có thể muộn hơn nhiều. Chuyến chậm đến lớn nhất trong tệp là 1.971 phút.

Có 6.089 chuyến đến chậm trên 360 phút, khoảng 0,11% số chuyến hoàn tất. Nhóm rất nhỏ này tạo 4,64% tổng phút chậm dương. Do đó, những quan sát cực đoan có tác động thực đến chỉ tiêu trung bình và khối lượng phục hồi, nên không nên bị xóa chỉ vì nằm xa phần lớn dữ liệu. Đồng thời, chưa có bằng chứng đủ để xác minh từng quan sát lớn nhất là sự kiện vận hành thật hay lỗi ghi nhận; cần giữ và gắn vào danh sách kiểm tra.

Phép phân tích nhạy cảm cho thấy nếu loại nhóm trên 360 phút khỏi phép tính, mean giảm từ 4,41 còn 3,85 phút, trung vị vẫn -5 phút, và tỷ lệ chậm nặng còn 5,60% so với 5,70% ban đầu. Chênh lệch sáng–tối cũng còn tồn tại. Vì vậy, lời giải thích “chỉ vài chuyến rất bất thường kéo hỏng mọi kết quả” không được dữ liệu ủng hộ.

Đối với quản lý, điều này dẫn đến hai lớp công việc song song. Lớp thứ nhất là cải thiện độ tin cậy thường xuyên trên các phân khúc có rủi ro lặp lại. Lớp thứ hai là năng lực ứng phó những tình huống rất nghiêm trọng nhưng ít gặp. Nếu chỉ theo dõi mean, một trong hai lớp có thể bị bỏ sót.

Không nên diễn giải 69,10 triệu phút chậm dương thành số phút hành khách mất hoặc số giờ máy bay mất. Đây là tổng phút chậm của các chuyến, và tác động lan truyền có thể xuất hiện ở nhiều chặng. Để đo hậu quả thực đối với khách, tổ bay hoặc tài chính, cần nối thêm dữ liệu tương ứng.

## Tác động kinh doanh đã biết và tác động chưa đo được

Điều đã đo được là số chuyến, xác suất gián đoạn trong từng tập chuyến, phân phối mức chậm, sự tập trung theo địa điểm/thời gian và các nhóm nguyên nhân được báo cáo. Những đại lượng này đủ để lựa chọn phạm vi điều tra và thiết kế thử nghiệm cải thiện.

Điều chưa đo được là số hành khách lỡ nối chuyến, chi phí đổi lịch, nghĩa vụ bồi thường, giờ tổ bay bị mất, năng suất tàu bay bị giảm hoặc doanh thu bị ảnh hưởng. Các cơ chế này hợp lý về mặt vận hành nhưng không có đủ dữ liệu để lượng hóa trong nghiên cứu này. Báo cáo không gán một đơn giá giả định cho mỗi phút chậm để tạo ra con số tiết kiệm.

Kết quả kinh doanh mong đợi từ việc dùng báo cáo là ưu tiên đúng phân khúc và giảm các quyết định dựa trên chỉ tiêu tổng hợp dễ gây hiểu nhầm. Lợi ích cụ thể của từng biện pháp phải được kiểm chứng bằng dữ liệu mới và một thiết kế đo lường phù hợp.

## Thứ tự hành động đề xuất

Trước hết, chủ sở hữu dữ liệu cần xác minh nguồn, lấy kỳ dữ liệu đủ mới và bổ sung bảng đối chiếu mã sân bay tháng 10. Đây là nền tảng để biết những tín hiệu lịch sử có còn đúng với bối cảnh quyết định hiện tại hay không. Nếu thứ hạng hoặc mẫu theo giờ thay đổi, danh sách ưu tiên phải thay đổi theo.

Sau bước đó, bộ phận điều hành nên chọn một số tổ hợp sân bay–tuyến–khung giờ cuối ngày để xem xét rotation, thời gian quay đầu theo lịch, khả năng thay thế nguồn lực và quy trình phục hồi. ORD và LGA là ứng viên lịch sử đáng kiểm tra, với lý do khác nhau về tổng lượng chậm và xác suất gián đoạn. Tác động kỳ vọng là giảm chậm lan truyền, nhưng chưa có kết quả can thiệp để xác nhận mức giảm.

Song song, cần tách chương trình xử lý hủy chuyến khỏi chương trình giảm chậm của chuyến hoàn tất. Đối với phân khúc có tỷ lệ hủy cao, cần xem quyết định hủy, khả năng khôi phục lịch và phương án hỗ trợ hành trình; đối với chậm cuối ngày, cần xem propagation và khả năng phục hồi. Giảm một chỉ tiêu không được đi kèm việc đẩy vấn đề sang chỉ tiêu còn lại.

Ở bước tiếp theo, nhóm quản lý hiệu suất hãng cần kiểm tra sâu những nhóm tuyến của NK còn chênh lệch sau so sánh tương đồng và những phân khúc hủy của MQ. Phân tích phải giữ cả nhóm chuyến hoàn tất lẫn nhóm không thực hiện được lịch để tránh kết luận thuận lợi hoặc bất lợi chỉ vì thay đổi mẫu số.

Để mở nguyên nhân gốc, ưu tiên nối thêm thời tiết thực tế, thông tin múi giờ/ngày sự kiện, lịch quay vòng tàu bay, tổ bay, bảo dưỡng và hành khách nối chuyến. Chỉ sau khi có dữ liệu này mới nên đánh giá các giả thuyết cụ thể về nguồn lực, kỹ thuật hoặc tổn thất thương mại.

## Đo hiệu quả và truyền đạt qua Power BI

Trước thử nghiệm, cần xây mức nền bằng dữ liệu mới trên đúng các tuyến và khung giờ định can thiệp. Sau đó so kết quả với nhóm đối chiếu tương đồng, theo dõi thay đổi về cơ cấu tuyến, thời tiết, số chuyến và độ phủ dữ liệu. Không tự đặt một mức giảm phần trăm hoặc số tiền tiết kiệm như thể đã được mô hình dự báo xác nhận.

Các chỉ tiêu chính nên là tỷ lệ chậm từ 60 phút, tỷ lệ gián đoạn gồm hủy/đổi hướng/chậm nặng và phân vị 95 của mức chậm. Tỷ lệ hủy, đổi hướng, số chuyến và độ phủ là các chỉ tiêu bảo vệ: kết quả sẽ không thuyết phục nếu mean đẹp hơn nhưng nhiều chuyến bị hủy hơn hoặc nhiều bản ghi bị loại hơn.

Power BI nên giúp người đọc đi theo câu chuyện: quy mô vấn đề; địa điểm có tác động; thời điểm rủi ro; hãng và tuyến cần điều tra; bằng chứng về nguyên nhân; hành động và thước đo thành công. Các trang sân bay/tuyến phải ghi rõ phạm vi 11 tháng; các trang toàn hệ thống phải giữ cả tháng 10. Mỗi tỷ lệ cần đặt cạnh số chuyến và định nghĩa mẫu số.

Phần hành động phải thể hiện trạng thái đề xuất hoặc đang thử nghiệm đúng thực tế. Hiện tại chưa có dữ liệu trước–sau can thiệp, nên chưa thể trình bày thành tích cải thiện hoặc khoản tiết kiệm đã đạt được. Đã dựng và mở lại [bản Power BI Desktop 7 trang](https://github.com/MINNNZZ/flight-delay-operations-analytics/releases/tag/v1.0.0) có dữ liệu nhúng. Kiểm định trực tiếp bằng engine DAX trên chính bản `.pbix` đạt PASS cho 21 chỉ tiêu; xem [bằng chứng đối soát](../powerbi/desktop/desktop_verification.json). Một số visual/slicer trong kế hoạch ban đầu vẫn là đề xuất mở rộng.

## Điều người đọc nên ghi nhớ

Một insight tốt nối được con số với nơi, thời điểm, nhóm chịu ảnh hưởng, lời giải thích có bằng chứng và một quyết định có thể kiểm chứng. Trong bộ dữ liệu này, sự chênh lệch cuối ngày có độ bền qua nhiều phép kiểm tra; ngược lại, cách đánh giá MQ thay đổi rõ khi chuyển từ bảng tổng hợp sang các nhóm chuyến tương đồng. Cả hai kết quả đều có ích vì chúng giúp ưu tiên đúng và tránh quy kết quá sớm.

Giới hạn quan trọng nhất vẫn là thời điểm dữ liệu, phần địa lý thiếu tháng 10 và khoảng trống giữa nhãn nguyên nhân với cơ chế được xác minh. Báo cáo hỗ trợ lựa chọn câu hỏi điều tra tiếp theo; quyết định vận hành hiện tại cần được đặt trên dữ liệu mới và kết quả kiểm chứng tương ứng.

## Cập nhật: khác biệt cuối ngày có bền trước biến động theo ngày không?

Chênh lệch mean arrival thô giữa nhóm khởi hành 17–21 và 06–11 là 9,27 phút; chênh lệch tỷ lệ chậm nặng là 4,88 điểm phần trăm, tương đương tỷ số rủi ro 2,35 lần. Kiểm chứng mới lấy lại mẫu đồng thời sáng và tối theo các khối ngày trong từng tháng, để không coi hàng triệu chuyến là các quan sát độc lập.

Với 3.000 lần lấy lại mẫu theo khối 7 ngày, khoảng phân vị 2,5–97,5% của chênh lệch mean là 8,41–10,13 phút, và của chênh lệch severe là 4,37–5,40 điểm phần trăm. Thử khối 1 và 14 ngày vẫn giữ cùng chiều. Điều này bổ sung bằng chứng rằng chênh lệch cuối ngày không chỉ xuất hiện dưới một cách lấy lại mẫu ngày duy nhất trong năm 2015.

Đối với quản lý, ưu tiên hợp lý vẫn là tìm những nhóm tuyến, hãng và rotation có rủi ro cuối ngày để điều tra trên dữ liệu mới. Các khoảng này chỉ mô tả độ ổn định lịch sử theo giả định của phương pháp; không phải dự báo 2026, không xác định lợi ích của chuyển lịch bay và không áp dụng cho chênh lệch điều chỉnh 10,06 phút. Phương pháp, giới hạn và đề xuất bổ sung Power BI nằm trong [báo cáo rà soát](skill_review/analysis_improvement_review.md). Bản Desktop hiện có chưa bổ sung các khoảng và bảng độ nhạy mới.

## Tài liệu số liệu đi kèm

Các số liệu và kiểm chứng trong bản diễn giải này lấy từ [báo cáo phân tích gốc](aviation_analysis_report.md), [đánh giá chất lượng](data_quality_report.md), [kết quả kiểm định toàn bộ dữ liệu xuất](verification.json), [tổng hợp KPI](analysis_summary.json), các bảng trong thư mục `tables/`, và hai bộ kết quả [so theo hãng–sân bay–tháng](matched_airline_origin_month.json), [so theo tuyến–tháng](matched_route_month.json). Kiểm chứng hãng ban đầu nằm trong [robustness_summary.json](robustness_summary.json), phần rà soát mới trong [statistical_review.json](skill_review/statistical_review.json). Bản cập nhật chạy thêm phép kiểm chứng trên nguồn cũ, không bổ sung dữ liệu quan sát mới.
