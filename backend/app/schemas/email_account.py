from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.email_account import EmailProvider, AccountStatus


class EmailAccountCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None
    provider: EmailProvider = EmailProvider.CUSTOM
    smtp_host: str = Field(min_length=1)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_use_tls: bool = True
    imap_host: str = Field(min_length=1)
    imap_port: int = Field(default=993, ge=1, le=65535)
    imap_use_ssl: bool = True
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    daily_warmup_limit: int = Field(default=50, ge=1, le=500)
    ramp_up_days: int = Field(default=30, ge=7, le=90)


class EmailAccountUpdate(BaseModel):
    display_name: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = Field(default=None, ge=1, le=65535)
    smtp_use_tls: Optional[bool] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = Field(default=None, ge=1, le=65535)
    imap_use_ssl: Optional[bool] = None
    username: Optional[str] = None
    password: Optional[str] = None
    daily_warmup_limit: Optional[int] = Field(default=None, ge=1, le=500)
    ramp_up_days: Optional[int] = Field(default=None, ge=7, le=90)


class EmailAccountOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    email: str
    display_name: Optional[str] = None
    provider: EmailProvider
    smtp_host: str
    smtp_port: int
    smtp_use_tls: bool
    imap_host: str
    imap_port: int
    imap_use_ssl: bool
    username: str
    warming_enabled: bool
    status: AccountStatus
    daily_warmup_limit: int
    ramp_up_days: int
    current_warmup_day: int
    emails_sent_today: int
    warmup_start_date: Optional[datetime] = None
    last_warmup_at: Optional[datetime] = None
    deliverability_score: float
    total_sent: int
    total_inbox: int
    total_spam_rescued: int
    target_emails_today: int
    last_connection_error: Optional[str] = None
    connection_tested_at: Optional[datetime] = None
    created_at: datetime


class ConnectionTestResult(BaseModel):
    success: bool
    smtp_ok: bool
    imap_ok: bool
    error: Optional[str] = None
    latency_ms: Optional[float] = None
