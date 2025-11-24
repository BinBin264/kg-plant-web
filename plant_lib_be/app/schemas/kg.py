from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class KGUserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class KGUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None


class KGSessionCreate(BaseModel):
    username: str
    password: str


class KGChatSessionCreate(BaseModel):
    auth_token: str = Field(..., description="session_token nhận được sau khi login")


class KGSessionOut(BaseModel):
    session_token: str
    expires_at: str
    user_id: str

class KGSessionShort(BaseModel):
    session_token: str
    created_at: str
    expires_at: str
    is_active: bool


class KGQueryRequest(BaseModel):
    session_token: str
    query: str
    image_path: Optional[str] = None
    use_cache: bool = True


class KGQueryResponse(BaseModel):
    query: str
    image_path: Optional[str] = None
    answer: str
    success: bool
    from_cache: bool = False
    pipeline: Dict[str, Any]
    metadata: Dict[str, Any]


class KGChatHistoryItem(BaseModel):
    id: str
    query: str
    answer: Optional[str] = None
    created_at: Optional[str] = None
    image_path: Optional[str] = None
    intent: Optional[str] = None
    from_cache: Optional[bool] = None
    processing_time: Optional[int] = None


class KGChatHistoryOut(BaseModel):
    items: list[KGChatHistoryItem]
