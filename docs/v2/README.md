# Tài liệu kỹ thuật phiên bản 2 (API + ReAct + DB mở rộng)

Các file trong thư mục này mô tả **thiết kế tích hợp backend** cho chatbot du lịch và agent ReAct. Tài liệu tổng quan cũ vẫn nằm ở thư mục [docs/](../) (`TECH-SPEC` v1.2, `DATABASE-DESIGN` v3.0).

| Tài liệu | Mô tả ngắn |
|----------|------------|
| [API-DESIGN-travel-chat-backend.md](API-DESIGN-travel-chat-backend.md) | Hợp đồng REST (`/api/chat`, history, health, lỗi). |
| [BACKEND-TOOLS-REACT-TRAVEL.md](BACKEND-TOOLS-REACT-TRAVEL.md) | Tool Registry, orchestrator, bộ tool du lịch gợi ý. |
| [DATABASE-DESIGN-chatbot-du-lich-v4.md](DATABASE-DESIGN-chatbot-du-lich-v4.md) | Metadata `lab_metric_log`, bảng `tool_invocation` tuỳ chọn. |
| [TECH-SPEC-chatbot-du-lich-v2-integrated.md](TECH-SPEC-chatbot-du-lich-v2-integrated.md) | Kiến trúc `apps/api`, luồng simple vs agent. |
| [LAB3_BACKEND_AI_MASTER_SPEC.md](LAB3_BACKEND_AI_MASTER_SPEC.md) | Bản master cho người mới: folder, logic backend/agent, tool, DB, workflow, trình bày đo lường. |
