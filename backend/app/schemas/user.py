from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_admin: bool
    timezone: str
    avatar_url: Optional[str] = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    timezone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserChangePassword(BaseModel):
    current_password: str
    new_password: str
