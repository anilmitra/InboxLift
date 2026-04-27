from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class ESPStats(BaseModel):
    esp: str  # google / microsoft / others
    total_sent: int = 0
    inbox: int = 0
    spam: int = 0
    other: int = 0
    undelivered: int = 0
    replies: int = 0
    deliverability_rate: float = 0.0
    score: float = 0.0


class DailyStats(BaseModel):
    date: date
    emails_sent: int = 0
    replies: int = 0
    inbox: int = 0
    spam_rescued: int = 0
    other: int = 0
    undelivered: int = 0


class PlacementBreakdown(BaseModel):
    inbox: int = 0
    spam_rescued: int = 0
    other: int = 0
    undelivered: int = 0


class AccountReport(BaseModel):
    account_id: int
    account_email: str
    status: str
    period_days: int
    total_sent: int = 0
    total_received: int = 0
    total_replies: int = 0
    deliverability_score: float = 0.0
    google_score: float = 0.0
    microsoft_score: float = 0.0
    others_score: float = 0.0
    placement: PlacementBreakdown
    esp_stats: List[ESPStats]
    daily_stats: List[DailyStats]


class AnalyticsOverview(BaseModel):
    total_accounts: int = 0
    active_accounts: int = 0
    needs_recovery: int = 0
    total_emails_sent: int = 0
    avg_deliverability_score: float = 0.0
    accounts_summary: List[dict] = []
