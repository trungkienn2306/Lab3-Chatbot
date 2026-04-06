# Tech Spec — Chatbot tra cứu thông tin du lịch

**Phiên bản:** 1.2  
**Đi kèm PRD:** `docs/PRD-chatbot-du-lich.md`  
**Database:** `docs/DATABASE-DESIGN-chatbot-du-lich.md`

---

## 1. Tổng quan kiến trúc

- **Monorepo** chứa frontend (React + Vite + Tailwind) và backend **Python**; toàn bộ **định nghĩa bảng + migration** nằm trong **cùng service API** nhờ **SQLAlchemy 2.x** (ORM / Core) và **Alembic** (migration — vai trò tương tự Prisma Migrate trong hệ sinh thái Python).
- **Vì sao không dùng Prisma:** Prisma thiên về Node/TypeScript; **SQLAlchemy + Alembic** phù hợp backend Python với schema **`chat_message` + `lab_metric_log`** (lab đơn giản — xem [DATABASE-DESIGN-chatbot-du-lich.md](DATABASE-DESIGN-chatbot-du-lich.md) v3.0).

```mermaid
flowchart LR
  subgraph client [Browser]
    FE[React Vite Tailwind]
  end
  subgraph server [Backend]
    API[Python API]
    ORM[SQLAlchemy]
    Mig[Alembic]
    LLM[LLM Provider]
  end
  subgraph data [Data]
    PG[(PostgreSQL)]
  end
  FE -->|HTTPS JSON| API
  API --> ORM
  API --> LLM
  ORM -->|SQL| PG
  Mig -.->|upgrade heads| PG
```

---

## 2. Cấu trúc monorepo (đã áp dụng trong repo)

```
repo-root/
├── package.json             # npm workspaces: `apps/web`; script `dev:web`, `build:web`
├── apps/
│   ├── web/                 # React 19 + Vite 8 + TypeScript + Tailwind CSS v4 (@tailwindcss/vite)
│   │   ├── src/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   └── package.json     # name: "web"
│   └── api/                 # Python API (FastAPI + SQLAlchemy + Alembic) — scaffold
│       ├── README.md
│       ├── app/
│       │   └── models/      # chat_message, lab_metric_log
│       └── alembic/
│           └── versions/
├── docs/                    # PRD, TECH-SPEC, DATABASE-DESIGN
├── src/                     # Mã lab gốc (ReAct agent, providers, …) — giữ tại root cho tới khi gom vào apps/api
├── tests/
├── requirements.txt
└── .env                     # không commit; xem mục 6
```

**Sau này:** thêm `apps/api/alembic.ini`, `app/db.py`, `alembic/env.py` và có thể **di chuyển** (hoặc tái sử dụng) mã từ `src/` vào `apps/api`.

**Tuỳ chọn:** package Python dùng chung `packages/py-db/`; giữ model + Alembic trong `apps/api` là đủ cho quy mô lab.

---

## 3. Frontend — `apps/web`

### 3.1 Stack

- **React 19**, **Vite 8**, **TypeScript** (đã cài trong `apps/web`).
- **Tailwind CSS v4** (`tailwindcss` + `@tailwindcss/vite`) — theme tokens trong `src/index.css` (`@theme`).
- Gọi REST (hoặc SSE/WebSocket sau này) tới Python API.

### 3.2 UI/UX — chủ đề du lịch

Tham khảo xu hướng UI ứng dụng booking/du lịch: **xanh nước biển + cyan nhạt** (cảm giác bầu trời/biển), điểm nhấn **coral / rose gold** hoặc **vàng nắng** cho CTA; nền **trắng kem / xám lạnh** để nội dung chat dễ đọc.

**Gợi ý palette (tùy chỉnh trong `tailwind.config`):**

| Token gợi ý | Hex (tham khảo) | Dùng cho |
|-------------|-----------------|----------|
| `brand.sky` | `#20b5f4` | header gradient, liên kết |
| `brand.cyan` | `#8ce4fc` | highlight nhẹ, bubble bot |
| `brand.teal` | `#1098a4` | viền, icon |
| `brand.ocean` | `#334f5f` | text phụ, footer |
| `accent.sun` | `#F9C74F` | nút gửi / CTA |
| `accent.rose` | `#b16474` | badge, trạng thái |

**UX patterns:**

- **Rail trái:** menu, branding (máy bay), nút **Đoạn chat mới** (xóa luồng hiện tại); **không** danh sách nhiều hội thoại; thu gọn / drawer mobile.
- **Vùng tin nhắn:** bubble user căn phải (màu đậm hơn), bot căn trái (nền cyan nhạt / glass).
- **Hero pattern (tùy chọn):** ảnh nền mờ (destination) + lớp phủ gradient để không làm phân tâm chữ.
- **Typography:** sans hiện đại (Inter, DM Sans, hoặc Plus Jakarta Sans).
- **Spacing:** padding rộng rãi, bo góc lớn (`rounded-2xl`), đổ bóng nhẹ cho card input.
- **Mobile:** ô nhập cố định dưới đáy; safe-area cho iOS.

**Nguồn cảm hứng thiết kế:** Dribbble/Behance từ khóa “travel app UI”, “flight booking”; palette tương tự bộ màu booking trên [ColorsWall](https://colorswall.com/palette/219869) (xanh/cyan/teal + accent ấm).

### 3.3 Trạng thái client (khớp DB)

- **`travel_chat_messages`:** một mảng JSON toàn bộ tin của **đoạn chat hiện tại**.
- **`travel_chat_session_id`:** UUID phiên; **đổi mới** khi user bấm *Đoạn chat mới* (gửi kèm API sau này).
- Migrate từ bản đa hội thoại: xem [apps/web/README.md](../apps/web/README.md).

### 3.4 API surface (gợi ý)

| Method | Path | Mô tả |
|--------|------|--------|
| `GET` | `/api/health` | Kiểm tra sống |
| `GET` | `/api/chat/history?session_id=&limit=` | Lịch sử tin theo phiên hiện tại |
| `POST` | `/api/chat` | Body: `{ session_id, message }` → lưu user + assistant; stream hoặc JSON `{ reply }` |

Chi tiết payload có thể mở rộng (`client_message_id`, `correlation_id` cho metric).

---

## 4. Backend — `apps/api` (Python)

### 4.1 Stack gợi ý

- **FastAPI** + **Uvicorn** (hoặc framework tương đương).
- **SQLAlchemy 2.x** (ORM) + **Alembic** (migration).
- Driver: **asyncpg** (async) hoặc **psycopg** v3 — kết hợp `sqlalchemy[asyncio]` nếu dùng async session.
- **Tuỳ chọn:** [SQLModel](https://sqlmodel.tiangolo.com/) (Pydantic + SQLAlchemy) nếu muốn model gọn cho FastAPI; migration vẫn dùng Alembic.
- Tích hợp LLM: OpenAI / Gemini / provider có sẵn trong lab — API key qua biến môi trường.

### 4.2 Luồng xử lý `POST /api/chat`

1. Validate `session_id` + nội dung tin.
2. **INSERT** `chat_message` role `user` (theo `session_id`).
3. Nạp ngữ cảnh gần đây (N tin) cùng `session_id`.
4. Gọi LLM → **INSERT** `chat_message` role `assistant`.
5. (Tuỳ chọn Lab 3) **INSERT** `lab_metric_log` (`session_id`, `component=travel_chat`, `event_type`, `duration_ms`, token nếu có).
6. Trả về client (JSON hoặc SSE).

### 4.3 Ghi metric Lab 3 (`lab_metric_log`)

- **Mục đích:** phục vụ báo cáo nhóm / phân tích giống tiêu chí [EVALUATION.md](../EVALUATION.md) (latency, token, bước vòng lặp, mã lỗi), có thể truy vấn bằng SQL.
- **Nguồn dữ liệu:** (1) pipeline chat du lịch `component=travel_chat`; (2) khi tích hợp agent gốc repo, có thể ghi thêm `react_agent` / `chatbot_baseline` từ `src/telemetry` hoặc sau mỗi lần chạy test — **song song** với file `logs/*.json`, không thay thế trace đầy đủ.
- **Trường chính:** xem [DATABASE-DESIGN-chatbot-du-lich.md](DATABASE-DESIGN-chatbot-du-lich.md) §4.

### 4.4 System prompt (gợi ý ngắn)

- Bot chỉ ưu tiên **tư vấn du lịch**; từ chối lịch sự ngoài phạm vi.
- Nhắc trả lời có cấu trúc (gạch đầu dòng), không khẳng định giá vé/thời gian thực nếu không có tool cập nhật.

### 4.5 Bảo mật & vận hành tối thiểu

- CORS: chỉ origin của Vite dev và domain production.
- Rate limit theo IP hoặc theo `session_id` (khuyến nghị).
- Không trả `DATABASE_URL` hay API key ra client.

---

## 5. SQLAlchemy, Alembic & PostgreSQL

### 5.1 Vai trò trong dự án nhỏ

| Thành phần | Vai trò (tương đương Prisma Migrate / schema) |
|------------|-------------------------------------|
| **SQLAlchemy `DeclarativeBase` + model** | Định nghĩa `chat_message`, `lab_metric_log` — single source of truth. |
| **Alembic** | Sinh và áp dụng file migration (`alembic revision --autogenerate` → `alembic upgrade head`). |
| **`DATABASE_URL`** | Cùng một chuỗi cho engine SQLAlchemy và `env.py` của Alembic. |

### 5.2 Lệnh dev tiêu biểu

Chạy trong `apps/api` (hoặc thư mục gốc Python đã cấu hình Alembic):

```bash
# Tạo migration từ thay đổi model (sau khi chỉnh SQLAlchemy model)
alembic revision --autogenerate -m "chat_message_lab_metric"

# Áp dụng lên DB local
alembic upgrade head
```

Xem dữ liệu: **pgAdmin**, **DBeaver**, hoặc `psql` — không bắt buộc GUI riêng như Prisma Studio.

### 5.3 Gói phụ thuộc Python (gợi ý tối thiểu)

```
sqlalchemy>=2
alembic
asyncpg
# hoặc psycopg[binary] nếu dùng driver sync
```

---

## 6. Biến môi trường

| Biến | Mô tả |
|------|--------|
| `DATABASE_URL` | Chuỗi kết nối PostgreSQL (dev local như PRD lab). |
| `LLM_API_KEY` / tên tương đương | Khóa nhà cung cấp model. |
| `CORS_ORIGINS` | Danh sách origin cho FE. |

**Dev local (theo yêu cầu):**

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/postgres?schema=public"
```

---

## 7. Chạy local (mục tiêu trải nghiệm dev)

1. Khởi động PostgreSQL (Docker hoặc service local).
2. Trong `apps/api`: cấu hình `DATABASE_URL`, chạy `alembic upgrade head` để tạo/cập nhật bảng.
3. Chạy API (port ví dụ `8000`).
4. Chạy frontend: từ root `npm run dev:web`, hoặc `cd apps/web && npm run dev` (port mặc định Vite thường là `5173`).
5. Mở trình duyệt tới URL Vite; kiểm tra chat, *Đoạn chat mới*, và reload.

---

## 8. Kiểm thử gợi ý

- Gửi vài tin; reload; kiểm tra history theo `session_id`.
- *Đoạn chat mới* trên FE → `session_id` mới → lịch sử API theo id mới trống; phiên cũ vẫn có thể còn trong DB (tuỳ chính sách xóa).
- API lỗi LLM → thông báo UI; tuỳ chọn ghi `lab_metric_log` với `error_code`.
- Export / query metric: `SELECT` trên `lab_metric_log` so khớp với mẫu trong [EVALUATION.md](../EVALUATION.md).

---

## 9. Phụ lục: mapping PRD → kỹ thuật

| PRD | Kỹ thuật |
|-----|----------|
| Một màn chat | Single route `/`, layout chat + rail |
| Không login | `session_id` do client + `chat_message` |
| Một cửa sổ + đoạn mới | Đổi `session_id`, xóa `localStorage` messages |
| Metric báo cáo Lab 3 | `lab_metric_log` + `logs/*.json` |
| Theme du lịch | Tailwind + icon máy bay, palette mục 3.2 |
