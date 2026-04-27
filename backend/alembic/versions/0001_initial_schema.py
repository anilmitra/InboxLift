"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("uq_users_email", "users", ["email"], unique=True)

    op.create_table(
        "email_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="custom"),
        sa.Column("smtp_host", sa.String(255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False, server_default="587"),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("imap_host", sa.String(255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"),
        sa.Column("imap_use_ssl", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("username", sa.String(255), nullable=False),
        sa.Column("password_encrypted", sa.Text(), nullable=False),
        sa.Column("warming_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(50), nullable=False, server_default="inactive"),
        sa.Column("daily_warmup_limit", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("ramp_up_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("current_warmup_day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_sent_today", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warmup_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_warmup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deliverability_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_inbox", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spam_rescued", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_connection_error", sa.Text(), nullable=True),
        sa.Column("connection_tested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_email_accounts_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_email_accounts"),
    )
    op.create_index("ix_email_accounts_id", "email_accounts", ["id"])
    op.create_index("ix_email_accounts_user_id", "email_accounts", ["user_id"])
    op.create_index("ix_email_accounts_email", "email_accounts", ["email"])

    op.create_table(
        "warmup_emails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sender_account_id", sa.Integer(), nullable=False),
        sa.Column("recipient_account_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(500), nullable=True),
        sa.Column("reply_message_id", sa.String(500), nullable=True),
        sa.Column("thread_id", sa.String(500), nullable=True),
        sa.Column("subject", sa.String(998), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("reply_body", sa.Text(), nullable=True),
        sa.Column("sender_esp", sa.String(50), nullable=True),
        sa.Column("recipient_esp", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("spam_detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("spam_rescued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sender_account_id"], ["email_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipient_account_id"], ["email_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_warmup_emails"),
    )
    op.create_index("ix_warmup_emails_id", "warmup_emails", ["id"])
    op.create_index("ix_warmup_emails_sender_account_id", "warmup_emails", ["sender_account_id"])
    op.create_index("ix_warmup_emails_recipient_account_id", "warmup_emails", ["recipient_account_id"])
    op.create_index("ix_warmup_emails_message_id", "warmup_emails", ["message_id"])

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("emails_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_inbox", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_spam", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_spam_rescued", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_other", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_undelivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("replies_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_inbox", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_spam", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_other", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_undelivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_inbox", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_spam", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_other", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_undelivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("microsoft_replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_inbox", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_spam", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_other", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_undelivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("others_replies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deliverability_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("google_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("microsoft_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("others_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["email_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_analytics_snapshots"),
        sa.UniqueConstraint("account_id", "snapshot_date", name="uq_analytics_account_date"),
    )
    op.create_index("ix_analytics_snapshots_id", "analytics_snapshots", ["id"])
    op.create_index("ix_analytics_snapshots_account_id", "analytics_snapshots", ["account_id"])
    op.create_index("ix_analytics_snapshots_snapshot_date", "analytics_snapshots", ["snapshot_date"])

    op.create_table(
        "ai_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="openai"),
        sa.Column("model", sa.String(100), nullable=False, server_default="gpt-4o-mini"),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_ai_settings"),
    )
    op.create_index("ix_ai_settings_id", "ai_settings", ["id"])
    op.create_index("ix_ai_settings_user_id", "ai_settings", ["user_id"])


def downgrade() -> None:
    op.drop_table("ai_settings")
    op.drop_table("analytics_snapshots")
    op.drop_table("warmup_emails")
    op.drop_table("email_accounts")
    op.drop_table("users")
