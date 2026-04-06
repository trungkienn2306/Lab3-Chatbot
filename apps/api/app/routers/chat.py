from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse, MessageDTO
from app.services.chat_service import ChatService
from app.services.history_service import HistoryService

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history(
    session_id: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    history = HistoryService(db).get_history(session_id=session_id, limit=limit)
    dto = [
        MessageDTO(
            id=item.id,
            role=item.role,
            content=item.content,
            created_at=item.created_at,
        )
        for item in history
    ]
    return ChatHistoryResponse(session_id=session_id, messages=dto)


@router.post("", response_model=ChatResponse)
def post_chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    try:
        return ChatService(db).handle_turn(req)
    except Exception as exc:
        # Tra loi loi than thien cho luong user-facing (friendly error for user-facing flow).
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Khong the xu ly yeu cau chat luc nay.",
                    "details": str(exc),
                }
            },
        ) from exc
