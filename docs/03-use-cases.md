# 03. Tác nhân, vai trò và Use case

> Trạng thái thiết kế: TARGET V1

## 1. Tác nhân

| Tác nhân | Mô tả |
|---|---|
| **Quản trị viên (Admin)** | Quản lý người dùng, cấu hình hệ thống, có toàn quyền. |
| **Quản lý IT (IT Manager)** | Theo dõi sự cố, xem nghi phạm, ra quyết định rollback, xem nhật ký. |
| **Kỹ sư thay đổi (Change Engineer)** | Người thực hiện change; tạo/cập nhật change record và kế hoạch rollback. |
| **Nhân viên service desk (Agent)** | Tiếp nhận ticket, theo dõi anomaly, xem nghi phạm để định tuyến ticket. |
| **Hệ thống ITSM (tác nhân hệ thống)** | Đẩy ticket/change qua API. |
| **Bộ xử lý nền (tác nhân hệ thống)** | Chạy tính baseline, phát hiện bất thường, xếp hạng. |

## 2. Danh sách Use case

| ID | Use case | Tác nhân chính |
|---|---|---|
| UC01 | Đăng nhập | Tất cả người dùng |
| UC02 | Đăng xuất | Tất cả người dùng |
| UC03 | Xem dashboard sự cố | Tất cả người dùng |
| UC04 | Xem danh sách / chi tiết change | Tất cả người dùng |
| UC05 | Tạo change record | Change Engineer, IT Manager, Admin |
| UC06 | Sửa change record / đổi trạng thái | Change Engineer (change của mình), IT Manager, Admin |
| UC07 | Xem danh sách / chi tiết ticket | Tất cả người dùng |
| UC08 | Tạo ticket thủ công | Agent, IT Manager, Admin |
| UC09 | Import ticket từ CSV/Excel | Agent, IT Manager, Admin |
| UC10 | Nhận ticket/change qua API | ITSM (hệ thống) |
| UC11 | Xem baseline | Agent, IT Manager, Admin |
| UC12 | Tính lại baseline | IT Manager, Admin |
| UC13 | Phát hiện bất thường | Bộ xử lý nền |
| UC14 | Xem chi tiết anomaly và nghi phạm xếp hạng | Tất cả người dùng |
| UC15 | Phản hồi nghi phạm (đúng / không liên quan) | Agent, IT Manager, Change Engineer, Admin |
| UC16 | Xem nhật ký hoạt động | IT Manager, Admin |
| UC17 | Cấu hình ngưỡng, cửa sổ truy vết, trọng số | Admin |
| UC18 | Quản lý người dùng | Admin |
| UC19 | Quản lý hồ sơ cá nhân / đổi mật khẩu | Tất cả người dùng |

## 3. Use case chính: UC14 Xem chi tiết anomaly và nghi phạm

| Mục | Nội dung |
|---|---|
| Tiền điều kiện | Đã đăng nhập; tồn tại anomaly đã được phát hiện. |
| Luồng chính | 1. Người dùng mở dashboard và chọn một anomaly. 2. Hệ thống hiển thị nhóm bị ảnh hưởng, khoảng thời gian, số ticket thực tế so với baseline. 3. Hệ thống hiển thị danh sách change nghi phạm theo điểm giảm dần, mỗi mục có giải thích yếu tố. 4. Người dùng mở một nghi phạm để xem ticket liên quan, người thực hiện, kế hoạch rollback. |
| Luồng thay thế | Không có change nào trong cửa sổ truy vết → hiển thị "Không tìm thấy nghi phạm" và gợi ý mở rộng cửa sổ. |
| Hậu điều kiện | Không thay đổi dữ liệu; hành động xem được ghi nhật ký nếu bật cấu hình. |

## 4. Vai trò và quyền hạn

| Chức năng | Admin | IT Manager | Change Engineer | Agent |
|---|---|---|---|---|
| Xem dashboard, anomaly, nghi phạm | Có | Có | Có | Có |
| Xem change và ticket | Có | Có | Có | Có |
| Tạo change | Có | Có | Có | Không |
| Sửa change | Có | Có | Chỉ change của mình | Không |
| Tạo / import ticket | Có | Có | Không | Có |
| Xem / tính lại baseline | Có | Có | Chỉ xem | Chỉ xem |
| Phản hồi nghi phạm | Có | Có | Có | Có |
| Nhật ký hoạt động | Có | Có | Không | Không |
| Cấu hình hệ thống | Có | Không | Không | Không |
| Quản lý người dùng | Có | Không | Không | Không |

Backend phải thực thi RBAC và chính sách "chỉ change của mình"; việc ẩn nút ở giao diện chỉ phục vụ UI/UX.

## 5. User story V1 (đánh giá theo INVEST)

| ID | Là một... | Tôi muốn... | Để... | UC |
|---|---|---|---|---|
| US01 | Người dùng | đăng nhập bằng email và mật khẩu | truy cập đúng phần việc của mình | UC01 |
| US02 | Người dùng | đăng xuất | kết thúc phiên an toàn | UC02 |
| US03 | Agent | xem dashboard anomaly đang mở | biết ngay có đợt tăng ticket bất thường | UC03 |
| US04 | Change Engineer | tạo change record kèm phạm vi và kế hoạch rollback | thay đổi của tôi có thể được truy vết | UC05 |
| US05 | Change Engineer | sửa change và đổi trạng thái (kể cả đã rollback) | dữ liệu phản ánh đúng thực tế | UC06 |
| US06 | Người dùng | lọc và xem chi tiết change | tra cứu thay đổi gần đây | UC04 |
| US07 | Agent | thêm ticket thủ công | ghi nhận báo cáo của người dùng | UC08 |
| US08 | Agent | import ticket từ CSV/Excel có xem trước | nạp dữ liệu hàng loạt mà không sai sót | UC09 |
| US09 | Người dùng | lọc và xem chi tiết ticket | xem các ticket cùng nhóm | UC07 |
| US10 | IT Manager | xem baseline so với thực tế | hiểu mức ticket bình thường | UC11 |
| US11 | IT Manager | tính lại baseline | cập nhật theo dữ liệu mới | UC12 |
| US12 | Agent | xem anomaly và danh sách change nghi phạm đã xếp hạng, có giải thích | nhanh chóng nối ticket với thay đổi | UC14 |
| US13 | IT Manager | xem kế hoạch rollback và người thực hiện của nghi phạm | quyết định rollback kịp thời | UC14 |
| US14 | Agent | xác nhận nghi phạm đúng hoặc không liên quan | cải thiện độ chính xác của hệ thống | UC15 |
| US15 | IT Manager | xem nhật ký hoạt động | kiểm tra ai đã làm gì | UC16 |
| US16 | Admin | cấu hình ngưỡng, cửa sổ truy vết, trọng số | điều chỉnh theo thực tế tổ chức | UC17 |
| US17 | Admin | quản lý người dùng và vai trò | kiểm soát quyền truy cập | UC18 |
| US18 | Người dùng | cập nhật hồ sơ và đổi mật khẩu | giữ tài khoản an toàn | UC19 |
| US19 | ITSM | gửi ticket/change qua API | dữ liệu tự động đồng bộ | UC10 |

Tiêu chí INVEST áp dụng: **I**ndependent (độc lập), **N**egotiable (có thể thương lượng), **V**aluable (có giá trị), **E**stimable (ước lượng được), **S**mall (đủ nhỏ), **T**estable (kiểm thử được). Tiêu chí chấp nhận chi tiết sẽ được bổ sung ở giai đoạn sau.
