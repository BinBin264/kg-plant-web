from functools import lru_cache

from fastapi import APIRouter, Depends

from app.schemas.kg import (
    KGChatSessionCreate,
    KGChatHistoryOut,
    KGQueryRequest,
    KGQueryResponse,
    KGSessionCreate,
    KGSessionOut,
    KGSessionShort,
    KGUserCreate,
    KGUserOut,
)
from app.services.kg_pipeline_service import KGPipelineService

router = APIRouter(prefix="/kg", tags=["knowledge-graph"])


@lru_cache(maxsize=1)
def get_kg_service() -> KGPipelineService:
    return KGPipelineService()


@router.post("/register", response_model=KGUserOut)
def register(payload: KGUserCreate, svc: KGPipelineService = Depends(get_kg_service)):
    # Alias cho đăng ký
    return svc.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )


@router.post("/sessions", response_model=KGSessionOut)
def create_kg_session(payload: KGSessionCreate, svc: KGPipelineService = Depends(get_kg_service)):
    session = svc.create_session(
        username=payload.username,
        password=payload.password,
        ip_address=None,
        user_agent=None,
    )
    return {
        "session_token": session.session_token,
        "expires_at": session.expires_at.isoformat(),
        "user_id": session.user_id,
    }


@router.post("/login", response_model=KGSessionOut)
def login(payload: KGSessionCreate, svc: KGPipelineService = Depends(get_kg_service)):
    # Alias cho đăng nhập
    session = svc.create_session(
        username=payload.username,
        password=payload.password,
        ip_address=None,
        user_agent=None,
    )
    return {
        "session_token": session.session_token,
        "expires_at": session.expires_at.isoformat(),
        "user_id": session.user_id,
    }


@router.post("/chat-sessions", response_model=KGSessionOut)
def create_chat_session(payload: KGChatSessionCreate, svc: KGPipelineService = Depends(get_kg_service)):
    # Tạo thêm session chat mới cho user đã login bằng auth_token
    session = svc.create_chat_session(
        auth_token=payload.auth_token,
        ip_address=None,
        user_agent=None,
    )
    return {
        "session_token": session.session_token,
        "expires_at": session.expires_at.isoformat(),
        "user_id": session.user_id,
    }


@router.get("/chat-sessions", response_model=list[KGSessionShort])
def list_chat_sessions(auth_token: str = "", svc: KGPipelineService = Depends(get_kg_service)):
    sessions = svc.list_chat_sessions(auth_token)
    normalized = []
    for s in sessions:
        normalized.append(
            {
                "session_token": s["session_token"],
                "created_at": s["created_at"].isoformat() if s.get("created_at") else "",
                "expires_at": s["expires_at"].isoformat() if s.get("expires_at") else "",
                "is_active": bool(s.get("is_active")),
            }
        )
    return normalized


@router.delete("/chat-sessions", response_model=dict)
def delete_chat_session(auth_token: str, session_token: str, svc: KGPipelineService = Depends(get_kg_service)):
    return svc.delete_chat_session(auth_token=auth_token, session_token=session_token)


@router.get("/chat-history", response_model=KGChatHistoryOut)
def get_chat_history(session_token: str, limit: int = 50, svc: KGPipelineService = Depends(get_kg_service)):
    history = svc.get_chat_history(session_token=session_token, limit=limit)
    # Normalize datetime to iso string
    items = []
    for h in history:
        items.append(
            {
                "id": h.get("id"),
                "query": h.get("query"),
                "answer": h.get("answer"),
                "intent": h.get("intent"),
                "created_at": h.get("created_at").isoformat() if h.get("created_at") else "",
                "image_path": h.get("image_path") or "",
                "from_cache": h.get("from_cache"),
                "processing_time": h.get("processing_time"),
            }
        )
    return {"items": items}


@router.post("/query", response_model=KGQueryResponse)
def run_kg_query(payload: KGQueryRequest, svc: KGPipelineService = Depends(get_kg_service)):
    return svc.process_query(
        session_token=payload.session_token,
        query=payload.query,
        image_path=payload.image_path,
        use_cache=payload.use_cache,
    )
