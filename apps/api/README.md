# API (Python) — `apps/api`

Thư mục dành cho **FastAPI + SQLAlchemy + Alembic** theo `docs/TECH-SPEC-chatbot-du-lich.md`.

**Hiện trạng:** mã lab ReAct/chatbot gốc vẫn nằm ở `src/` ở root repo. Khi tích hợp, có thể di chuyển hoặc import dần vào đây (`app/`, `alembic/`).

Cấu trúc mục tiêu:

```
apps/api/
├── app/
│   ├── models/
│   ├── db.py
│   └── ...
├── alembic/
│   └── versions/
├── alembic.ini
└── pyproject.toml   # hoặc requirements.txt
```
