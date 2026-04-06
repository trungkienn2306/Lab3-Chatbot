# Du lịch AI — frontend (`apps/web`)

Giao diện chat kiểu ChatGPT: **rail trái** (menu, logo, nút *Đoạn chat mới*), vùng chat rộng (`max-w-4xl`). **Một cửa sổ chat duy nhất** — không danh sách nhiều hội thoại. Stack: React 19 + Vite 8 + TypeScript + Tailwind v4.

## Chế độ hiện tại: mock (không API)

- Phản hồi bot: [src/lib/mockReplies.ts](src/lib/mockReplies.ts) (~0,6–1,2s trễ).

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

- `src/hooks/useTravelChat.ts` — một luồng tin + `clearChat` + mock gửi tin
- `src/components/chat/` — `ChatRail`, `ChatTopBar`, `MessageList`, `ChatComposer`, …
- `src/lib/chatStorage.ts` — đọc/ghi một key messages + session id
