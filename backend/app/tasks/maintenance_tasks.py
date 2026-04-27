"""Maintenance tasks: analytics updates, counter resets, health checks."""
import asyncio
from datetime import datetime, timezone, date, timedelta
import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.maintenance_tasks.update_all_analytics")
def update_all_analytics():
    """Recompute analytics snapshots for all accounts for today."""
    return _run_async(_update_analytics_async())


async def _update_analytics_async():
    from app.core.database import AsyncSessionLocal
    from app.models.email_account import EmailAccount
    from app.services.analytics_service import update_daily_snapshot
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        accounts_q = await db.execute(select(EmailAccount.id))
        account_ids = [row[0] for row in accounts_q.fetchall()]
        today = date.today()
        yesterday = today - timedelta(days=1)

        for account_id in account_ids:
            for target_date in [yesterday, today]:
                try:
                    await update_daily_snapshot(db, account_id, target_date)
                except Exception as e:
                    logger.error("snapshot_update_failed", account_id=account_id, error=str(e))

        await db.commit()
        logger.info("analytics_updated", accounts=len(account_ids))
        return {"updated": len(account_ids)}


@celery_app.task(name="app.tasks.maintenance_tasks.reset_daily_counters")
def reset_daily_counters():
    """Reset per-account daily email counters and increment warmup day."""
    return _run_async(_reset_counters_async())


async def _reset_counters_async():
    from app.core.database import AsyncSessionLocal
    from app.models.email_account import EmailAccount, AccountStatus
    from sqlalchemy import select, update

    async with AsyncSessionLocal() as db:
        # Reset daily send counts
        await db.execute(
            update(EmailAccount).values(emails_sent_today=0)
        )
        # Increment warmup day for active warming accounts
        accounts_q = await db.execute(
            select(EmailAccount).where(
                EmailAccount.warming_enabled == True
            )
        )
        accounts = accounts_q.scalars().all()
        today = datetime.now(timezone.utc)

        for account in accounts:
            if account.status == AccountStatus.ACTIVE:
                account.current_warmup_day += 1

        await db.commit()
        logger.info("daily_counters_reset", accounts=len(accounts))
        return {"reset": len(accounts)}


@celery_app.task(name="app.tasks.maintenance_tasks.check_account_health")
def check_account_health():
    """Check connection health for all active accounts and update status."""
    return _run_async(_check_health_async())


async def _check_health_async():
    from app.core.database import AsyncSessionLocal
    from app.models.email_account import EmailAccount, AccountStatus
    from app.services.email_service import test_smtp_connection, test_imap_connection
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        accounts_q = await db.execute(
            select(EmailAccount).where(EmailAccount.warming_enabled == True)
        )
        accounts = accounts_q.scalars().all()
        checked = 0
        errors = 0

        for account in accounts:
            smtp_ok, smtp_err = await test_smtp_connection(account)
            imap_ok, imap_err = await test_imap_connection(account)

            account.last_checked_at = datetime.now(timezone.utc)

            if smtp_ok and imap_ok:
                account.last_connection_error = None
                if account.status == AccountStatus.ERROR:
                    account.status = AccountStatus.ACTIVE
            else:
                err = smtp_err or imap_err
                account.last_connection_error = err
                if account.status == AccountStatus.ACTIVE:
                    account.status = AccountStatus.ERROR

            checked += 1
            if not (smtp_ok and imap_ok):
                errors += 1

        await db.commit()
        logger.info("health_check_complete", checked=checked, errors=errors)
        return {"checked": checked, "errors": errors}
