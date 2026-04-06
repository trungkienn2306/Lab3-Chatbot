# Thiết kế logic Tool backend và ReAct (du lịch)

**Phiên bản tài liệu:** 1.0  
**Căn cứ:** [LAB3_SCORING_DELIVERY_PLAYBOOK.md](../LAB3_SCORING_DELIVERY_PLAYBOOK.md) (test case du lịch, bonus fallback/escalation), [API-DESIGN-travel-chat-backend.md](API-DESIGN-travel-chat-backend.md).

**Mục tiêu:** Mô tả chiết lý triển khai **Tool Registry** (đăng ký công cụ), **validation** (kiểm tra tham số), **orchestrator ReAct** trên server để `POST /api/chat` với `mode=agent` đáp ứng rubric lab (ít nhất 2 tool, xử lý lỗi, trace).

---

## 1. Khái niệm và ranh giới

- **Tool:** Hàm Python thuần (hoặc async) có tên ổn định, mô tả cho LLM, và schema tham số (JSON Schema hoặc Pydantic model).
- **ReAct orchestrator:** Tầng dịch vụ gọi LLM lặp: sinh Thought/Action → parse → chạy tool → đưa Observation vào ngữ cảnh → lặp đến Final Answer hoặc `max_steps`.
- **Khác `src/agent/agent.py` (lab):** Mã skeleton ở root `src/` dùng cho bài tập; **backend production** nên đặt orchestrator trong `apps/api/app/services/` và có thể **tái sử dụng** ý tưởng hoặc import sau khi refactor. Tài liệu này mô tả **hợp đồng hành vi**, không ràng buộc tên file cuối cùng.

---

## 2. Tool Registry (đăng ký công cụ)

### 2.1 Cấu trúc một tool trong code

Mỗi tool khai báo:

| Thuộc tính | Mô tả |
|------------|--------|
| `name` | Chuỗi snake_case, duy nhất (ví dụ `get_exchange_rate`). |
| `description` | Văn bản cho LLM: khi nào gọi, đầu vào mong đợi, giới hạn (mock / không phải giá thật). |
| `parameters_schema` | JSON Schema object hoặc Pydantic `model_json_schema()` cho object tham số. |
| `handler` | `Callable[[dict], ToolResult]` — luôn nhận dict đã validate. |
| `timeout_seconds` | Mặc định 5–15s; tool gọi HTTP ngoài cần giới hạn. |

**Kiểu trả về chuẩn hóa (`ToolResult`):**

```text
ok: bool
data: str | dict          # Chuỗi đưa vào Observation (observation text) cho LLM
error_code: str | None    # Ví dụ BAD_PARAMS, EXTERNAL_TIMEOUT
message: str | None       # Chi tiết ngắn cho log, không nhất thiết hiển thị user
```

### 2.2 Đăng ký tập trung

- Một module `app/tools/registry.py` (gợi ý) chứa `TOOLS: list[ToolSpec]` và `get_tool(name) -> ToolSpec | None`.
- Agent **chỉ** được gọi tool có trong registry — tránh thực thi hàm tùy ý (an toàn).

---

## 3. Bộ tool gợi ý theo domain du lịch (khớp playbook)

Các tool dưới đây bám [LAB3_SCORING_DELIVERY_PLAYBOOK.md](../LAB3_SCORING_DELIVERY_PLAYBOOK.md) mục 5.1; dữ liệu **mock** trừ khi tích hợp API thật.

### 3.1 `get_exchange_rate`

- **Mục đích:** Test **single tool** — quy đổi tiền (mock).
- **Tham số (gợi ý):** `from_currency` (string, ISO 4217), `to_currency` (string), `amount` (number, dương).
- **Logic:** Validate mã tiền hợp lệ; tra bảng mock cố định (USD→VND = 25000); trả chuỗi có disclaimer *tham khảo / mock*.
- **Lỗi:** `BAD_PARAMS` nếu tiền không hỗ trợ hoặc `amount` âm.

### 3.2 `estimate_stay_budget`

- **Mục đích:** Một bước trong **multi-tool** (ước lượng lưu trú + ăn).
- **Tham số:** `city` (string), `nights` (int 1–30), `comfort` (`budget` | `standard` | `comfort`).
- **Logic:** Bảng giá mock theo `city` + `comfort`; trả tổng và breakdown ngắn (text).

### 3.3 `sum_expenses`

- **Mục đích:** Bước thứ hai trong multi-tool — cộng các khoản (số học đơn giản, tránh hallucination LLM).
- **Tham số:** `items` (array of `{ "label": string, "amount_vnd": number }`).
- **Logic:** Cộng `amount_vnd`; trả tổng và danh sách đã làm tròn.

### 3.4 `validate_flight_request`

- **Mục đích:** Test **bad params** — ngày không tồn tại, route sai format.
- **Tham số:** `origin_iata` (3 ký tự), `dest_iata` (3 ký tự), `departure_date` (YYYY-MM-DD).
- **Logic:** Parse date; nếu không hợp lệ trả `ok=false`, `error_code=INVALID_DATE` và message tiếng Việt thân thiện. Không “đặt vé” thật.

### 3.5 `search_destination_tips`

- **Mục đích:** **Simple Q&A** hoặc bổ sung ngữ cảnh; mock RAG (bonus extra tools).
- **Tham số:** `query` (string), `city` (string, optional).
- **Logic:** Trả 3–5 gạch đầu dòng cố định theo từ khóa / city (không gọi web trừ khi cấu hình).

### 3.6 `escalate_to_human`

- **Mục đích:** Bonus **Human escalation** (deliverables); out-of-scope hoặc yêu cầu nhạy cảm.
- **Tham số:** `reason` (string), `user_summary` (string).
- **Logic:** Không gọi con người thật trong lab; ghi log / `lab_metric_log` với `event_type=escalation`; trả Observation dạng “Đã ghi nhận chuyển tiếp hỗ trợ viên (mock), mã REF-…”.

---

## 4. Parse Action từ LLM (robust)

### 4.1 Định dạng ép buộc trong system prompt

- Yêu cầu LLM: một khối duy nhất `Action: tool_name({"key": "value"})` hoặc JSON thuần sau `Action:` — **thống nhất một kiểu** trong toàn dự án.
- Khuyến nghị: **JSON thuần** cho tham số tool để dễ `json.loads` sau khi loại bỏ fence mã markdown (khối code ba dấu backtick).

### 4.2 Pipeline xử lý

1. Lấy text completion từ LLM.
2. Strip code fence nếu có.
3. Regex hoặc marker tìm `Thought:` / `Action:` / `Final Answer:`.
4. Nếu có `Final Answer:` → kết thúc vòng lặp, trả nội dung sau nhãn đó làm `reply` cho user.
5. Nếu có `Action:` → parse `tool_name` + `arguments`; nếu parse lỗi → **Observation** giả lập: `Parse error, please fix JSON` và ghi metric `parse_error` (EVALUATION: JSON Parser Error).
6. Nếu `tool_name` không có trong registry → Observation: unknown tool + metric `UNKNOWN_TOOL`.

### 4.3 Retry (bonus failure handling)

- Tối đa `N` (ví dụ 2) lần retry chỉ cho bước parse JSON với cùng completion (hoặc yêu cầu LLM sửa format) — tránh vòng lặp vô hạn; tổng bước vẫn chịu `max_steps`.

---

## 5. ReAct orchestrator (luồng chi tiết)

**Đầu vào:** `session_id`, `user_message`, `history_messages` (từ DB), `correlation_id`, `max_steps`, `llm_client`.

**Thuật toán (pseudo):**

1. `steps = 0`
2. Xây `messages` cho LLM: system (persona du lịch + danh sách tool + format ReAct), sau đó xen kẽ user/assistant từ history (cắt theo token budget), cuối cùng là tin user mới.
3. Vòng lặp:
   - Ghi `lab_metric_log` `llm_call` bắt đầu (timestamp).
   - Gọi LLM → nhận `completion`.
   - Ghi kết thúc `llm_call` (duration_ms, tokens nếu có).
   - Nếu có Final Answer → lưu assistant message, return.
   - Nếu có Action → `execute_tool`:
     - Validate args với Pydantic/schema.
     - Chạy `handler` trong `timeout`.
     - Ghi `lab_metric_log` với `event_type=tool_call` hoặc tương đương trong `metadata` (xem DB v4).
   - Append vào ngữ cảnh: `Observation: ...` (chuỗi từ `ToolResult`).
   - `steps += 1`; nếu `steps >= max_steps` → tin assistant cuối: giải thích dừng sớm (policy SCORING / UX).
4. Mọi exception chưa bắt → bọc: trả `reply` lỗi thân thiện, không crash process, `error_code` trong log.

---

## 6. Chế độ `simple` vs `agent`

| `mode` | Hành vi |
|--------|---------|
| `simple` | Một completion LLM với system prompt persona; không gọi tool; phù hợp baseline so sánh. |
| `agent` | Chạy orchestrator mục 5; ghi đủ metric để GROUP_REPORT §3. |

---

## 7. Liên kết observability

- Mỗi bước LLM và tool nên có thể query qua SQL nếu ghi [DATABASE-DESIGN-chatbot-du-lich-v4.md](DATABASE-DESIGN-chatbot-du-lich-v4.md).
- File `logs/*.json` ở root repo (lab CLI) **song song** với DB; không thay thế trace chi tiết khi debug local.

---

## 8. Kiểm thử gợi ý (mapping playbook)

| Case playbook | Tool / mode |
|---------------|-------------|
| Simple Q&A | `mode=simple` hoặc agent không bắt buộc gọi tool |
| Single tool | `get_exchange_rate` |
| Multi-tool | `estimate_stay_budget` + `sum_expenses` |
| Bad params | `validate_flight_request` với ngày sai |
| Out-of-scope | `escalate_to_human` hoặc từ chối trong Final Answer |
