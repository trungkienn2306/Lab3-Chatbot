# PRD — Chatbot tra cứu thông tin du lịch

**Phiên bản:** 1.2  
**Trạng thái:** Draft  
**Phạm vi:** Một màn hình — layout kiểu ChatGPT (**rail trái** + vùng chat), **một cửa sổ chat duy nhất**; không đăng nhập.

---

## 1. Tóm tắt điều hành

Sản phẩm là **chatbot tra cứu du lịch** trên web. Người dùng chat với bot; hệ thống **lưu lịch sử** (client `localStorage` khi mock; **database** theo `session_id` khi có API) để **F5 vẫn thấy cùng đoạn hội thoại**. Có nút **xóa / đoạn chat mới** để làm trống màn hình và bắt đầu luồng mới (UUID phiên mới).

---

## 2. Vấn đề & cơ hội

- Hỏi nhanh về du lịch không cần tài khoản.
- **Một luồng** đơn giản cho lab; vẫn demo persistence và “bắt đầu lại” rõ ràng.

---

## 3. Mục tiêu sản phẩm

| Mục tiêu | Mô tả |
|----------|--------|
| G1 | Gửi tin và nhận phản hồi bot (chủ đề du lịch). |
| G2 | Lịch sử **một đoạn chat** được lưu; reload vẫn thấy cho tới khi user xóa / đoạn mới. |
| G3 | UI một màn, chủ đề du lịch, responsive. |

---

## 4. Phi chức năng / ngoài phạm vi

- Không đăng ký / đăng nhập / phân quyền.
- Không **danh sách nhiều cuộc** trong sidebar (không lưu nhiều “cửa sổ” song song trên UI).
- Không nhiều màn điều hướng; không OTA thật bắt buộc.

---

## 5. Đối tượng sử dụng

- Khách / người lên kế hoạch; sinh viên lab.

---

## 6. User stories

1. Mở trang và chat ngay.
2. Thấy lịch sử trong **cùng đoạn** để tiếp tục hội thoại.
3. **Đoạn chat mới:** xóa nội dung trên màn hình và bắt đầu trắng (có xác nhận nếu đang có tin).
4. Giao diện dễ đọc, cảm giác du lịch.
5. Lab: có dữ liệu persistence minh họa; có thể **ghi metric DB** (`lab_metric_log`) bổ sung `logs/` — xem [DATABASE-DESIGN-chatbot-du-lich.md](DATABASE-DESIGN-chatbot-du-lich.md).

---

## 7. Yêu cầu chức năng

### 7.1 Chat

- **FR-CHAT-01–04:** như trước (gửi tin, persona du lịch, loading, lỗi thân thiện).

### 7.2 Một phiên / session (không đăng nhập)

- **FR-HIST-01:** Client giữ **`session_id`** (UUID); đổi **`session_id` mới** khi *Đoạn chat mới*.
- **FR-HIST-02:** Server (khi có) lưu tin theo **`session_id`** trong `chat_message` — xem DB design v3.0.
- **FR-HIST-03:** API trả lịch sử theo `session_id` hiện tại (`GET .../history?session_id=&limit=`).
- **FR-HIST-04:** Không yêu cầu API danh sách nhiều conversation cho phạm vi lab này.

### 7.3 Một màn hình

- **FR-UI-01:** Rail trái: menu, branding, **Đoạn chat mới**; không list nhiều hội thoại.
- **FR-UI-02:** Rail đóng/mở mobile; thu gọn desktop.

### 7.4 Observability (Lab 3)

- **FR-OBS-01:** Có thể ghi `lab_metric_log` (tuỳ chọn), bổ sung `logs/*.json`.
- **FR-OBS-02:** Liên kết lỏng qua `session_id` trong bảng metric (không bắt buộc `conversation_id`).

---

## 8. Yêu cầu phi chức năng

- NFR như bản trước; rate limit theo IP / `session_id`.

---

## 9. Tiêu chí chấp nhận — tóm tắt

- Chat được; F5 còn lịch sử cho đến khi *Đoạn chat mới*.
- Không login; DB tối thiểu: `chat_message` + (khuyến nghị) `lab_metric_log`.
- Một màn; rail + chat + composer.

---

## 10. Rủi ro & giả định

- `session_id` đoán được → rủi ro đọc lịch sử nếu không giới hạn — chấp nhận MVP lab.

---

## 11. Phụ thuộc tài liệu

- **Tech Spec:** monorepo, React/Vite/Tailwind + Python + PostgreSQL + SQLAlchemy + Alembic — tổng quan [TECH-SPEC-chatbot-du-lich.md](TECH-SPEC-chatbot-du-lich.md) v1.2; tích hợp API + ReAct [TECH-SPEC-chatbot-du-lich-v2-integrated.md](v2/TECH-SPEC-chatbot-du-lich-v2-integrated.md) v2.0 (thư mục [v2](v2/README.md)).
- **API:** [API-DESIGN-travel-chat-backend.md](v2/API-DESIGN-travel-chat-backend.md).
- **Tool / agent backend:** [BACKEND-TOOLS-REACT-TRAVEL.md](v2/BACKEND-TOOLS-REACT-TRAVEL.md).
- **Database design:** [DATABASE-DESIGN-chatbot-du-lich.md](DATABASE-DESIGN-chatbot-du-lich.md) v3.0 (`chat_message` + `lab_metric_log`); mở rộng tuỳ chọn [DATABASE-DESIGN-chatbot-du-lich-v4.md](v2/DATABASE-DESIGN-chatbot-du-lich-v4.md).
- **Playbook điểm lab:** [LAB3_SCORING_DELIVERY_PLAYBOOK.md](LAB3_SCORING_DELIVERY_PLAYBOOK.md).
