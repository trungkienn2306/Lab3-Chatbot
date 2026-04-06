# Runbook tích hợp FE-BE-DB (Lab 3 chatbot du lịch)

Tài liệu này lưu lại các giải pháp đã áp dụng để nối frontend (`apps/web`) với backend (`apps/api`) và database (SQLite), theo nguyên tắc mock-first.

## 1) Mục tiêu tích hợp

- Frontend không còn trả lời từ mock cục bộ mặc định.
- Mọi lượt chat đi qua API backend để có lịch sử và metric.
- Có pre-flight check trước khi gửi tin để giảm lỗi demo.
- Có bằng chứng dữ liệu trong DB cho phần thuyết trình.

## 2) Kiến trúc luồng dữ liệu sau tích hợp

1. FE tạo/đọc `session_id` từ localStorage.
2. FE gọi `GET /api/health` để kiểm tra backend và DB.
3. FE gọi `GET /api/chat/history?session_id=...` để nạp lịch sử.
4. FE gửi `POST /api/chat` với `mode=simple|agent`.
5. BE xử lý, ghi `chat_message`, ghi metric vào `lab_metric_log`.
6. FE nhận `reply` và hiển thị cùng luồng chat hiện tại.

## 3) Các thay đổi chính đã áp dụng

## 3.1 Frontend

- Tạo API client `apps/web/src/lib/chatApi.ts`:
  - `getHealth()`
  - `getHistory(sessionId)`
  - `postChat({ sessionId, message, mode })`
- Refactor `apps/web/src/hooks/useTravelChat.ts`:
  - Bỏ luồng gọi `getMockReply` trong flow mặc định.
  - Bootstrap lịch sử từ backend theo `session_id`.
  - Khi gửi tin: check `/api/health` trước, sau đó mới gọi `/api/chat`.
  - Nếu backend/DB lỗi thì hiển thị thông báo thân thiện cho user.

## 3.2 Backend

- Mở rộng endpoint sức khỏe `GET /api/health` để trả rõ:
  - `status`
  - `database` (`up`/`down`)
  - `app_env`
- API chat:
  - `GET /api/chat/history`
  - `POST /api/chat` (`mode=simple|agent`)
- Ghi dữ liệu:
  - Bảng `chat_message`
  - Bảng `lab_metric_log`
  - Bảng `tool_invocation` (tùy chọn theo env)

## 3.3 Cấu hình môi trường

- Bổ sung `fastapi`, `uvicorn`, `sqlalchemy` vào `requirements.txt`.
- Tạo file `.env` ở root để chạy local.
- Chuẩn hóa biến cấu hình backend:
  - `DEFAULT_PROVIDER`
  - `DEFAULT_LLM_MODEL`
  - `OPENAI_API_KEY` hoặc `LLM_API_KEY`
  - `DATABASE_URL`

## 4) Sự cố thực tế đã gặp và cách xử lý

## 4.1 Lỗi cài dependency Python

- Triệu chứng: thiếu `fastapi` khi import/chạy API.
- Xử lý: cài đủ package backend; trên Windows có thể cài theo nhóm package cần cho API trước để tránh chờ lâu vì `llama-cpp-python`.

## 4.2 Lỗi đường dẫn SQLite khi chạy trong `apps/api`

- Triệu chứng: DB file không nằm đúng vị trí mong muốn khi chạy `uvicorn` từ `apps/api`.
- Nguyên nhân: default URL dùng đường dẫn tương đối không khớp thư mục làm việc.
- Xử lý: đặt default `DATABASE_URL=sqlite:///./dev.db` để nhất quán theo working directory `apps/api`.

## 4.3 ReAct mock bị lặp tool đến max steps

- Triệu chứng: câu hỏi quy đổi tiền gọi `get_exchange_rate` nhiều lần rồi dừng do `MAX_STEPS`.
- Nguyên nhân: mock LLM vẫn match từ khóa cũ trong toàn prompt sau khi đã có `Observation`.
- Xử lý: cập nhật `MockLLMProvider` để nếu prompt đã có `Observation:` thì trả `Final Answer` thay vì tiếp tục phát `Action`.

## 4.4 Lỗi CORS giữa FE và BE

- Triệu chứng:
  - Browser báo `CORS policy blocked` hoặc `No 'Access-Control-Allow-Origin' header`.
  - API vẫn có thể sống, nhưng FE không gọi được từ trình duyệt.
- Nguyên nhân thường gặp:
  - FE đổi port (5173/5174) nhưng `CORS_ORIGINS` chưa cập nhật.
  - Đã sửa `.env` nhưng chưa restart backend.
  - FE gọi `localhost` nhưng BE chỉ allow `127.0.0.1` (hoặc ngược lại).
- Xử lý chuẩn:
  - Khai báo `CORS_ORIGINS` dạng comma-separated, ví dụ:
    - `http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173`
  - Restart backend sau mọi thay đổi `.env`.
  - Kiểm tra lại `Origin` thực tế FE đang chạy rồi đối chiếu với `CORS_ORIGINS`.

## 5) Cách verify tích hợp (checklist ngắn)

1. Chạy BE trong `apps/api`: `python -m uvicorn app.main:app --reload --port 8000`.
2. Chạy FE trong `apps/web`: `npm run dev`.
3. Kiểm tra FE:
   - Vào trang chat, app không crash.
   - Tin nhắn lỗi thân thiện xuất hiện đúng khi tắt BE/DB.
4. Kiểm tra API:
   - `GET /api/health` trả `database: up`.
   - `POST /api/chat` trả `reply`.
   - `GET /api/chat/history` trả đủ 2 bản ghi (user + assistant) cho session test.
5. Kiểm tra DB:
   - `chat_message` tăng số dòng sau mỗi lượt chat.
   - `lab_metric_log` tăng số dòng sau mỗi turn.
6. Kiểm tra chất lượng FE:
   - `npm run lint`
   - `npm run build`

## 5.1 CORS preflight checklist (bắt buộc khi lỗi FE gọi API)

1. Mở DevTools -> Network, chọn request lỗi.
2. Xem header `Origin` của request.
3. Kiểm tra response preflight `OPTIONS` có:
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Methods`
   - `Access-Control-Allow-Headers`
4. Đảm bảo `Origin` nằm trong `CORS_ORIGINS`.
5. Xác nhận backend đã restart sau khi đổi env.
6. Chạy `GET /api/health` để phân biệt lỗi CORS với lỗi BE/DB không chạy.

## 6) Bằng chứng dùng khi demo với giảng viên

- Health check trả trạng thái DB.
- Một phiên chat mẫu có `session_id`, `correlation_id`, `agent.steps_used`, `tools_called`.
- Truy vấn DB cho thấy:
  - Lịch sử chat có lưu.
  - Metric có lưu.
- Build frontend pass (`lint` + `build`).

## 7) Khuyến nghị cho bước tiếp theo

- Viết script test case tự động cho 5 kịch bản mock-first.
- Viết script export bảng metric từ `lab_metric_log` sang markdown/csv để đưa thẳng vào báo cáo.
- Khi chuyển sang external API, giữ cơ chế fallback để demo ổn định.
