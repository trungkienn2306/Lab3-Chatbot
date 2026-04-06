# Du lịch AI — frontend (`apps/web`)

Giao diện chat kiểu ChatGPT: **rail trái** (menu, logo, nút *Đoạn chat mới*), vùng chat rộng (`max-w-4xl`). **Một cửa sổ chat duy nhất** — không danh sách nhiều hội thoại. Stack: React 19 + Vite 8 + TypeScript + Tailwind v4.

## Chế độ hiện tại: API-backed (mock-first ở BE)

- Frontend gọi backend qua:
  - `GET /api/health` (pre-flight DB check)
  - `GET /api/chat/history` (đồng bộ lịch sử theo `session_id`)
  - `POST /api/chat` (gửi tin và nhận phản hồi)
- Base URL đọc từ `VITE_API_BASE_URL` (fallback: `http://localhost:8000`).
- `src/lib/mockReplies.ts` giữ lại để tham chiếu/dự phòng, không còn trong luồng chat mặc định.

## Lưu cục bộ (`localStorage`)

| Key | Mục đích |
|-----|-----------|
| `travel_chat_messages` | Mảng tin nhắn (JSON) — toàn bộ luồng hiện tại |
| `travel_chat_session_id` | UUID phiên; **đổi mới** mỗi lần *Đoạn chat mới* (chuẩn bị đồng bộ API) |

**Đoạn chat mới:** xóa `travel_chat_messages`, sinh `session_id` mới, dọn key cũ (`travel_chat_conversations`, `travel_chat_active_id`, `travel_chat_messages:*` nếu còn sót từ bản trước).

**Migrate:** lần đầu mở sau khi nâng cấp, nếu chưa có `travel_chat_messages` thì đọc tin từ bản đa hội thoại / `travel_chat_messages:<id>` cũ rồi ghi vào key mới.

## Lệnh

```bash
npm run dev:web   # từ root
# hoặc: cd apps/web && npm run dev
```

Build / lint: `npm run build`, `npm run lint`.

## Cấu trúc chính

- `src/hooks/useTravelChat.ts` — một luồng tin + `clearChat` + gọi API backend
- `src/components/chat/` — `ChatRail`, `ChatTopBar`, `MessageList`, `ChatComposer`, …
- `src/lib/chatStorage.ts` — đọc/ghi một key messages + session id
- `src/lib/chatApi.ts` — API client FE cho health/history/chat
