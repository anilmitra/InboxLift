from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.ai_settings import AIProvider


class AISettingsUpdate(BaseModel):
    provider: Optional[AIProvider] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class AISettingsOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: Optional[int] = None
    provider: AIProvider
    model: str
    temperature: float
    max_tokens: int
    is_active: bool
    has_api_key: bool
    updated_at: datetime


class AvailableModel(BaseModel):
    id: str
    name: str
    provider: AIProvider
    context_length: int
    description: str
