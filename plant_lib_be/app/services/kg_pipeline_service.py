from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.kg_pipeline import get_pipeline_bundle
from app.kg_pipeline.database import session_manager
from app.kg_pipeline.database.models import User


class KGPipelineService:
    def __init__(self):
        # Dùng session_manager nhẹ nhàng cho CRUD session; pipeline sẽ init khi cần
        self.pipeline = None
        self.sessions = session_manager

    def _ensure_pipeline(self):
        if self.pipeline is not None:
            return
        try:
            bundle = get_pipeline_bundle()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"KG pipeline init failed: {exc}",
            )
        self.pipeline = bundle.pipeline
        # session_manager từ bundle có thể khác? dùng chung để đồng bộ
        self.sessions = bundle.session_manager

    def create_user(self, username: str, email: str, password: str, full_name: str | None = None) -> User:
        try:
            return self.sessions.create_user(username=username, email=email, password=password, full_name=full_name)
        except IntegrityError:
            # Trùng username/email
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username hoặc email đã tồn tại",
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Không thể tạo user: {exc}",
            )

    def create_session(self, username: str, password: str, ip_address: str | None, user_agent: str | None):
        user = self.sessions.authenticate_user(username, password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        return self.sessions.create_session(user_id=user.id, ip_address=None, user_agent=None)

    def create_chat_session(self, auth_token: str, ip_address: str | None, user_agent: str | None):
        parent = self.sessions.get_session(auth_token)
        if not parent:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        return self.sessions.create_session(user_id=parent["user_id"], ip_address=None, user_agent=None)

    def list_chat_sessions(self, auth_token: str):
        parent = self.sessions.get_session(auth_token)
        if not parent:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        sessions = self.sessions.list_sessions_for_user(parent["user_id"])
        # Loại bỏ session login hiện tại để tránh lẫn với chat
        sessions = [s for s in sessions if s.get("session_token") != auth_token]
        return sessions

    def get_chat_history(self, session_token: str, limit: int = 50):
        session = self.sessions.get_session(session_token)
        if not session:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token")
        return self.sessions.get_chat_history(session_id=session["id"], limit=limit)

    def delete_chat_session(self, auth_token: str, session_token: str):
        parent = self.sessions.get_session(auth_token)
        if not parent:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        ok = self.sessions.delete_session(session_token=session_token, user_id=parent["user_id"])
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return {"deleted": True}

    def process_query(self, session_token: str, query: str, image_path: str | None, use_cache: bool = True):
        self._ensure_pipeline()
        return self.pipeline.process_query(
            session_token=session_token,
            query=query,
            image_path=image_path,
            use_cache=use_cache,
        )
