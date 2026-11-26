# Nhật ký thực thi HW3

Ngày thực hiện: **25/11/2026**, múi giờ Asia/Bangkok.

## Phạm vi đã chốt

Đã đọc đủ hai trang `HW3.pdf`, đối chiếu nội dung văn bản và ảnh trang. Phát hiện thiếu 360 vị trí phòng-tiết ở dữ liệu gốc và mâu thuẫn 60 môn với dải mã 1-50. Người dùng chọn đối chiếu 20/32 phòng và yêu cầu chỉ ghi tài liệu Markdown, bỏ báo cáo PDF.

Đã triển khai GA, bước khởi tạo khả thi, dữ liệu tổng hợp, bộ kiểm tra cứng độc lập, CSV/JSON, trình xem lịch HTML ngoại tuyến và biểu đồ SVG. Không tạo báo cáo PDF, không điền thông tin nhóm, không nộp LMS.

## Lệnh thực nghiệm

```powershell
python -X utf8 main.py
```

Python **3.11.7**, Windows 64-bit. Data seed `2026`; population `60`; generations `400`; elite `4`; tournament `3`; crossover `0.9`; mutation `0.9`; run seeds `42,43,44`.

Mỗi run ghi thế hệ 0 và 400 thế hệ tiếp theo. Dữ liệu dưới đây được đọc từ kết quả chạy thực tế, không được dựng giả.

| Phòng | Seed | Chi phí đầu S0 | Chi phí cuối S | Giảm so với S0 | Thời gian dựng + GA (giây) |
|---|---:|---:|---:|---:|---:|
| 20 | 42 | 2508 | 1029 | 58.97% | 6.7057 |
| 20 | 43 | 2498 | 1060 | 57.57% | 7.6640 |
| 20 | 44 | 2494 | 1052 | 57.82% | 7.5387 |
| 32 | 42 | 3666 | 2138 | 41.68% | 9.0848 |
| 32 | 43 | 3619 | 2053 | 43.27% | 10.1663 |
| 32 | 44 | 3698 | 2026 | 45.21% | 10.0499 |

Tổng thời gian dựng + GA của sáu run: **51.2094 giây** trên môi trường thực thi này; không bao gồm xuất tệp, đọc đề, kiểm thử hoặc kiểm tra hiển thị.

| Thống kê | 20 phòng | 32 phòng |
|---|---:|---:|
| Seed tốt nhất | 42 | 44 |
| Chi phí cuối trung bình | 1047.00 | 2072.33 |
| Độ lệch chuẩn mẫu, 3 run | 16.09 | 58.45 |
| Lớp đủ hai buổi | 300 | 480 |
| Buổi đã xếp | 600 | 960 |
| Buổi thiếu U | 360 | 0 |
| Vi phạm vận hành H | 0 | 0 |
| Tổng vi phạm cứng U+H | 360 | 0 |
| Giảng viên có môn yêu thích đã xếp | 60/60 | 60/60 |
| Số lớp tối đa một giảng viên đang dạy | 5 | 8 |
| Fitness tốt nhất | 2.7776983047429477e-8 | 0.000493339911198816 |

Không so sánh trực tiếp chi phí mềm 1029 với 2026 để kết luận 20 phòng tốt hơn: hai phương án phục vụ số buổi khác nhau. Lịch 20 phòng vẫn thiếu 180 lớp, trong khi lịch 32 phòng là lịch đầy đủ.

## Chi tiết cải thiện của lịch được chọn

| Thành phần | 20 phòng: trước | 20 phòng: sau | 32 phòng: trước | 32 phòng: sau |
|---|---:|---:|---:|---:|
| Tiết trống giữa các buổi của GV | 362 | 86 | 397 | 150 |
| Ngày trống giữa các ngày dạy | 0 | 0 | 0 | 0 |
| Ngày dạy vượt quá một ngày/GV | 240 | 240 | 240 | 240 |
| Cặp GV/ngày lẫn sáng và chiều | 164 | 40 | 262 | 126 |
| Buổi thuộc nửa ngày ít hơn của từng môn | 216 | 112 | 406 | 238 |
| Buổi dùng phòng lớn hơn cỡ lớp | 76 | 81 | 136 | 142 |
| **Tổng chi phí có trọng số** | **2508** | **1029** | **3698** | **2026** |

Hai thành phần theo ngày trong tuần bất biến vì cặp ngày được cố định trong từng run. Số phòng không khớp chính xác tăng nhẹ do đánh đổi với các mục tiêu trọng số lớn hơn; không có trường hợp phòng nhỏ hơn lớp. Chưa có chứng minh tối ưu toàn cục cho chi phí mềm.

## Kiểm thử và kiểm tra độc lập

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 verify.py results/rooms32
python -X utf8 verify.py results/rooms20 --allow-partial
```

**16/16 kiểm thử đạt**, bao gồm:

- Độ phủ 600/960, cỡ phòng, khoảng cách ngày, số buổi, giới hạn tải và sở thích.
- Cố ý tạo trùng phòng, giảng viên, lớp; thêm/thiếu buổi; sai phòng/tiết/ngày; dạy môn ngoài danh sách; vượt 10 lớp.
- 300 bước lai/đột biến có kiểm tra đầy đủ (150 cho mỗi phương án).
- Tái lập theo seed, tính không tăng của chi phí tốt nhất do elitism, cải thiện thực sự qua thế hệ.
- Tính tay thành phần mềm và so thứ tự fitness.
- Ghi CSV rồi đọc lại kiểm tra; phát hiện thông tin giảng viên CSV bị sửa sai.
- Từ chối cấu hình không hợp lệ và xác nhận hai phương án dùng cùng dữ liệu lớp/GV/phòng gốc.

Đã kiểm tra các CSV xuất của cả sáu run và hai lịch đại diện; đối chiếu chi phí cuối, số buổi và fitness của lịch với lịch sử thế hệ. Kiểm tra 20 phòng không có `--allow-partial` trả lỗi như mong đợi. Các kiểm tra không dựa vào nhãn “fully_feasible” có sẵn trong JSON.

Đã mở lịch HTML và biểu đồ SVG bằng trình duyệt headless, xem ảnh kết quả để kiểm tra tiếng Việt, bảng ngày/tiết, số liệu và nhãn biểu đồ. Trục fitness của 20 phòng dùng ký hiệu khoa học, có khoảng lề để không cắt nhãn.

## Tệp bàn giao

- Mã nguồn và hướng dẫn: [README.md](README.md), [main.py](main.py), thư mục [hw3](hw3), [verify.py](verify.py), [tests](tests).
- Lịch đại diện: [20 phòng](results/rooms20/schedule.html), [32 phòng](results/rooms32/schedule.html).
- Đồ thị: [20 phòng](results/rooms20/fitness.svg), [32 phòng](results/rooms32/fitness.svg).
- Số liệu đầy đủ: [comparison.json](results/comparison.json), các thư mục `results/rooms*/seed*`.
- Gói mã nguồn + Markdown + kết quả: `HW3_solution.zip`, tạo bởi `package.py`; không chứa `.tools`, `tmp`, cache hoặc báo cáo PDF mới.

Giữ nguyên đề gốc `HW3.pdf`. Chưa thực hiện thao tác nộp bài lên hệ thống bên ngoài.
