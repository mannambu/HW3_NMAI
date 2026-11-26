# HW3 - Class Scheduling using Genetic Algorithm

Lời giải cho bài toán xếp thời khóa biểu trong [đề HW3](HW3.pdf), gồm mã Python, dữ liệu sinh có seed, lịch cuối, biểu đồ fitness và nhật ký thực thi. Theo yêu cầu của người dùng, tài liệu được viết bằng Markdown; không tạo báo cáo PDF và không điền thông tin thành viên.

## 1. Kết quả và cách xem nhanh

| Phương án | Lớp đủ 2 buổi | Buổi đã xếp | Buổi còn thiếu | Xung đột trong phần đã xếp | Trạng thái |
|---|---:|---:|---:|---:|---|
| Giữ 20 phòng | 300/480 | 600/960 | 360 | 0 | Đạt tối đa sức chứa, chưa thỏa yêu cầu xếp đủ |
| Tăng lên 32 phòng | 480/480 | 960/960 | 0 | 0 | Thỏa toàn bộ ràng buộc cứng của dữ liệu đã khởi tạo |

- [Lịch 20 phòng](results/rooms20/schedule.html), [CSV](results/rooms20/schedule.csv), [180 lớp chưa xếp](results/rooms20/unscheduled.csv).
- [Lịch 32 phòng](results/rooms32/schedule.html), [CSV](results/rooms32/schedule.csv).
- [Biểu đồ 20 phòng](results/rooms20/fitness.svg), [biểu đồ 32 phòng](results/rooms32/fitness.svg).
- [Nhật ký thực thi và số liệu](EXECUTION_LOG.md).

Mở `schedule.html` trực tiếp trong trình duyệt. Có thể lọc theo phòng, giảng viên hoặc môn học; không cần máy chủ hay kết nối mạng. Thư mục cấp `rooms20`/`rooms32` chứa lịch tốt nhất trong ba lần chạy; từng lần chạy được lưu riêng trong `seed42`, `seed43`, `seed44`.

## 2. Chạy chương trình

Yêu cầu Python 3.10 trở lên. Chương trình, kiểm thử và xuất CSV/JSON/SVG/HTML chỉ dùng thư viện chuẩn Python, không cần `pip install`. Đã thực thi bằng Python 3.11.7 trên Windows.

```powershell
# Chạy hai phương án, mỗi phương án ba seed, 60 cá thể, 400 thế hệ.
python -X utf8 main.py

# Chạy nhanh với thư mục kết quả riêng, tránh ghi đè kết quả đầy đủ.
python -X utf8 main.py --rooms 32 --seeds 42 --population 20 --generations 50 --output quick_results

# Kiểm thử.
python -X utf8 -m unittest discover -s tests -v

# Kiểm tra trực tiếp CSV đã xuất, đối chiếu instance.json.
python -X utf8 verify.py results/rooms32
python -X utf8 verify.py results/rooms20 --allow-partial

# Đóng gói mã nguồn, tài liệu và kết quả hiện tại.
python -X utf8 package.py
```

`verify.py results/rooms20` **không** có `--allow-partial` phải trả mã thoát 1: 360 buổi bắt buộc vẫn chưa được xếp. Cờ này chỉ cho phép chấp nhận lịch một phần khi kiểm tra, không thay đổi số vi phạm hoặc biến nó thành lịch khả thi đầy đủ.

`main.py` ghi đè các tệp sinh trong thư mục `--output` đã chọn. Chạy cùng phiên bản Python, tham số và seed cho cùng lịch, fitness và lịch sử thế hệ; thời gian chạy có thể khác.

## 3. Phân tích đề và các quyết định mô hình hóa

Đề yêu cầu 60 môn, mỗi môn 8 lớp, mỗi lớp 2 buổi/tuần: tổng cộng 480 lớp và 960 buổi. Có 60 giảng viên, 5 ngày, 6 tiết/ngày và 20 phòng. Cần dùng GA, trình bày fitness, lịch cuối và biểu đồ fitness. Đề ghi hạn nộp 23:59:00 ngày 29/11/2026.

### 3.1. Chứng minh dữ liệu gốc không có lịch đầy đủ

Một phòng chỉ chứa một lớp tại mỗi tiết, nên:

```text
sức chứa = 20 phòng × 5 ngày × 6 tiết = 600 buổi
nhu cầu  = 480 lớp × 2 buổi           = 960 buổi
thiếu ít nhất                        = 360 buổi
số lớp đủ hai buổi tối đa             = floor(600 / 2) = 300 lớp
số phòng tối thiểu theo sức chứa      = ceil(960 / 30) = 32 phòng
```

GA không thể khắc phục một mâu thuẫn sức chứa. Lịch 20 phòng được xây dựng với 300 lớp đủ hai buổi và 180 lớp hoàn toàn chưa xếp; không chia lớp thành các buổi lẻ để làm đẹp số liệu. Lịch thực tế đạt đúng cận 600 buổi/300 lớp nên tối ưu về **độ phủ** cho dữ liệu gốc.

32 phòng chỉ là điều kiện cần theo sức chứa, không tự bảo đảm khả thi khi xét cỡ phòng, giảng viên và ngày học. Với dữ liệu được sinh ở đây, lịch 960 buổi đã được xây dựng và kiểm tra, là bằng chứng cụ thể cho tính khả thi. Phương án tăng phòng là một thay đổi dữ liệu được người dùng chấp thuận, không được gộp với trường hợp gốc.

### 3.2. Giả định được sử dụng

| Điểm chưa rõ trong đề | Cách xử lý |
|---|---|
| `num_courses = 60` nhưng `course_name = {1-50}` | Dùng mã môn 1-60, nhất quán với 60 × 8 = 480 lớp. |
| Chưa định nghĩa sáng/chiều | Tiết 1-3 là sáng; 4-6 là chiều. |
| Hai buổi không cùng hoặc liền ngày | Dùng `abs(day1 - day2) >= 2`; chỉ số nội bộ 0-4, CSV 1-5. |
| Chưa có lịch đóng/mở phòng | Tất cả phòng khả dụng trong cả 30 tiết/tuần. |
| Chưa có số sinh viên cụ thể | Dùng đúng ba loại 0/1/2, không tự gán số ghế. |
| Chưa có danh sách lớp của từng giảng viên | GV p phụ trách môn p: 8 lớp ở phương án đầy đủ, không quá 10. Hai buổi một lớp cùng giảng viên. |
| Chưa có sở thích hoặc môn được phép dạy | Danh sách ba môn gồm môn p và hai môn khác lấy ngẫu nhiên; cũng là danh sách được phép dạy. |
| Chưa có dữ liệu sinh viên/nhóm học chung | Không áp thêm ràng buộc trùng lịch sinh viên giữa các lớp. |

Mỗi lớp có mã duy nhất 1-480. `section_in_course` là số thứ tự 1-8 trong môn; không dùng nó làm khóa duy nhất.

### 3.3. Khởi tạo dữ liệu

Data seed mặc định là `2026`:

- 480 cỡ lớp được lấy ngẫu nhiên đều trong `{0,1,2}`; dữ liệu thực tế gồm 143 lớp nhỏ, 165 lớp vừa, 172 lớp lớn.
- 20 phòng gồm 4 nhỏ, 6 vừa, 10 lớn, thứ tự mã phòng được xáo trộn.
- Phương án 32 phòng giữ nguyên 20 phòng ban đầu và thêm 2 nhỏ, 4 vừa, 6 lớn, thứ tự phần thêm được xáo trộn.
- Hai phương án có cùng 480 lớp, phân công giảng viên và sở thích; chỉ khác số phòng và phần lịch có thể xếp.
- `instance.json` lưu dữ liệu cụ thể của từng lần chạy, không chỉ lưu seed.

Đây là bộ dữ liệu tổng hợp phù hợp với việc đề cho phép khởi tạo giá trị còn thiếu. Không có bước tìm lịch cho sở thích bất kỳ của trường học thực tế.

## 4. Biến quyết định và ràng buộc

Một sự kiện có dạng `(section_id, timeslot, room_id)` và nằm trong một ngày. Một nhiễm sắc thể là tuple chứa năm ngày; mỗi ngày là tuple các sự kiện. Tương đương, có thể mô hình hóa biến nhị phân `x[s,d,t,r]` cho biết lớp s có buổi học ở ngày d, tiết t, phòng r.

Các điều kiện cứng được kiểm tra:

1. Cỡ phòng phải lớn hơn hoặc bằng cỡ lớp.
2. Mỗi lớp có đúng hai buổi, cách nhau ít nhất hai ngày. Buổi thiếu luôn được ghi nhận là vi phạm yêu cầu bắt buộc.
3. Tại mỗi `(ngày, tiết)`, một giảng viên dạy tối đa một lớp; số lớp khác nhau của mỗi giảng viên không quá 10.
4. Chỉ dùng mã phòng/ngày/tiết hợp lệ trong tập khả dụng của mô hình.
5. Một lớp không xuất hiện đồng thời ở hai phòng.
6. Một phòng không chứa hai lớp tại cùng tiết.
7. Môn được dạy phải thuộc danh sách môn được phép của giảng viên (bonus 2).

Bonus 1 được thống kê qua số giảng viên có ít nhất một môn yêu thích đã xếp: 60/60 trong cả hai phương án. Do phân công và danh sách được khởi tạo tương thích, hai bonus này thỏa ngay từ đầu; **GA không tìm kiếm lại phân công giảng viên**.

## 5. Fitness

Gọi:

- `U`: tổng số buổi bắt buộc còn thiếu, tính riêng từng lớp bằng `max(0, 2 - số_buổi_đã_xếp)`.
- `H`: số vi phạm vận hành còn lại, như trùng phòng, trùng giảng viên, sai cỡ phòng hoặc sai ngày học. Bộ kiểm tra lưu cả danh sách lỗi.
- `S`: chi phí ràng buộc mềm.

```text
S = 2 × idle_slots
  + 2 × idle_weekdays
  + 1 × extra_teaching_days
  + 5 × mixed_professor_days
  + 3 × course_minority_sessions
  + 1 × room_mismatches

fitness = 1 / (1 + 100000 × (U + H) + S)
```

Fitness càng lớn càng tốt; chi phí càng nhỏ càng tốt. Hệ số 100000 lớn hơn cận bảo thủ 10000 của tổng chi phí mềm trong mô hình hiện tại. Trong quá trình GA, `U` đã cố định ở cận sức chứa và `H=0` được bảo toàn bằng biểu diễn/toán tử. Do đó chọn cá thể có `S` nhỏ nhất tương đương chọn fitness lớn nhất. Không chạy GA trên các lịch tùy ý rồi hy vọng hệ số phạt sẽ sửa hết xung đột.

| Thành phần | Định nghĩa |
|---|---|
| `idle_slots` | Với mỗi GV/ngày có dạy: `tiết_cuối - tiết_đầu + 1 - số_buổi`; cộng trên toàn bộ GV/ngày. |
| `idle_weekdays` | Với mỗi GV: số ngày không dạy nằm giữa ngày dạy đầu tiên và cuối cùng. |
| `extra_teaching_days` | Với mỗi GV có dạy: `số_ngày_dạy - 1`; khuyến khích gom ngày. |
| `mixed_professor_days` | Số cặp GV/ngày có cả tiết sáng và chiều. |
| `course_minority_sessions` | Với mỗi môn: `min(số_buổi_sáng, số_buổi_chiều)`, cộng trên các môn; xét toàn bộ lớp của môn, không chỉ riêng từng lớp. |
| `room_mismatches` | Số buổi dùng phòng lớn hơn cỡ lớp. Phòng nhỏ hơn lớp là lỗi cứng. |

Ví dụ một giảng viên dạy tiết 1 và 6 trong cùng ngày tạo ra 4 tiết trống và một ngày lẫn sáng/chiều. Từng thành phần được lưu trước/sau để không che khuất đánh đổi do tổng trọng số.

`fitness.svg` vẽ chi phí mềm tốt nhất/trung bình quần thể và **fitness có phạt buổi thiếu**. Trục fitness được phóng đại theo khoảng dữ liệu. Với 20 phòng, fitness vẫn chỉ khoảng `2.78e-8` vì 360 buổi chưa xếp. `fitness.csv` lưu thêm `conditional_fitness = 1/(1+S)` để tham khảo trong cùng mức độ phủ; giá trị này không chứng minh tính khả thi đầy đủ.

## 6. Thuật toán

Đây là GA có bước dựng lịch khả thi ban đầu. Bước dựng lịch giải quyết độ phủ và ràng buộc cứng; GA tìm kiếm lịch tốt hơn theo các ràng buộc mềm.

### 6.1. Chọn lớp và cặp ngày

Ở phương án 20 phòng, chọn ngẫu nhiên 5/8 lớp của mỗi môn. Mỗi giảng viên có các cặp ngày: Hai-Tư, Hai-Sáu, Tư-Sáu, Ba-Năm, Ba-Năm. Vì vậy mỗi người có đúng 2 buổi mỗi ngày; toàn trường có `60 × 2 = 120` buổi/ngày, đúng `20 × 6`.

Ở phương án 32 phòng, mỗi giảng viên nhận cả 8 lớp. Dùng tam giác các cặp Hai-Tư, Hai-Sáu, Tư-Sáu cùng cặp Ba-Năm:

- 48 giảng viên có ba lớp Ba-Năm và năm lớp thuộc tam giác, với số lần các cạnh là hoán vị của `(2,2,1)`.
- 12 giảng viên có bốn lớp Ba-Năm và bốn lớp thuộc tam giác, với số lần các cạnh là hoán vị của `(2,1,1)`.
- Luân phiên cạnh ít/nhiều theo nhóm để tổng mỗi ngày đều là 192 buổi, đúng `32 × 6`.

Seed của lần chạy điều khiển cả việc chọn lớp, gán cặp ngày và ngẫu nhiên của GA. Các lần chạy có thể khác tập 300 lớp được chọn trong phương án 20 phòng. So sánh trước/sau trong **cùng lần chạy** luôn giữ nguyên tập lớp và cặp ngày. Không coi ba seed là ba bộ dữ liệu độc lập lấy mẫu từ thực tế.

### 6.2. Dựng lịch bằng tô cạnh đồ thị hai phía

Với mỗi ngày:

1. Xét lớp từ lớn đến nhỏ. Gán mỗi buổi vào phòng phù hợp chật nhất còn chỗ trong hạn mức 6 buổi/ngày, cân bằng tải các phòng cùng cỡ.
2. Lập đa đồ thị hai phía: đỉnh trái là giảng viên, đỉnh phải là phòng; mỗi buổi là một cạnh. Bậc đỉnh không quá 6.
3. Thêm đỉnh/cạnh giả để được đa đồ thị hai phía 6-chính quy, mỗi phía có 60 đỉnh.
4. Tìm một ghép cặp hoàn hảo, gán các cạnh thật trong đó vào tiết 1 rồi bỏ toàn bộ cạnh ghép. Lặp cho tiết 2-6; bỏ qua cạnh giả khi xuất lịch.

Vì mỗi ghép cặp dùng mỗi giảng viên và phòng nhiều nhất một lần, lịch không thể trùng giảng viên/phòng ở một tiết. Tính tồn tại ghép cặp có thể thấy trực tiếp: trong đồ thị k-chính quy, tập S bên trái có `k|S|` cạnh đến các hàng xóm N(S), trong khi các hàng xóm nhận nhiều nhất `k|N(S)|` cạnh. Suy ra `|S| <= |N(S)|`; điều kiện Hall thỏa. Sau khi bỏ một ghép cặp, đồ thị còn `(k-1)`-chính quy.

Bước gán cỡ phòng được kiểm tra riêng và có thể báo lỗi nếu dữ liệu/ngày đã chọn không đủ phòng phù hợp. Không tuyên bố cách dựng này giải được mọi dữ liệu chỉ vì tổng sức chứa đủ.

### 6.3. Quần thể, chọn lọc, lai và đột biến

| Tham số của lần chạy đầy đủ | Giá trị |
|---|---:|
| Kích thước quần thể | 60 |
| Số thế hệ | 400, cộng thế hệ 0 khởi tạo |
| Elitism | Giữ 4 cá thể tốt nhất |
| Tournament | Chọn tốt nhất trong 3 cá thể ngẫu nhiên |
| Xác suất lai | 0.9 |
| Xác suất đột biến | 0.9 |
| Số phép đột biến khi được chọn | Ngẫu nhiên 1-3 |
| Các seed thực nghiệm | 42, 43, 44 |

Các cá thể ban đầu được dựng ngẫu nhiên độc lập trên cùng tập lớp/cặp ngày. Phép lai chọn nguyên khối mỗi ngày từ bố hoặc mẹ. Vì mọi cá thể có cùng lớp học vào từng ngày, lai theo ngày giữ đủ hai buổi, giữ cặp ngày và không làm phát sinh xung đột nội ngày.

Mỗi lần đột biến chọn một ngày, sau đó dùng một trong ba phép:

- **70%: đổi màu một thành phần Kempe.** Chọn hai tiết, lấy đồ thị con gồm các cạnh của hai tiết đó, chọn một thành phần liên thông và đổi hai tiết cho toàn bộ cạnh trong thành phần. Tại mỗi đỉnh vẫn có nhiều nhất một cạnh của mỗi màu, nên không trùng phòng/GV.
- **15%: đổi hai tiết toàn cục trong ngày.** Bảo toàn mọi quan hệ đồng thời.
- **15%: đổi phòng giữa hai buổi cùng tiết.** Chỉ chấp nhận khi cả hai phòng đều đủ cỡ cho lớp mới; số thử bị chặn ở 12.

Đột biến có thể không thay đổi cá thể nếu không tìm được đổi phòng hợp lệ. Không dùng xác suất chấp nhận dựa trên việc cải thiện tức thì; cá thể con xấu hơn vẫn có thể xuất hiện, chọn lọc và elitism diễn ra ở cấp quần thể.

Mã giả:

```text
phân tích sức chứa; chọn tập lớp và cặp ngày
tạo N lịch khả thi bằng dựng đồ thị ngẫu nhiên
ghi nhận thế hệ 0
lặp G thế hệ:
    giữ E cá thể tốt nhất
    cho đến khi quần thể con đủ N:
        chọn bố mẹ bằng tournament
        lai theo ngày với xác suất pc
        đột biến bảo toàn tính khả thi với xác suất pm
        tính chi phí mềm của con
    thay quần thể; ghi fitness thật của thế hệ
kiểm tra độc lập lịch tốt nhất; xuất lịch, biểu đồ, dữ liệu
```

Chi phí đánh giá một cá thể tuyến tính theo số buổi và số cặp GV/ngày. Phần GA chủ yếu có độ phức tạp `O(G × N × số_buổi)`, cộng chi phí sắp hạng quần thể và thao tác trên đồ thị con. Dựng lịch dùng ghép cặp tăng cường sáu lần cho mỗi ngày trên đồ thị 60 × 60.

### 6.4. Phạm vi tìm kiếm và giới hạn

GA tối ưu tiết học và phòng trong miền có **phân công giảng viên, tập lớp được xếp và cặp ngày của mỗi lớp cố định trong một lần chạy**. Vì vậy:

- Hai thành phần `idle_weekdays` và `extra_teaching_days` bất biến trong thực nghiệm này: lần lượt 0 và 240. Chúng được công khai trong fitness/thống kê, không được nhận là cải thiện nhờ GA.
- Chưa tối ưu số ngày đi dạy của giảng viên, phân công lại giảng viên hoặc hoán đổi lớp được chọn trong phương án 20 phòng.
- Sở thích của cả 60 GV được thỏa do cách khởi tạo có chủ đích; không phải kết quả của một bài toán phân công sở thích tổng quát.
- Không chứng minh tối ưu toàn cục cho chi phí mềm. Elitism chỉ bảo đảm chi phí tốt nhất không tăng giữa các thế hệ.
- Tối ưu tổng trọng số có thể làm một thành phần riêng tăng; thực nghiệm có số buổi sai cỡ chính xác tăng nhẹ, trong khi tổng chi phí giảm mạnh.
- Với 32 phòng, tất cả phòng đều dùng đủ 30 tiết. Không có dư địa dự phòng cho phòng đóng cửa hoặc thêm lớp.

Độ phủ 600 buổi ở 20 phòng được chứng minh tối ưu; chất lượng mềm chỉ là kết quả heuristic đo được. Đây là hai kết luận khác nhau.

## 7. Tổ chức mã nguồn và đầu ra

```text
main.py                 CLI chạy các phương án và seed
verify.py               Đọc CSV/instance.json, kiểm tra độc lập lịch xuất
package.py              Tạo HW3_solution.zip từ danh sách tệp cho phép
hw3/model.py            Kiểu dữ liệu, sinh dữ liệu có seed
hw3/construct.py        Cặp ngày, gán phòng, tô cạnh bằng ghép cặp
hw3/evaluate.py         Các thành phần mềm, fitness, kiểm tra cứng
hw3/ga.py               GA, chọn lọc, lai, đột biến
hw3/export.py           Xuất JSON, CSV, SVG, HTML ngoại tuyến
tests/test_hw3.py       16 kiểm thử
results/comparison.json Tổng hợp thực nghiệm
results/rooms20/        Lịch tốt nhất của phương án gốc
results/rooms32/        Lịch tốt nhất của phương án điều chỉnh
```

Mỗi thư mục kết quả có `instance.json`, `schedule.json`, `schedule.csv`, `initial_schedule.csv`, `unscheduled.csv`, `summary.json`, `fitness.csv`, `fitness.svg`, `schedule.html`. Cấp phương án còn có `experiments.json` và `all_fitness.csv`; các thư mục `seed*` giữ toàn bộ kết quả từng lần chạy.

`initial_schedule.csv` là **cá thể tốt nhất của quần thể ở thế hệ 0**, không phải một lịch khởi tạo tùy chọn. `fitness.csv` có đủ 401 hàng dữ liệu. Thời gian trong `summary.json` chỉ đo bước dựng lịch và GA, không gồm xuất tệp/kiểm thử.

`.tools/` và `tmp/` chỉ là công cụ/tệp tạm dùng khi đọc đề và kiểm tra hiển thị; chương trình không phụ thuộc vào chúng và gói ZIP loại bỏ chúng. Đề gốc yêu cầu báo cáo PDF và thông tin nhóm khi nộp LMS; phiên bản này chủ ý chỉ có Markdown theo chỉ dẫn mới của người dùng và chưa được nộp lên LMS.
