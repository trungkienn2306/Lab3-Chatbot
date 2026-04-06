# API (Python) — `apps/api`

Thư mục dành cho **FastAPI + SQLAlchemy + Alembic**.

**Tài liệu thiết kế (ưu tiên khi triển khai):**

- [docs/v2/README.md](../../docs/v2/README.md) — mục lục tài liệu v2
- [docs/v2/API-DESIGN-travel-chat-backend.md](../../docs/v2/API-DESIGN-travel-chat-backend.md) — REST, lỗi, `POST /api/chat` (`mode=simple` | `agent`)
- [docs/v2/BACKEND-TOOLS-REACT-TRAVEL.md](../../docs/v2/BACKEND-TOOLS-REACT-TRAVEL.md) — Tool Registry, ReAct orchestrator, bộ tool du lịch gợi ý
- [docs/v2/TECH-SPEC-chatbot-du-lich-v2-integrated.md](../../docs/v2/TECH-SPEC-chatbot-du-lich-v2-integrated.md) — kiến trúc tích hợp v2 (bản tổng quan cũ: [docs/TECH-SPEC-chatbot-du-lich.md](../../docs/TECH-SPEC-chatbot-du-lich.md))
- [docs/v2/DATABASE-DESIGN-chatbot-du-lich-v4.md](../../docs/v2/DATABASE-DESIGN-chatbot-du-lich-v4.md) — schema mở rộng tuỳ chọn (baseline v3: [docs/DATABASE-DESIGN-chatbot-du-lich.md](../../docs/DATABASE-DESIGN-chatbot-du-lich.md))

**Hiện trạng:** mã lab ReAct/chatbot gốc vẫn nằm ở `src/` ở root repo. Khi tích hợp, có thể di chuyển hoặc import dần vào đây (`app/`, `alembic/`).

Cấu trúc mục tiêu (khớp Tech Spec v2):

```text
apps/api/
├── app/
│   ├── main.py
│   ├── db.py
│   ├── models/
│   ├── routers/
│   ├── services/
│   ├── tools/
│   └── schemas/
├── alembic/
│   └── versions/
├── alembic.ini
└── pyproject.toml   # hoặc requirements.txt
```

## Chạy local nhanh (mock-first)

1. Cài dependency ở root:
   - `pip install -r requirements.txt`
2. Chạy API:
   - `uvicorn app.main:app --reload --port 8000` (thực thi trong `apps/api`)
3. Endpoints:
   - `GET /api/health`
   - `GET /api/chat/history?session_id=<uuid>`
   - `POST /api/chat` với `mode=simple` hoặc `mode=agent`

## Tránh lỗi CORS khi dev localhost

Backend đọc danh sách origin từ biến môi trường `CORS_ORIGINS` (chuỗi phân tách bởi dấu phẩy).

Ví dụ khi FE có thể chạy ở nhiều port:

```text
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173
```

Checklist nhanh:

1. Xác nhận URL FE thực tế trên terminal Vite (ví dụ `http://localhost:5173`).
2. Đảm bảo URL đó có trong `CORS_ORIGINS`.
3. Restart backend sau khi sửa `.env`.
4. Kiểm tra `GET /api/health` thành công trước khi test gửi chat.
