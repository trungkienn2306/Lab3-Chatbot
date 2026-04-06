# Database Design — Một luồng chat + log metrics (Lab 3)

**Phiên bản:** 3.0  
**RDBMS:** PostgreSQL  
**Schema:** `public` (theo `DATABASE_URL` có `?schema=public`)

**Căn chỉnh FE:** [apps/web](../apps/web) chỉ có **một cửa sổ chat**; client giữ `travel_chat_session_id` (đổi khi *Đoạn chat mới*) và một mảng tin. Backend tối thiểu: bảng **`chat_message`** gắn **`session_id`** (UUID do client), **không** bảng `conversation` / không đa hội thoại trong phạm vi lab nhỏ.

**Lab 3 — báo cáo metric:** bảng **`lab_metric_log`** (tuỳ chọn) để truy vấn SQL bổ sung cho `logs/*.json` ([EVALUATION.md](../EVALUATION.md)). `conversation_id` **không dùng** trong mô hình đơn giản — để `NULL` hoặc bỏ cột nếu schema tối giản hơn nữa.

---

## 1. Mục tiêu

- Không user/login.
- **Một luồng** trên client mỗi lần “chat mới” = `session_id` mới; lịch sử server theo `session_id`.
- `lab_metric_log` phục vụ so sánh Chatbot vs Agent, trace, bonus trong [SCORING.md](../SCORING.md).

---

## 2. Sơ đồ quan hệ (ER)

```mermaid
erDiagram
  chat_message {
    uuid id PK
    uuid session_id
    string role
    text content
    timestamptz created_at
  }

  lab_metric_log {
    uuid id PK
    timestamptz created_at
    uuid session_id_null
    uuid correlation_id_null
    string component
    string event_type
    int duration_ms_null
    int prompt_tokens_null
    int completion_tokens_null
    int step_index_null
    string error_code_null
    jsonb metadata_null
  }
```

Không FK bắt buộc giữa hai bảng; có thể liên kết lỏng qua `session_id` / `correlation_id` trong ứng dụng.

---

## 3. Bảng `chat_message`

| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|--------|
| `id` | `UUID` | `PRIMARY KEY`, default `gen_random_uuid()` | |
| `session_id` | `UUID` | `NOT NULL` | Trùng `travel_chat_session_id` từ client. |
| `role` | `VARCHAR(20)` | `NOT NULL` | `user` \| `assistant` \| `system`. |
| `content` | `TEXT` | `NOT NULL` | |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL`, default `now()` | |

**Index:** `idx_chat_message_session_created ON chat_message (session_id, created_at ASC)`.

**CHECK:** `role IN ('user', 'assistant', 'system')`.

Khi user bấm *Đoạn chat mới* trên FE, client gửi **`session_id` mới**; server chỉ insert tin cho phiên đó (tin phiên cũ vẫn trong DB nếu không xóa — chấp nhận cho lab hoặc thêm job dọn dẹp sau).

---

## 4. Bảng `lab_metric_log`

| Cột | Kiểu | Mô tả |
|-----|------|--------|
| `id` | `UUID` PK | |
| `created_at` | `TIMESTAMPTZ` | |
| `session_id` | `UUID` NULL | Gắn tới phiên chat du lịch (nếu có). |
| `correlation_id` | `UUID` NULL | Gom nhiều dòng một lượt xử lý. |
| `component` | `VARCHAR(40)` NOT NULL | `travel_chat`, `react_agent`, `chatbot_baseline`, … |
| `event_type` | `VARCHAR(40)` NOT NULL | `llm_call`, `react_step`, `turn_complete`, `parse_error`, … |
| `duration_ms` | `INTEGER` NULL | |
| `prompt_tokens` / `completion_tokens` | `INTEGER` NULL | |
| `step_index` | `INTEGER` NULL | Bước ReAct. |
| `error_code` | `VARCHAR(64)` NULL | `JSON_PARSE`, `UNKNOWN_TOOL`, `MAX_STEPS`, … |
| `metadata` | `JSONB` NULL | |

**Index:** `(created_at DESC)`, `(component, event_type)`.

> Nếu muốn schema tối thiểu hơn: có thể bỏ `session_id` trong bảng này và chỉ dùng `correlation_id` + `metadata`.

---

## 5. SQLAlchemy & Alembic

Model trong `apps/api`: `ChatMessage`, `LabMetricLog` (tên class tuỳ repo). Không cần model `Conversation` cho phiên bản lab đơn giản.

---

## 6. Truy vấn tiêu biểu

```sql
-- Lịch sử một phiên (sau khi client gửi session_id hiện tại)
SELECT id, role, content, created_at
FROM chat_message
WHERE session_id = $1
ORDER BY created_at ASC
LIMIT 200;
```

```sql
-- Ví dụ metric: latency trung bình theo component (7 ngày)
SELECT component, AVG(duration_ms)::int, COUNT(*)
FROM lab_metric_log
WHERE created_at > now() - interval '7 days'
  AND event_type = 'llm_call'
  AND duration_ms IS NOT NULL
GROUP BY component;
```

---

## 7. Kết nối local

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres?schema=public"
```

---

## 8. Lịch phiên bản tài liệu

- **1.0:** Một bảng `chat_message` + `session_id`.
- **2.0:** Đa hội thoại + `conversation` + `lab_metric_log` (đã rút gọn cho lab nhỏ).
- **3.0:** Một luồng chat (khớp FE hiện tại) + `lab_metric_log` tùy chọn.
