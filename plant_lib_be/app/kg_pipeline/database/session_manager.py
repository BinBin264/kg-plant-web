import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import func

from app.kg_pipeline.config import get_logger, settings
from app.kg_pipeline.database.connection import db_connection
from app.kg_pipeline.database.models import ChatHistory, QueryCache, User, UserSession

logger = get_logger(__name__)


class SessionManager:
    def __init__(self):
        self.cache_ttl_hours = settings.cache.ttl_hours
        self.session_ttl_hours = settings.cache.session_ttl_hours
        logger.info("KG session manager initialized")

    def create_user(self, username: str, email: str, password: str, full_name: str | None = None) -> User:
        db = db_connection.get_session()
        try:
            user = User(username=username, email=email, full_name=full_name)
            user.set_password(password)

            db.add(user)
            db.commit()
            db.refresh(user)

            db.expunge(user)
            logger.info(f"KG user created: {user.username}")
            return user
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to create KG user {username}: {exc}")
            raise exc
        finally:
            db.close()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        db = db_connection.get_session()
        try:
            user = (
                db.query(User)
                .filter(User.username == username, User.is_active.is_(True))
                .first()
            )
            if user and user.check_password(password):
                user.last_login = datetime.utcnow()
                db.commit()
                db.refresh(user)
                db.expunge(user)
                logger.info(f"KG user authenticated: {username}")
                return user

            logger.warning(f"Authentication failed for user: {username}")
            return None
        finally:
            db.close()

    def create_session(self, user_id: str, ip_address: str | None = None, user_agent: str | None = None) -> UserSession:
        db = db_connection.get_session()
        try:
            session_token = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(hours=self.session_ttl_hours)

            session = UserSession(
                user_id=user_id,
                session_token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(session)
            db.commit()
            db.refresh(session)

            db.expunge(session)
            logger.info(f"KG session created for user: {user_id}")
            return session
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to create KG session: {exc}")
            raise exc
        finally:
            db.close()

    def get_session(self, session_token: str) -> Optional[Dict]:
        db = db_connection.get_session()
        try:
            session = (
                db.query(UserSession)
                .filter(UserSession.session_token == session_token, UserSession.is_active.is_(True))
                .first()
            )

            if session and not session.is_expired:
                session.last_activity = datetime.utcnow()
                db.commit()

                session_dict = {
                    "id": session.id,
                    "user_id": session.user_id,
                    "session_token": session.session_token,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                    "last_activity": session.last_activity,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "is_active": session.is_active,
                }
                return session_dict

            return None
        finally:
            db.close()

    def cleanup_expired_sessions(self) -> int:
        db = db_connection.get_session()
        try:
            expired_count = (
                db.query(UserSession)
                .filter(UserSession.expires_at < datetime.utcnow())
                .delete()
            )
            db.commit()
            logger.info(f"Cleaned up {expired_count} expired KG sessions")
            return expired_count
        finally:
            db.close()

    def delete_session(self, session_token: str, user_id: str) -> bool:
        db = db_connection.get_session()
        try:
            session = (
                db.query(UserSession)
                .filter(UserSession.session_token == session_token, UserSession.user_id == user_id)
                .first()
            )
            if not session:
                return False
            db.delete(session)
            db.commit()
            return True
        finally:
            db.close()

    def list_sessions_for_user(self, user_id: str, limit: int = 50) -> list[dict]:
        db = db_connection.get_session()
        try:
            sessions = (
                db.query(UserSession)
                .filter(UserSession.user_id == user_id)
                .order_by(UserSession.created_at.desc())
                .limit(limit)
                .all()
            )
            result: list[dict] = []
            for sess in sessions:
                result.append(
                    {
                        "id": sess.id,
                        "user_id": sess.user_id,
                        "session_token": sess.session_token,
                        "created_at": sess.created_at,
                        "expires_at": sess.expires_at,
                        "last_activity": sess.last_activity,
                        "is_active": sess.is_active,
                    }
                )
            return result
        finally:
            db.close()

    def get_cached_query(self, session_id: str, query: str, image_path: str | None = None) -> Optional[Dict]:
        db = db_connection.get_session()
        try:
            query_hash = QueryCache.generate_hash(query, image_path)
            cache = (
                db.query(QueryCache)
                .filter(QueryCache.session_id == session_id, QueryCache.query_hash == query_hash)
                .first()
            )

            if cache and not cache.is_expired:
                cache.hit_count += 1
                cache.last_accessed = datetime.utcnow()
                db.commit()

                logger.debug(f"KG cache hit for query hash: {query_hash[:8]}")
                return cache.cached_result

            return None
        finally:
            db.close()

    def set_cached_query(self, session_id: str, query: str, result: Dict, image_path: str | None = None):
        db = db_connection.get_session()
        try:
            query_hash = QueryCache.generate_hash(query, image_path)
            expires_at = datetime.utcnow() + timedelta(hours=self.cache_ttl_hours)

            cache = db.query(QueryCache).filter(QueryCache.query_hash == query_hash).first()
            if cache:
                cache.cached_result = result
                cache.expires_at = expires_at
                cache.last_accessed = datetime.utcnow()
            else:
                cache = QueryCache(
                    session_id=session_id,
                    query_hash=query_hash,
                    query_text=query,
                    image_path=image_path,
                    cached_result=result,
                    expires_at=expires_at,
                )
                db.add(cache)

            db.commit()
            logger.debug(f"KG query cached: {query_hash[:8]}")
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to cache KG query: {exc}")
            raise exc
        finally:
            db.close()

    def cleanup_expired_cache(self) -> int:
        db = db_connection.get_session()
        try:
            expired_count = (
                db.query(QueryCache)
                .filter(QueryCache.expires_at < datetime.utcnow())
                .delete()
            )
            db.commit()
            logger.info(f"Cleaned up {expired_count} expired KG cache entries")
            return expired_count
        finally:
            db.close()

    def save_chat_history(
        self,
        session_id: str,
        user_id: str,
        query: str,
        answer: str,
        pipeline_data: Dict,
        **kwargs,
    ) -> ChatHistory:
        db = db_connection.get_session()
        try:
            chat = ChatHistory(
                session_id=session_id,
                user_id=user_id,
                query=query,
                answer=answer,
                pipeline_data=pipeline_data,
                **kwargs,
            )

            db.add(chat)
            db.commit()
            db.refresh(chat)
            db.expunge(chat)

            logger.debug(f"KG chat history saved for session: {session_id}")
            return chat
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to save KG chat history: {exc}")
            raise exc
        finally:
            db.close()

    def get_session_stats(self, session_id: str) -> Dict:
        db = db_connection.get_session()
        try:
            chat_count = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).count()
            cache_count = db.query(QueryCache).filter(QueryCache.session_id == session_id).count()
            cache_hits = (
                db.query(QueryCache)
                .filter(QueryCache.session_id == session_id)
                .with_entities(QueryCache.hit_count)
                .all()
            )
            total_hits = sum(hit[0] for hit in cache_hits)

            return {
                "chat_count": chat_count,
                "cache_count": cache_count,
                "total_cache_hits": total_hits,
                "cache_hit_rate": f"{(total_hits / max(chat_count, 1)) * 100:.1f}%",
            }
        finally:
            db.close()

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        db = db_connection.get_session()
        try:
            chats = (
                db.query(ChatHistory)
                .filter(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.created_at.asc())
                .limit(limit)
                .all()
            )
            chat_list: List[Dict] = []
            for chat in chats:
                chat_list.append(
                    {
                        "id": chat.id,
                        "query": chat.query,
                        "answer": chat.answer,
                        "intent": chat.intent,
                        "image_path": chat.image_path,
                        "created_at": chat.created_at,
                        "from_cache": chat.from_cache,
                        "processing_time": chat.processing_time,
                    }
                )
            return chat_list
        finally:
            db.close()


session_manager = SessionManager()
