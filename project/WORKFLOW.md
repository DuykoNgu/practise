# Quy trình làm việc với `/implement`

Hướng dẫn ngắn: làm từng screen theo đúng thứ tự, từ lúc chuẩn bị đến lúc xong.

## 0. Chuẩn bị (làm 1 lần)

1. Mở phiên Claude Code trên nhánh `main` (hoặc chạy `git pull origin main` trên máy).
2. Cài thư viện cho script kiểm tra:

   ```bash
   pip install -r project/tools/requirements.txt
   ```

3. Chốt các câu hỏi đang mở trong [risks-and-questions.md](risks-and-questions.md) cho các mục sắp làm (ví dụ Q-14 trước khi làm `PLT-1`).

## 1. Chọn mục cần làm

- Xem [tracker.md](tracker.md): mục ⬜ đầu tiên có các mục phụ thuộc đều ✅ là mục tiếp theo.
- Thứ tự track chính: `PLT-1 → PLT-2 → PLT-3 → PLT-4 → SCR-01 → SCR-90 → SCR-80 → SCR-70 → SCR-60 → SCR-20 → SCR-30 → SCR-31 → API-ITSM → SCR-40 → JOB-DETECT → SCR-10 → SCR-11.1 → SCR-02 → API-LOGS → SCR-11.2 → SCR-11.3 → SCR-50 → NFR-VERIFY`
- Track AI chạy song song: `AI-1 → AI-2 → AI-3 → AI-4`.

## 2. Gõ lệnh

```text
/implement SCR-01
```

Hoặc chỉ gõ `/implement` để agent tự chọn mục tiếp theo.

Nếu ô chat không gợi ý `/implement`, cứ gõ thường: *implement SCR-01* hoặc *làm mục tiếp theo* — agent tự nạp skill `implement` (file `.claude/skills/implement/SKILL.md`).

## 3. Agent tự làm theo thứ tự

| Bước | Agent làm gì | Khi nào dừng lại hỏi bạn |
|---|---|---|
| 1. Kiểm tra đồng bộ | Chạy `check_screens.py` | YAML lệch với docs, OpenAPI, SQL |
| 2. Đọc mục | Mở `project/screens/<ID>.yaml` | Mục phụ thuộc chưa xong |
| 3. Đối chiếu project | Đọc câu hỏi mở, decisions, backlog, definition of done | Câu hỏi mở còn chặn task |
| 4. Đối chiếu docs | Đọc AC, BR, NFR, OpenAPI, SQL, IA, sơ đồ | Docs mâu thuẫn hoặc thiếu |
| 5. Code | Backend → frontend → test, viết tóm tắt trước khi code | Cần sửa ngoài phạm vi mục |
| 6. Kiểm tra | Lint, type check, test, build, `simplify`, `code-review` | — (tự sửa đến khi qua) |
| 7. Ghi lại | Tick task, ghi các skill đã dùng vào `skills_used`, sinh lại tracker (có cột Skills used), commit `<ID>: ...` kèm dòng `Skills:`, push | — |

## 4. Việc của bạn sau mỗi mục

1. Đọc báo cáo cuối: phần nào đã qua, phần nào còn lại.
2. Trả lời nếu agent hỏi (chọn phương án, duyệt chi phí `--live`, …).
3. Gõ `/compact` để làm gọn context.
4. Quay lại bước 2 với mục tiếp theo.
5. Hết một milestone thì bảo agent merge lên `main`.

## 5. Khi thay đổi yêu cầu

1. Sửa docs (OpenAPI, `cic.sql`, IA, business rules…).
2. Sửa các file YAML liên quan trong `project/screens/`.
3. Chạy kiểm tra, phải báo ✓ trước khi `/implement` tiếp:

   ```bash
   python project/tools/check_screens.py --write
   ```
