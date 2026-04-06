# Plan 01 — Mock-first implementation (ổn định demo trước)

**Mục tiêu:** Triển khai chatbot du lịch backend + agent ReAct theo nguyên tắc **mock trước** để đảm bảo demo ổn định, đo được metric, có trace chứng minh.

**Nguyên tắc cứng:**

1. Không phụ thuộc internet để pass demo core.
2. Dữ liệu tool ở giai đoạn này dùng mock dataset nội bộ.
3. Chỉ được sang Plan 02 khi qua toàn bộ cổng chất lượng của Plan 01.

**Tài liệu căn cứ:**

- [docs/v2/LAB3_BACKEND_AI_MASTER_SPEC.md](../v2/LAB3_BACKEND_AI_MASTER_SPEC.md)
- [docs/v2/TECH-SPEC-chatbot-du-lich-v2-integrated.md](../v2/TECH-SPEC-chatbot-du-lich-v2-integrated.md)
- [docs/v2/API-DESIGN-travel-chat-backend.md](../v2/API-DESIGN-travel-chat-backend.md)
- [docs/v2/BACKEND-TOOLS-REACT-TRAVEL.md](../v2/BACKEND-TOOLS-REACT-TRAVEL.md)
- [docs/v2/DATABASE-DESIGN-chatbot-du-lich-v4.md](../v2/DATABASE-DESIGN-chatbot-du-lich-v4.md)

---

## 1. Tracking board cho AI agent

Trạng thái dùng 4 mức: `todo` -> `in_progress` -> `blocked` -> `done`.

| ID | Task | Owner | Status | Evidence |
|----|------|-------|--------|----------|
| P1-T01 | Khởi tạo cấu trúc `apps/api/app` (routers/services/tools/models/schemas) | AI | todo | Cây thư mục + commit diff |
| P1-T02 | Implement API `GET /api/health` | AI | todo | Response mẫu + test |
| P1-T03 | Implement API `GET /api/chat/history` | AI | todo | Query theo `session_id` |
| P1-T04 | Implement API `POST /api/chat` nhánh `mode=simple` | AI | todo | Chat một vòng LLM |
| P1-T05 | Implement registry + 5 tools mock | AI | todo | Tool list và schema |
| P1-T06 | Implement `mode=agent` (ReAct loop + parse action) | AI | todo | Trace có steps/tool calls |
| P1-T07 | Implement metric logging (`lab_metric_log`) | AI | todo | SQL kiểm tra event |
| P1-T08 | (Optional) Implement `tool_invocation` | AI | todo | SQL tool analytics |
| P1-T09 | Chuẩn hóa error handling (`JSON_PARSE`, `UNKNOWN_TOOL`, ...) | AI | todo | Error response sample |
| P1-T10 | Viết test cases + chạy 5 case domain du lịch | AI | todo | Bảng pass/fail |
| P1-T11 | Trích 1 trace RCA hoàn chỉnh | AI | todo | File trace + phân tích |
| P1-T12 | Tổng hợp bảng metric v1 | AI | todo | Bảng markdown report-ready |

---

## 2. Sprint breakdown (thực thi)

### Sprint A — Nền tảng API và persistence

- [ ] Tạo `main.py`, router `health.py`, `chat.py`.
- [ ] Tạo model `chat_message`, `lab_metric_log` (và migration).
- [ ] Kết nối DB qua SQLAlchemy + Alembic.
- [ ] Chạy local: health pass + insert/select message pass.

**Done when:** API chạy local ổn định, có thể lưu và đọc lịch sử theo `session_id`.

### Sprint B — Baseline chatbot (`mode=simple`)

- [ ] `POST /api/chat` nhận request đúng schema.
- [ ] Lưu `user` message.
- [ ] Nạp history + gọi LLM một lần.
- [ ] Lưu `assistant` message + trả response.
- [ ] Ghi metric tối thiểu: `llm_call`, `turn_complete`.

**Done when:** 5/5 test cơ bản chạy qua ở `mode=simple` với dữ liệu hợp lệ.

### Sprint C — ReAct agent (`mode=agent`) với mock tools

- [ ] Tạo tool registry và schema validate.
- [ ] Tool mock bắt buộc:
  - `get_exchange_rate`
  - `estimate_stay_budget`
  - `sum_expenses`
  - `validate_flight_request`
  - `search_destination_tips`
- [ ] Implement ReAct loop (`max_steps`, parse action, execute tool, observation).
- [ ] Implement `escalate_to_human` (bonus, mock).
- [ ] Ghi metric lỗi parse/tool timeout/unknown tool.

**Done when:** Agent gọi được tool, trả Final Answer, không crash khi lỗi input.

### Sprint D — Quality gate và report artifacts

- [ ] Chạy 5 test case theo domain du lịch.
- [ ] Xuất bảng metric:
  - success
  - steps
  - total latency
  - prompt/completion tokens
  - error_code
- [ ] Trích 1 trace thành công + 1 trace lỗi.
- [ ] Viết RCA trace lỗi (root cause -> fix -> kết quả sau fix).

**Done when:** Có đủ artifact để thuyết trình mà không phụ thuộc API ngoài.

---

## 3. Danh sách test cases bắt buộc (mock phase)

1. **Simple Q&A**: gợi ý lịch trình/tips du lịch.
2. **Single tool**: quy đổi tiền tệ.
3. **Multi-tool**: ước lượng ngân sách + cộng chi phí.
4. **Bad params**: ngày bay không hợp lệ.
5. **Out-of-scope**: yêu cầu nhạy cảm/ngoài phạm vi.

---

## 4. Dữ liệu cần lưu để chứng minh

### 4.1 Bắt buộc

- `chat_message`: lịch sử chat.
- `lab_metric_log`:
  - `llm_call`
  - `tool_call` (hoặc `react_step`)
  - `parse_error`
  - `turn_complete`
  - `escalation` (nếu có)

### 4.2 Tùy chọn nhưng khuyến nghị

- `tool_invocation`: phân tích tool theo SQL nhanh hơn.

---

## 5. Cổng chất lượng để sang Plan 02

Chỉ được bắt đầu Plan 02 khi **tất cả** điều kiện sau đạt:

- [ ] API contract ổn định (không đổi schema lớn).
- [ ] 5 test case pass trong `mode=mock`.
- [ ] Có bảng metric đầy đủ cho baseline và agent.
- [ ] Có ít nhất 1 trace RCA chất lượng.
- [ ] Demo local pass khi tắt internet.

---

## 6. Rủi ro và cách xử lý

- **Rủi ro parse JSON từ LLM**
  - Mitigation: strip markdown fence + retry parse ngắn + error code rõ.
- **Rủi ro loop vô hạn**
  - Mitigation: `max_steps` + `AGENT_MAX_STEPS`.
- **Rủi ro output sai nghiệp vụ**
  - Mitigation: tool schema chặt + validate args trước execute.

---

## 7. Kết quả bàn giao của Plan 01

- Backend chạy ổn định với mock tools.
- Có metric, log, trace chứng minh.
- Có bảng số liệu report-ready.
- Đủ điều kiện vào Plan 02 (external integration).
