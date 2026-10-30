# 01. Phạm vi (Scope) V1

> Trạng thái thiết kế: TARGET V1 · Trạng thái triển khai: CHƯA TRIỂN KHAI (giai đoạn tài liệu)

Tên sản phẩm: **Change-Incident Correlation (CIC)** — Hệ thống truy vết sự cố do thay đổi.

## 1. Bài toán

Khi số ticket tăng bất thường, hệ thống tự trả lời câu hỏi **"thay đổi nào gần đây có khả năng là nguyên nhân?"** và xếp hạng các "nghi phạm".

Ví dụ thực tế: 22h thứ Ba, IT cập nhật bản vá Windows cho phòng Kế toán. Sáng thứ Tư có 14 ticket "không in được". Hiện nay chỉ người giàu kinh nghiệm mới nối được hai sự việc này; người trực service desk thường xử lý từng ticket riêng lẻ, mất nhiều giờ mới nhận ra đây là một sự cố chung.

## 2. Mục tiêu V1

- Ghi nhận **Change record** (bản vá, đổi cấu hình, nâng cấp phần mềm) cùng phạm vi ảnh hưởng và kế hoạch rollback.
- Tiếp nhận **Ticket** (thủ công, import CSV/Excel, hoặc API từ hệ thống ITSM).
- Xây dựng **Baseline**: số ticket trung bình theo khung giờ / thứ / danh mục.
- **Phát hiện bất thường** khi số ticket của một nhóm (danh mục, phòng ban, chi nhánh, phần mềm) vượt baseline.
- **Xếp hạng nghi phạm**: với mỗi bất thường, liệt kê các change gần đây theo điểm khả nghi (0–100) kèm lý do giải thích được.
- Hỗ trợ quyết định: hiển thị ticket liên quan, kế hoạch rollback, người thực hiện change.
- Thu thập **phản hồi** (nghi phạm đúng/sai) để cải thiện độ chính xác.
- Phân quyền theo vai trò và ghi nhật ký hoạt động.

## 3. Dữ liệu đầu vào

### 3.1 Change record

| Trường | Mô tả |
|---|---|
| Loại thay đổi | Bản vá (patch) · Đổi cấu hình (config) · Nâng cấp phần mềm (upgrade) |
| Thời điểm | Bắt đầu / kết thúc thực hiện (có múi giờ) |
| Phạm vi ảnh hưởng | Nhóm máy · Phòng ban · Phần mềm · Chi nhánh (một hoặc nhiều) |
| Người thực hiện | Tài khoản IT thực hiện và người phê duyệt |
| Kế hoạch rollback | Có / không, mô tả các bước, thời gian ước tính, mức rủi ro |
| Trạng thái | Đã lên lịch · Đang thực hiện · Hoàn tất · Đã rollback · Thất bại |

### 3.2 Ticket

| Trường | Mô tả |
|---|---|
| Thời điểm tạo | Thời điểm người dùng báo sự cố |
| Danh mục | Ví dụ: In ấn, Mạng, Email, Phần mềm kế toán, Đăng nhập |
| Người báo | Phòng ban, chi nhánh của người báo |
| Thiết bị / phần mềm liên quan | Nhóm máy, tên phần mềm, phiên bản |
| Mô tả | Văn bản tự do (dùng cho khớp từ khóa với change) |
| Trạng thái | Mới · Đang xử lý · Đã giải quyết · Đóng |

### 3.3 Baseline

Số ticket trung bình (và độ lệch chuẩn) theo **khung giờ × thứ trong tuần × danh mục**, tính từ lịch sử ticket (mặc định 8 tuần gần nhất, loại bỏ các giai đoạn đã được đánh dấu là sự cố).

## 4. Ngoài phạm vi (Non-goals)

V1 **không** bao gồm:

- Tự động thực thi rollback hoặc thay đổi trên hạ tầng thật.
- Thay thế hệ thống ITSM/CMDB; CIC chỉ đọc và đối chiếu dữ liệu.
- Phân tích nguyên nhân gốc rễ (root cause) ở mức log/hệ thống.
- Dự đoán sự cố trước khi change được thực hiện.
- Chatbot hoặc xử lý ngôn ngữ tự nhiên nâng cao (chỉ khớp từ khóa/danh mục cơ bản).
- SSO bên ngoài và xác thực đa yếu tố.

## 5. Kiến trúc mục tiêu (mức ý tưởng)

```text
Giao diện web (SPA)
    → REST / HTTPS / JSON
Backend API (nhiều tầng)
    → Cơ sở dữ liệu quan hệ (change, ticket, baseline, kết quả tương quan)
    → Bộ xử lý nền (tính baseline, phát hiện bất thường, xếp hạng)
    → Lưu trữ tệp (file import)
```

Chi tiết kiến trúc (C4, ERD, API) thuộc các giai đoạn sau và nằm ngoài tài liệu này.
