"""Core email warming Celery tasks."""
import asyncio
import random
from datetime import datetime, timezone, date
from typing import Optional
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    """Run async coroutine in sync Celery task context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.tasks.warmup_tasks.run_warmup_cycle", max_retries=3)
def run_warmup_cycle(self):
    """Main warming cycle: select account pairs and send warm-up emails."""
    return _run_async(_run_warmup_cycle_async())


async def _run_warmup_cycle_async():
    from app.core.database import AsyncSessionLocal
    from app.models.email_account import EmailAccount, AccountStatus
    from app.services.ai_service import generate_warmup_email, generate_reply
    from app.services.email_service import send_warmup_email, send_reply
    from app.services.analytics_service import update_daily_snapshot
    from app.models.warmup_email import WarmupEmail, EmailStatus
    from app.models.ai_settings import AISettings, AIProvider
    from sqlalchemy import select, and_

    async with AsyncSessionLocal() as db:
        # Get all active warming accounts
        result = await db.execute(
            select(EmailAccount).where(
                and_(
                    EmailAccount.warming_enabled == True,
                    EmailAccount.status == AccountStatus.ACTIVE,
                )
            )
        )
        accounts = result.scalars().all()

        if len(accounts) < 2:
            logger.info("warmup_cycle_skipped", reason="not_enough_accounts", count=len(accounts))
            return {"skipped": True, "reason": "need_at_least_2_accounts"}

        # Get global AI settings
        ai_q = await db.execute(select(AISettings).where(AISettings.user_id == None))
        ai_settings = ai_q.scalar_one_or_none()
        ai_provider = ai_settings.provider if ai_settings else AIProvider.OPENAI
        ai_model = ai_settings.model if ai_settings else "gpt-4o-mini"
        ai_key = ai_settings.api_key_encrypted if ai_settings else None

        sent_count = 0
        now = datetime.now(timezone.utc)

        for sender in accounts:
            # Check if we've hit today's target
            target = sender.target_emails_today
            if sender.emails_sent_today >= target:
                continue

            # Pick a random recipient (not the same account)
            pool = [a for a in accounts if a.id != sender.id and a.user_id != sender.user_id or a.id != sender.id]
            if not pool:
                continue

            # Prefer cross-user accounts for more realistic warming
            cross_user = [a for a in pool if a.user_id != sender.user_id]
            recipient = random.choice(cross_user if cross_user else pool)

            remaining = target - sender.emails_sent_today
            batch = min(remaining, random.randint(1, 3))

            for _ in range(batch):
                subject, body = await generate_warmup_email(
                    provider=ai_provider,
                    model=ai_model,
                    encrypted_key=ai_key,
                )

                success, message_id, error = await send_warmup_email(
                    sender=sender,
                    recipient_email=recipient.email,
                    subject=subject,
                    body=body,
                )

                if success and message_id:
                    from app.services.email_service import _detect_esp as detect_esp
                    warmup_email = WarmupEmail(
                        sender_account_id=sender.id,
                        recipient_account_id=recipient.id,
                        message_id=message_id,
                        subject=subject,
                        body=body,
                        sender_esp=detect_esp(sender.email),
                        recipient_esp=detect_esp(recipient.email),
                        status=EmailStatus.SENT,
                        sent_at=now,
                        ai_provider=str(ai_provider.value),
                        ai_model=ai_model,
                    )
                    db.add(warmup_email)
                    sender.emails_sent_today += 1
                    sender.total_sent += 1
                    sender.last_warmup_at = now
                    sent_count += 1

        await db.commit()

        logger.info("warmup_cycle_complete", emails_sent=sent_count)
        return {"emails_sent": sent_count}


@celery_app.task(bind=True, name="app.tasks.warmup_tasks.check_email_delivery", max_retries=3)
def check_email_delivery(self):
    """Check delivery status of sent warmup emails and handle spam rescue + replies."""
    return _run_async(_check_email_delivery_async())


async def _check_email_delivery_async():
    from app.core.database import AsyncSessionLocal
    from app.models.warmup_email import WarmupEmail, EmailStatus
    from app.models.email_account import EmailAccount
    from app.services.email_service import check_inbox_for_warmup, send_reply as send_reply_fn
    from app.services.ai_service import generate_reply, AIProvider
    from app.models.ai_settings import AISettings
    from app.core.config import settings as app_settings
    from sqlalchemy import select, and_

    async with AsyncSessionLocal() as db:
        # Check emails sent in the last 48 hours that aren't yet confirmed
        cutoff = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

        emails_q = await db.execute(
            select(WarmupEmail).where(
                and_(
                    WarmupEmail.status == EmailStatus.SENT,
                    WarmupEmail.sent_at >= cutoff,
                )
            ).limit(200)
        )
        pending_emails = emails_q.scalars().all()

        # Load recipient accounts
        account_ids = list(set(e.recipient_account_id for e in pending_emails))
        accounts_q = await db.execute(
            select(EmailAccount).where(EmailAccount.id.in_(account_ids))
        )
        accounts = {a.id: a for a in accounts_q.scalars().all()}

        # AI settings for replies
        ai_q = await db.execute(select(AISettings).where(AISettings.user_id == None))
        ai_settings = ai_q.scalar_one_or_none()
        ai_provider = ai_settings.provider if ai_settings else AIProvider.OPENAI
        ai_model = ai_settings.model if ai_settings else "gpt-4o-mini"
        ai_key = ai_settings.api_key_encrypted if ai_settings else None

        checked = 0
        replied = 0
        now = datetime.now(timezone.utc)

        for warmup_email in pending_emails:
            recipient = accounts.get(warmup_email.recipient_account_id)
            if not recipient:
                continue

            placement = await check_inbox_for_warmup(
                account=recipient,
                sender_email=warmup_email.sender_account_id and "",
                message_id=warmup_email.message_id or "",
            )

            if placement == "inbox":
                warmup_email.status = EmailStatus.INBOX
                warmup_email.delivered_at = now
                warmup_email.read_at = now
                recipient.total_inbox += 1
            elif placement == "spam_rescued":
                warmup_email.status = EmailStatus.SPAM_RESCUED
                warmup_email.spam_detected_at = now
                warmup_email.spam_rescued_at = now
                recipient.total_spam_rescued += 1
            elif placement == "spam":
                warmup_email.status = EmailStatus.SPAM
                warmup_email.spam_detected_at = now

            checked += 1

            # Send reply based on configured reply rate
            should_reply = (
                placement in ("inbox", "spam_rescued")
                and warmup_email.replied_at is None
                and random.random() < app_settings.WARMUP_REPLY_RATE
            )

            if should_reply:
                # Load sender account for replying
                sender_q = await db.execute(
                    select(EmailAccount).where(EmailAccount.id == warmup_email.sender_account_id)
                )
                sender = sender_q.scalar_one_or_none()
                if sender and sender.warming_enabled:
                    reply_body = await generate_reply(
                        original_subject=warmup_email.subject,
                        original_body=warmup_email.body,
                        provider=ai_provider,
                        model=ai_model,
                        encrypted_key=ai_key,
                    )
                    success, reply_id, _ = await send_reply_fn(
                        account=recipient,
                        original_sender_email=sender.email,
                        original_subject=warmup_email.subject,
                        original_message_id=warmup_email.message_id or "",
                        reply_body=reply_body,
                    )
                    if success:
                        warmup_email.reply_message_id = reply_id
                        warmup_email.reply_body = reply_body
                        warmup_email.replied_at = now
                        replied += 1

        await db.commit()
        logger.info("delivery_check_complete", checked=checked, replied=replied)
        return {"checked": checked, "replied": replied}


@celery_app.task(name="app.tasks.warmup_tasks.send_single_warmup_email")
def send_single_warmup_email(account_id: int):
    """Trigger an immediate warmup email for a specific account."""
    return _run_async(_send_single_async(account_id))


async def _send_single_async(account_id: int):
    from app.core.database import AsyncSessionLocal
    from app.models.email_account import EmailAccount, AccountStatus
    from app.services.ai_service import generate_warmup_email, AIProvider
    from app.services.email_service import send_warmup_email
    from app.models.warmup_email import WarmupEmail, EmailStatus
    from app.models.ai_settings import AISettings
    from sqlalchemy import select, and_
    import random

    async with AsyncSessionLocal() as db:
        account_q = await db.execute(select(EmailAccount).where(EmailAccount.id == account_id))
        account = account_q.scalar_one_or_none()
        if not account or not account.warming_enabled:
            return {"error": "account not found or not warming"}

        # Get pool
        pool_q = await db.execute(
            select(EmailAccount).where(
                and_(
                    EmailAccount.id != account_id,
                    EmailAccount.warming_enabled == True,
                    EmailAccount.status == AccountStatus.ACTIVE,
                )
            )
        )
        pool = pool_q.scalars().all()
        if not pool:
            return {"error": "no recipients in pool"}

        recipient = random.choice(pool)
        ai_q = await db.execute(select(AISettings).where(AISettings.user_id == None))
        ai_settings = ai_q.scalar_one_or_none()

        subject, body = await generate_warmup_email(
            provider=ai_settings.provider if ai_settings else AIProvider.OPENAI,
            model=ai_settings.model if ai_settings else "gpt-4o-mini",
            encrypted_key=ai_settings.api_key_encrypted if ai_settings else None,
        )

        success, message_id, error = await send_warmup_email(account, recipient.email, subject, body)
        if success:
            from app.services.email_service import _detect_esp as detect_esp
            now = datetime.now(timezone.utc)
            we = WarmupEmail(
                sender_account_id=account.id,
                recipient_account_id=recipient.id,
                message_id=message_id,
                subject=subject,
                body=body,
                sender_esp=detect_esp(account.email),
                recipient_esp=detect_esp(recipient.email),
                status=EmailStatus.SENT,
                sent_at=now,
            )
            db.add(we)
            account.emails_sent_today += 1
            account.total_sent += 1
            account.last_warmup_at = now
            await db.commit()
            return {"sent": True, "message_id": message_id}

        return {"sent": False, "error": error}
