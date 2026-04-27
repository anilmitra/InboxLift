from sqlalchemy import Date, Integer, Float, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from app.core.database import Base


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("account_id", "snapshot_date", name="uq_analytics_account_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Volume metrics
    emails_sent: Mapped[int] = mapped_column(Integer, default=0)
    emails_inbox: Mapped[int] = mapped_column(Integer, default=0)
    emails_spam: Mapped[int] = mapped_column(Integer, default=0)
    emails_spam_rescued: Mapped[int] = mapped_column(Integer, default=0)
    emails_other: Mapped[int] = mapped_column(Integer, default=0)
    emails_undelivered: Mapped[int] = mapped_column(Integer, default=0)
    replies_sent: Mapped[int] = mapped_column(Integer, default=0)
    replies_received: Mapped[int] = mapped_column(Integer, default=0)

    # ESP breakdown - Google
    google_sent: Mapped[int] = mapped_column(Integer, default=0)
    google_inbox: Mapped[int] = mapped_column(Integer, default=0)
    google_spam: Mapped[int] = mapped_column(Integer, default=0)
    google_other: Mapped[int] = mapped_column(Integer, default=0)
    google_undelivered: Mapped[int] = mapped_column(Integer, default=0)
    google_replies: Mapped[int] = mapped_column(Integer, default=0)

    # ESP breakdown - Microsoft
    microsoft_sent: Mapped[int] = mapped_column(Integer, default=0)
    microsoft_inbox: Mapped[int] = mapped_column(Integer, default=0)
    microsoft_spam: Mapped[int] = mapped_column(Integer, default=0)
    microsoft_other: Mapped[int] = mapped_column(Integer, default=0)
    microsoft_undelivered: Mapped[int] = mapped_column(Integer, default=0)
    microsoft_replies: Mapped[int] = mapped_column(Integer, default=0)

    # ESP breakdown - Others
    others_sent: Mapped[int] = mapped_column(Integer, default=0)
    others_inbox: Mapped[int] = mapped_column(Integer, default=0)
    others_spam: Mapped[int] = mapped_column(Integer, default=0)
    others_other: Mapped[int] = mapped_column(Integer, default=0)
    others_undelivered: Mapped[int] = mapped_column(Integer, default=0)
    others_replies: Mapped[int] = mapped_column(Integer, default=0)

    # Scores
    deliverability_score: Mapped[float] = mapped_column(Float, default=0.0)
    google_score: Mapped[float] = mapped_column(Float, default=0.0)
    microsoft_score: Mapped[float] = mapped_column(Float, default=0.0)
    others_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    account: Mapped["EmailAccount"] = relationship(  # noqa: F821
        "EmailAccount", back_populates="analytics_snapshots"
    )
