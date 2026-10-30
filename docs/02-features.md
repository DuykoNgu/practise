# 02. Danh mục tính năng (Feature Catalog)

> Trạng thái thiết kế: TARGET V1

| ID | Tên | V1 | Ưu tiên |
|---|---|---|---|
| F01 | Xác thực và phân quyền | Có | Must |
| F02 | Quản lý Change record | Có | Must |
| F03 | Quản lý / tiếp nhận Ticket | Có | Must |
| F04 | Baseline | Có | Must |
| F05 | Phát hiện bất thường | Có | Must |
| F06 | Tương quan và xếp hạng nghi phạm | Có | Must |
| F07 | Dashboard và chi tiết sự cố | Có | Must |
| F08 | Phản hồi chất lượng nghi phạm | Có | Should |
| F09 | Cấu hình hệ thống | Có | Should |
| F10 | Nhật ký hoạt động | Có | Should |
| F11 | Người dùng và hồ sơ cá nhân | Có | Must |

## F01 Xác thực và phân quyền

- F01.1 Đăng nhập (email, mật khẩu)
- F01.2 Đăng xuất
- F01.3 Phân quyền theo vai trò (RBAC) do backend thực thi
- F01.4 Chặn truy cập trang không đủ quyền (màn hình 403)

## F02 Quản lý Change record

Danh sách có lọc (loại, thời gian, phạm vi, trạng thái), thêm/sửa/xem chi tiết, đổi trạng thái (kể cả đánh dấu đã rollback), đính kèm kế hoạch rollback. Change có thể nhập thủ công, import file hoặc đồng bộ qua API.

Trường chính: loại, tiêu đề, mô tả, thời điểm bắt đầu/kết thúc, phạm vi (nhóm máy, phòng ban, phần mềm, chi nhánh), người thực hiện, người duyệt, kế hoạch rollback, trạng thái.

## F03 Quản lý / tiếp nhận Ticket

Danh sách có lọc (thời gian, danh mục, phòng ban, chi nhánh, phần mềm), xem chi tiết. Nguồn ticket: nhập tay, import CSV/Excel (xem trước và kiểm tra hợp lệ), API từ ITSM.

## F04 Baseline

Tính và lưu số ticket trung bình theo khung giờ/thứ/danh mục; xem biểu đồ baseline so với thực tế; tính lại theo lịch hoặc theo yêu cầu; loại giai đoạn sự cố khỏi dữ liệu nền.

## F05 Phát hiện bất thường

Định kỳ so sánh số ticket thực tế với baseline theo từng nhóm (danh mục, phòng ban, chi nhánh, phần mềm). Khi vượt ngưỡng, tạo **Cụm bất thường (Anomaly)** gồm nhóm bị ảnh hưởng, khoảng thời gian, số ticket thực tế/kỳ vọng, mức nghiêm trọng.

## F06 Tương quan và xếp hạng nghi phạm

Với mỗi anomaly, tìm các change nằm trong cửa sổ thời gian trước thời điểm bắt đầu tăng và tính điểm khả nghi dựa trên:

| Yếu tố | Ý nghĩa |
|---|---|
| Gần về thời gian | Change càng sát thời điểm ticket tăng càng khả nghi |
| Khớp phạm vi | Phòng ban / chi nhánh / phần mềm / nhóm máy của ticket trùng phạm vi change |
| Khớp danh mục & từ khóa | Danh mục hoặc từ khóa ticket liên quan loại/đối tượng change |
| Mức bất thường | Ticket tăng bao nhiêu lần so với baseline |
| Rủi ro change | Loại change, có/không kế hoạch rollback |

Kết quả: danh sách nghi phạm xếp theo điểm, kèm **giải thích từng yếu tố** để người dùng kiểm chứng. Công thức chi tiết được định nghĩa ở giai đoạn thiết kế thuật toán.

## F07 Dashboard và chi tiết sự cố

Tổng quan: anomaly đang mở, biểu đồ ticket so với baseline, top nghi phạm. Chi tiết anomaly: nghi phạm xếp hạng, ticket liên quan, dòng thời gian (change + ticket), kế hoạch rollback và người thực hiện.

## F08 Phản hồi

Người dùng xác nhận một nghi phạm là **đúng nguyên nhân / không liên quan**, ghi chú kết luận; dữ liệu dùng để đo độ chính xác và hiệu chỉnh trọng số.

## F09 Cấu hình hệ thống

Ngưỡng bất thường, cửa sổ truy vết (mặc định 48 giờ), trọng số các yếu tố, chu kỳ chạy, danh mục và ánh xạ phòng ban/chi nhánh/phần mềm.

## F10 Nhật ký hoạt động

Ghi lại: đăng nhập, tạo/sửa change, import ticket, thay đổi cấu hình, phản hồi nghi phạm. Cột: người dùng, hành động, đối tượng, chi tiết, thời gian.

## F11 Người dùng và hồ sơ cá nhân

Quản trị viên tạo/sửa/vô hiệu hóa người dùng và gán vai trò. Người dùng cập nhật hồ sơ và đổi mật khẩu.
