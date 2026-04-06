# API Design — Backend chat du lịch (REST)

**Phiên bản tài liệu:** 1.0  
**Căn cứ:** [PRD-chatbot-du-lich.md](../PRD-chatbot-du-lich.md), [LAB3_SCORING_DELIVERY_PLAYBOOK.md](../LAB3_SCORING_DELIVERY_PLAYBOOK.md), [TECH-SPEC-chatbot-du-lich.md](../TECH-SPEC-chatbot-du-lich.md) (bản 1.2 giữ làm nền tổng quan).

**Phạm vi:** Mô tả hợp đồng HTTP giữa `apps/web` và service Python trong `apps/api`. Không thay thế mã nguồn; khi triển khai, đồng bộ với OpenAPI (FastAPI tự sinh).

---

## 1. Nguyên tắc chung

- **Base URL:** ví dụ `https://api.example.com` hoặc dev `http://127.0.0.1:8000`.
- **Tiền tố:** mọi endpoint dưới đây giả định tiền tố `/api` (có thể thêm `/v1` sau nếu cần versioning rõ).
- **Định dạng:** `Content-Type: application/json; charset=utf-8`.
- **Xác thực:** không có (khớp PRD). Rate limit theo IP và/hoặc `session_id` (Tech Spec).
- **Idempotency (lập lại an toàn):** client nên gửi `client_message_id` (UUID) cho mỗi tin user để server có thể trả lại cùng kết quả nếu client retry (tuỳ triển khai).

### 1.1 Header tuỳ chọn

| Header | Mô tả |
|--------|--------|
| `X-Request-ID` | UUID do client hoặc proxy gửi; server trả lại trong lỗi và log. |
| `X-Correlation-ID` | Gom một lượt xử lý (một lần bấm Gửi); nếu client không gửi, server sinh `correlation_id` trong body phản hồi. |

### 1.2 Mã lỗi HTTP và body chuẩn

Mọi lỗi 4xx/5xx (trừ khi reverse proxy cắt ngang) nên dùng body:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "session_id is required",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

| `code` gợi ý | HTTP | Ý nghĩa |
|--------------|------|---------|
| `VALIDATION_ERROR` | 400 | Tham số hoặc JSON body không hợp lệ. |
| `SESSION_INVALID` | 400 | `session_id` không phải UUID hợp lệ. |
| `RATE_LIMITED` | 429 | Vượt giới hạn. |
| `LLM_UNAVAILABLE` | 502 / 503 | Nhà cung cấp LLM lỗi hoặc timeout. |
| `AGENT_MAX_STEPS` | 200* | Agent dừng do vượt `max_steps`; vẫn có thể trả `reply` giải thích (tuỳ policy). |

\*Có thể dùng 200 với `reply` + cờ `truncated: true` để UI không coi là lỗi mạng.

---

## 2. Endpoints

### 2.1 `GET /api/health`

**Mục đích:** Kiểm tra process sống; có thể mở rộng kiểm tra DB (ping).

**Response 200:**

```json
{
  "status": "ok",
  "database": "up"
}
```

`database` có thể là `"skipped"` nếu chưa cấu hình `DATABASE_URL`.

---

### 2.2 `GET /api/chat/history`

**Mục đích:** Khớp PRD FR-HIST-03 — lấy lịch sử tin theo `session_id` hiện tại.

**Query:**

| Tham số | Bắt buộc | Mô tả |
|---------|----------|--------|
| `session_id` | Có | UUID chuỗi chuẩn. |
| `limit` | Không | Mặc định 100, tối đa 500. |
| `before` | Không | UUID của `chat_message.id` — lấy tin cũ hơn tin đó (phân trang). |

**Response 200:**

```json
{
  "session_id": "…",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "…",
      "created_at": "2026-04-06T12:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "…",
      "created_at": "2026-04-06T12:00:01Z"
    }
  ]
}
```

**Lỗi:** `400` nếu thiếu/sai `session_id`.

---

### 2.3 `POST /api/chat`

**Mục đích:** Một endpoint thống nhất cho luồng **chat đơn** (chỉ LLM) hoặc **ReAct agent** (LLM + tool), khớp playbook (baseline vs agent) và bonus observability.

**Request body:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Quy đổi 100 USD sang VND hôm nay",
  "client_message_id": "optional-uuid",
  "mode": "simple",
  "options": {
    "max_steps": 8,
    "temperature": 0.2
  }
}
```

| Trường | Bắt buộc | Mô tả |
|--------|----------|--------|
| `session_id` | Có | UUID phiên (đồng bộ `travel_chat_session_id` trên FE). |
| `message` | Có | Nội dung tin user; độ dài tối đa khuyến nghị 8000 ký tự (cấu hình server). |
| `client_message_id` | Không | Chống gửi trùng. |
| `mode` | Không | `"simple"` (mặc định) = một vòng LLM sau khi nạp history; `"agent"` = ReAct với tool (xem [BACKEND-TOOLS-REACT-TRAVEL.md](BACKEND-TOOLS-REACT-TRAVEL.md)). |
| `options` | Không | `max_steps` giới hạn vòng ReAct; `temperature` gửi xuống provider. |

**Luồng server (tóm tắt):**

1. Validate body; sinh hoặc nhận `correlation_id`.
2. `INSERT` `chat_message` role `user`.
3. Đọc N tin gần nhất cùng `session_id` làm context.
4. Nếu `mode=simple`: một lần gọi LLM → `INSERT` assistant.
5. Nếu `mode=agent`: gọi **ReAct orchestrator** (nhiều bước tool + LLM) → `INSERT` một tin assistant chứa **Final Answer** (toàn bộ trace chi tiết vào `lab_metric_log` / metadata, xem DB v4).
6. Ghi `lab_metric_log` cho `llm_call`, `turn_complete`, lỗi parse nếu có (tuỳ chọn nhưng khuyến nghị cho Lab 3).

**Response 200 (JSON đồng bộ):**

```json
{
  "reply": "Theo tỷ giá mock hôm nay, 100 USD ≈ 2.500.000 VND (tham khảo).",
  "correlation_id": "…",
  "session_id": "…",
  "assistant_message_id": "uuid",
  "usage": {
    "prompt_tokens": 1200,
    "completion_tokens": 180,
    "total_ms": 3400
  },
  "agent": {
    "mode": "agent",
    "steps_used": 3,
    "tools_called": ["get_exchange_rate"]
  }
}
```

| Trường | Mô tả |
|--------|--------|
| `reply` | Nội dung hiển thị cho user (markdown cho phép nếu FE render). |
| `agent` | Chỉ có khi `mode=agent`; có thể ẩn trong production bằng cờ cấu hình. |

**Response streaming (tuỳ chọn, sau này):** `POST` với header `Accept: text/event-stream` — SSE chunk chỉ nên dùng cho token của **câu trả lời cuối**, không bắt buộc cho lab.

---

## 3. Hợp đồng liên quan DB và metric

- Mọi dòng `chat_message` gắn `session_id` theo [DATABASE-DESIGN-chatbot-du-lich-v4.md](DATABASE-DESIGN-chatbot-du-lich-v4.md).
- `correlation_id` trong response trùng với trường cùng tên trong `lab_metric_log` (nếu ghi DB) để join báo cáo với [EVALUATION.md](../../EVALUATION.md).

---

## 4. CORS và môi trường dev

- CORS được cấu hình qua biến môi trường `CORS_ORIGINS` (comma-separated), không hardcode 1 origin cố định cho mọi môi trường.
- Dev localhost khuyến nghị khai báo tối thiểu:
  - `http://localhost:5173`
  - `http://localhost:5174` (khi Vite tự tăng port)
  - `http://127.0.0.1:5173` (nếu FE truy cập theo IP loopback)
- Khi thay đổi `CORS_ORIGINS`, bắt buộc restart backend để áp dụng cấu hình mới.
- Khi debug CORS, kiểm tra theo thứ tự:
  1. Header `Origin` ở request từ browser.
  2. Preflight `OPTIONS` có `Access-Control-Allow-Origin` hợp lệ.
  3. Phân biệt lỗi CORS với lỗi API down bằng `GET /api/health`.
- Không trả lỗi chi tiết nội bộ (stack trace) ra client production.

---

## 5. Liên kết tài liệu

- Logic tool và vòng ReAct: [BACKEND-TOOLS-REACT-TRAVEL.md](BACKEND-TOOLS-REACT-TRAVEL.md)
- Kiến trúc triển khai: [TECH-SPEC-chatbot-du-lich-v2-integrated.md](TECH-SPEC-chatbot-du-lich-v2-integrated.md)
- Schema DB mở rộng (metadata, bảng tuỳ chọn): [DATABASE-DESIGN-chatbot-du-lich-v4.md](DATABASE-DESIGN-chatbot-du-lich-v4.md)
