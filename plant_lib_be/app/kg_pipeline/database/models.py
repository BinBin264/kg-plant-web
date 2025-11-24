import hashlib
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "kg_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)

    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    chat_histories = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


class UserSession(Base):
    __tablename__ = "kg_user_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("kg_users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")
    chat_histories = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")
    query_caches = relationship("QueryCache", back_populates="session", cascade="all, delete-orphan")

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def extend_session(self, hours: int = 24):
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()


class ChatHistory(Base):
    __tablename__ = "kg_chat_histories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("kg_user_sessions.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("kg_users.id"), nullable=False, index=True)

    query = Column(Text, nullable=False)
    query_language = Column(String(10), default="vi")
    intent = Column(String(50))

    answer = Column(Text)
    answer_language = Column(String(10))

    pipeline_data = Column(JSON)

    image_path = Column(Text)
    total_results = Column(Integer, default=0)
    processing_time = Column(Integer)
    from_cache = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user_rating = Column(Integer)
    user_feedback = Column(Text)

    session = relationship("UserSession", back_populates="chat_histories")
    user = relationship("User", back_populates="chat_histories")


class QueryCache(Base):
    __tablename__ = "kg_query_caches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("kg_user_sessions.id"), nullable=False, index=True)

    query_hash = Column(String(64), unique=True, nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    image_path = Column(Text)

    cached_result = Column(JSON, nullable=False)

    hit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    session = relationship("UserSession", back_populates="query_caches")

    @staticmethod
    def generate_hash(query: str, image_path: str | None = None) -> str:
        key = f"{query.strip().lower()}|{image_path or ''}"
        return hashlib.sha256(key.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
