from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage


class HistoryService:
    def __init__(self, db: Session):
        self.db = db

    def add_message(self, *, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_history(self, *, session_id: str, limit: int = 100) -> list[ChatMessage]:
        stmt: Select[tuple[ChatMessage]] = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
