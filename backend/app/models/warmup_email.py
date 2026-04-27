from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.core.database import Base


class EmailStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    INBOX = "inbox"
    SPAM = "spam"
    SPAM_RESCUED = "spam_rescued"
    OTHER = "other"
    UNDELIVERED = "undelivered"
    REPLIED = "replied"


class WarmupEmail(Base):
    __tablename__ = "warmup_emails"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sender_account_id: Mapped[int] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), index=True
    )
    recipient_account_id: Mapped[int] = mapped_column(
        ForeignKey("email_accounts.id", ondelete="CASCADE"), index=True
    )

    # Message identifiers
    message_id: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    reply_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thread_id: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Content
    subject: Mapped[str] = mapped_column(String(998), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    reply_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ESP/routing info
    sender_esp: Mapped[str | None] = mapped_column(String(50), nullable=True)  # google/microsoft/other
    recipient_esp: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status tracking
    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus, native_enum=False, length=50), default=EmailStatus.QUEUED
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    spam_detected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    spam_rescued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI generation metadata
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    sender_account: Mapped["EmailAccount"] = relationship(  # noqa: F821
        "EmailAccount", foreign_keys=[sender_account_id], back_populates="sent_warmup_emails"
    )
    recipient_account: Mapped["EmailAccount"] = relationship(  # noqa: F821
        "EmailAccount", foreign_keys=[recipient_account_id], back_populates="received_warmup_emails"
    )
