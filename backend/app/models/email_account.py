from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.core.database import Base


class EmailProvider(str, enum.Enum):
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    CUSTOM = "custom"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    NEEDS_RECOVERY = "needs_recovery"
    INACTIVE = "inactive"
    CONNECTING = "connecting"
    ERROR = "error"


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=True)
    provider: Mapped[EmailProvider] = mapped_column(
        Enum(EmailProvider, native_enum=False, length=50), default=EmailProvider.CUSTOM
    )

    # SMTP settings
    smtp_host: Mapped[str] = mapped_column(String(255), nullable=False)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)

    # IMAP settings
    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_use_ssl: Mapped[bool] = mapped_column(Boolean, default=True)

    # Credentials (encrypted)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # Warming config
    warming_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, native_enum=False, length=50), default=AccountStatus.INACTIVE
    )
    daily_warmup_limit: Mapped[int] = mapped_column(Integer, default=50)
    ramp_up_days: Mapped[int] = mapped_column(Integer, default=30)
    current_warmup_day: Mapped[int] = mapped_column(Integer, default=0)
    emails_sent_today: Mapped[int] = mapped_column(Integer, default=0)
    warmup_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_warmup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Stats
    deliverability_score: Mapped[float] = mapped_column(Float, default=0.0)
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_inbox: Mapped[int] = mapped_column(Integer, default=0)
    total_spam_rescued: Mapped[int] = mapped_column(Integer, default=0)

    # Connection health
    last_connection_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    connection_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="email_accounts")  # noqa: F821
    sent_warmup_emails: Mapped[list["WarmupEmail"]] = relationship(  # noqa: F821
        "WarmupEmail", foreign_keys="WarmupEmail.sender_account_id", back_populates="sender_account"
    )
    received_warmup_emails: Mapped[list["WarmupEmail"]] = relationship(  # noqa: F821
        "WarmupEmail",
        foreign_keys="WarmupEmail.recipient_account_id",
        back_populates="recipient_account",
    )
    analytics_snapshots: Mapped[list["AnalyticsSnapshot"]] = relationship(  # noqa: F821
        "AnalyticsSnapshot", back_populates="account", cascade="all, delete-orphan"
    )

    @property
    def target_emails_today(self) -> int:
        """Calculate target emails for today based on ramp-up schedule."""
        if not self.warming_enabled or self.current_warmup_day == 0:
            return 2
        from app.core.config import settings
        start = settings.WARMUP_START_EMAILS_PER_DAY
        maximum = min(self.daily_warmup_limit, settings.WARMUP_MAX_EMAILS_PER_DAY)
        # Linear ramp-up
        increment = (maximum - start) / max(self.ramp_up_days, 1)
        target = int(start + increment * min(self.current_warmup_day, self.ramp_up_days))
        return min(target, maximum)
