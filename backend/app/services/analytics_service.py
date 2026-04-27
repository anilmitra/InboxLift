"""Analytics aggregation and scoring."""
from datetime import date, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import structlog

from app.models.analytics import AnalyticsSnapshot
from app.models.warmup_email import WarmupEmail, EmailStatus
from app.models.email_account import EmailAccount, AccountStatus
from app.schemas.analytics import (
    AccountReport,
    DailyStats,
    ESPStats,
    PlacementBreakdown,
    AnalyticsOverview,
)

logger = structlog.get_logger(__name__)


def _compute_deliverability_score(
    sent: int,
    inbox: int,
    spam_rescued: int,
    spam: int,
    other: int,
    undelivered: int,
) -> float:
    """Score from 0-100. Inbox = full points, spam_rescued = 70%, other = 50%, undelivered/spam = 0%."""
    if sent == 0:
        return 0.0
    weighted = inbox * 100 + spam_rescued * 70 + other * 50
    return round(min(weighted / sent, 100.0), 1)


def _esp_for_domain(email: str) -> str:
    domain = email.split("@")[-1].lower()
    google = {"gmail.com", "googlemail.com"}
    ms = {"outlook.com", "hotmail.com", "live.com", "msn.com", "office365.com"}
    if domain in google:
        return "google"
    if domain in ms:
        return "microsoft"
    return "others"


async def build_account_report(
    db: AsyncSession,
    account: EmailAccount,
    days: int = 7,
) -> AccountReport:
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Fetch snapshots
    snapshots_q = await db.execute(
        select(AnalyticsSnapshot)
        .where(
            and_(
                AnalyticsSnapshot.account_id == account.id,
                AnalyticsSnapshot.snapshot_date >= start_date,
                AnalyticsSnapshot.snapshot_date <= end_date,
            )
        )
        .order_by(AnalyticsSnapshot.snapshot_date)
    )
    snapshots = snapshots_q.scalars().all()

    # Aggregate totals
    total_sent = sum(s.emails_sent for s in snapshots)
    total_inbox = sum(s.emails_inbox for s in snapshots)
    total_spam_rescued = sum(s.emails_spam_rescued for s in snapshots)
    total_spam = sum(s.emails_spam for s in snapshots)
    total_other = sum(s.emails_other for s in snapshots)
    total_undelivered = sum(s.emails_undelivered for s in snapshots)
    total_received = sum(s.replies_received for s in snapshots)
    total_replies = sum(s.replies_sent for s in snapshots)

    score = _compute_deliverability_score(
        total_sent, total_inbox, total_spam_rescued, total_spam, total_other, total_undelivered
    )

    # ESP stats
    def _esp_stats(prefix: str, label: str) -> ESPStats:
        sent = sum(getattr(s, f"{prefix}_sent") for s in snapshots)
        inbox = sum(getattr(s, f"{prefix}_inbox") for s in snapshots)
        spam = sum(getattr(s, f"{prefix}_spam") for s in snapshots)
        other = sum(getattr(s, f"{prefix}_other") for s in snapshots)
        undelivered = sum(getattr(s, f"{prefix}_undelivered") for s in snapshots)
        replies = sum(getattr(s, f"{prefix}_replies") for s in snapshots)
        rate = round((inbox / sent * 100) if sent > 0 else 0.0, 1)
        esp_score = _compute_deliverability_score(sent, inbox, 0, spam, other, undelivered)
        return ESPStats(
            esp=label,
            total_sent=sent,
            inbox=inbox,
            spam=spam,
            other=other,
            undelivered=undelivered,
            replies=replies,
            deliverability_rate=rate,
            score=esp_score,
        )

    esp_list = [
        _esp_stats("google", "google"),
        _esp_stats("microsoft", "microsoft"),
        _esp_stats("others", "others"),
    ]

    # Google / Microsoft / Others scores
    g_score = _compute_deliverability_score(
        sum(s.google_sent for s in snapshots),
        sum(s.google_inbox for s in snapshots),
        0,
        sum(s.google_spam for s in snapshots),
        sum(s.google_other for s in snapshots),
        sum(s.google_undelivered for s in snapshots),
    )
    ms_score = _compute_deliverability_score(
        sum(s.microsoft_sent for s in snapshots),
        sum(s.microsoft_inbox for s in snapshots),
        0,
        sum(s.microsoft_spam for s in snapshots),
        sum(s.microsoft_other for s in snapshots),
        sum(s.microsoft_undelivered for s in snapshots),
    )
    oth_score = _compute_deliverability_score(
        sum(s.others_sent for s in snapshots),
        sum(s.others_inbox for s in snapshots),
        0,
        sum(s.others_spam for s in snapshots),
        sum(s.others_other for s in snapshots),
        sum(s.others_undelivered for s in snapshots),
    )

    # Daily stats
    daily_map: dict[date, DailyStats] = {}
    for d in range(days):
        dd = start_date + timedelta(days=d)
        daily_map[dd] = DailyStats(date=dd)

    for s in snapshots:
        ds = daily_map.get(s.snapshot_date)
        if ds:
            ds.emails_sent = s.emails_sent
            ds.replies = s.replies_sent
            ds.inbox = s.emails_inbox
            ds.spam_rescued = s.emails_spam_rescued
            ds.other = s.emails_other
            ds.undelivered = s.emails_undelivered

    return AccountReport(
        account_id=account.id,
        account_email=account.email,
        status=account.status.value,
        period_days=days,
        total_sent=total_sent,
        total_received=total_received,
        total_replies=total_replies,
        deliverability_score=score,
        google_score=g_score,
        microsoft_score=ms_score,
        others_score=oth_score,
        placement=PlacementBreakdown(
            inbox=total_inbox,
            spam_rescued=total_spam_rescued,
            other=total_other,
            undelivered=total_undelivered,
        ),
        esp_stats=esp_list,
        daily_stats=list(daily_map.values()),
    )


async def update_daily_snapshot(
    db: AsyncSession,
    account_id: int,
    snapshot_date: Optional[date] = None,
):
    """Recompute and upsert analytics snapshot for given date."""
    target_date = snapshot_date or date.today()
    day_start = target_date
    day_end = target_date + timedelta(days=1)

    # Load all warmup emails for this account and date range
    emails_q = await db.execute(
        select(WarmupEmail).where(
            and_(
                WarmupEmail.sender_account_id == account_id,
                func.date(WarmupEmail.sent_at) == target_date,
            )
        )
    )
    emails = emails_q.scalars().all()

    counts: dict = {
        "emails_sent": 0,
        "emails_inbox": 0,
        "emails_spam": 0,
        "emails_spam_rescued": 0,
        "emails_other": 0,
        "emails_undelivered": 0,
        "replies_sent": 0,
        "google_sent": 0,
        "google_inbox": 0,
        "google_spam": 0,
        "google_other": 0,
        "google_undelivered": 0,
        "google_replies": 0,
        "microsoft_sent": 0,
        "microsoft_inbox": 0,
        "microsoft_spam": 0,
        "microsoft_other": 0,
        "microsoft_undelivered": 0,
        "microsoft_replies": 0,
        "others_sent": 0,
        "others_inbox": 0,
        "others_spam": 0,
        "others_other": 0,
        "others_undelivered": 0,
        "others_replies": 0,
    }

    for em in emails:
        counts["emails_sent"] += 1
        esp = em.recipient_esp or "others"

        if em.status == EmailStatus.INBOX:
            counts["emails_inbox"] += 1
            counts[f"{esp}_inbox"] += 1
        elif em.status == EmailStatus.SPAM_RESCUED:
            counts["emails_spam_rescued"] += 1
        elif em.status == EmailStatus.SPAM:
            counts["emails_spam"] += 1
            counts[f"{esp}_spam"] += 1
        elif em.status == EmailStatus.OTHER:
            counts["emails_other"] += 1
            counts[f"{esp}_other"] += 1
        elif em.status == EmailStatus.UNDELIVERED:
            counts["emails_undelivered"] += 1
            counts[f"{esp}_undelivered"] += 1

        if em.replied_at:
            counts["replies_sent"] += 1
            counts[f"{esp}_replies"] += 1

        counts[f"{esp}_sent"] += 1

    score = _compute_deliverability_score(
        counts["emails_sent"],
        counts["emails_inbox"],
        counts["emails_spam_rescued"],
        counts["emails_spam"],
        counts["emails_other"],
        counts["emails_undelivered"],
    )
    counts["deliverability_score"] = score

    # Received replies
    received_q = await db.execute(
        select(func.count(WarmupEmail.id)).where(
            and_(
                WarmupEmail.recipient_account_id == account_id,
                func.date(WarmupEmail.replied_at) == target_date,
            )
        )
    )
    counts["replies_received"] = received_q.scalar() or 0

    # Upsert snapshot
    existing_q = await db.execute(
        select(AnalyticsSnapshot).where(
            and_(
                AnalyticsSnapshot.account_id == account_id,
                AnalyticsSnapshot.snapshot_date == target_date,
            )
        )
    )
    snapshot = existing_q.scalar_one_or_none()

    if snapshot is None:
        snapshot = AnalyticsSnapshot(account_id=account_id, snapshot_date=target_date)
        db.add(snapshot)

    for key, val in counts.items():
        setattr(snapshot, key, val)

    await db.flush()
    return snapshot


async def get_analytics_overview(db: AsyncSession, user_id: int) -> AnalyticsOverview:
    accounts_q = await db.execute(
        select(EmailAccount).where(EmailAccount.user_id == user_id)
    )
    accounts = accounts_q.scalars().all()

    active = sum(1 for a in accounts if a.status.value == "active")
    needs_recovery = sum(1 for a in accounts if a.status.value == "needs_recovery")
    total_sent = sum(a.total_sent for a in accounts)
    avg_score = (
        sum(a.deliverability_score for a in accounts) / len(accounts) if accounts else 0.0
    )

    return AnalyticsOverview(
        total_accounts=len(accounts),
        active_accounts=active,
        needs_recovery=needs_recovery,
        total_emails_sent=total_sent,
        avg_deliverability_score=round(avg_score, 1),
        accounts_summary=[
            {
                "id": a.id,
                "email": a.email,
                "status": a.status.value,
                "score": a.deliverability_score,
                "sent_today": a.emails_sent_today,
                "target_today": a.target_emails_today,
                "warming_enabled": a.warming_enabled,
            }
            for a in accounts
        ],
    )
