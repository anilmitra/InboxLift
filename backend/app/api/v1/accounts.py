from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import time

from app.core.database import get_db
from app.core.security import encrypt_secret
from app.api.deps import get_current_user
from app.models.user import User
from app.models.email_account import EmailAccount, AccountStatus
from app.schemas.email_account import (
    EmailAccountCreate,
    EmailAccountUpdate,
    EmailAccountOut,
    ConnectionTestResult,
)
from app.services.email_service import test_smtp_connection, test_imap_connection

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _get_default_hosts(provider: str) -> dict:
    if provider == "gmail":
        return {"smtp_host": "smtp.gmail.com", "smtp_port": 587, "imap_host": "imap.gmail.com", "imap_port": 993}
    if provider == "outlook":
        return {"smtp_host": "smtp.office365.com", "smtp_port": 587, "imap_host": "outlook.office365.com", "imap_port": 993}
    return {}


@router.get("", response_model=list[EmailAccountOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EmailAccount)
        .where(EmailAccount.user_id == current_user.id)
        .order_by(EmailAccount.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=EmailAccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: EmailAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for duplicate
    existing = await db.execute(
        select(EmailAccount).where(
            EmailAccount.user_id == current_user.id,
            EmailAccount.email == str(payload.email),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email account already added")

    account = EmailAccount(
        user_id=current_user.id,
        email=str(payload.email),
        display_name=payload.display_name,
        provider=payload.provider,
        smtp_host=payload.smtp_host,
        smtp_port=payload.smtp_port,
        smtp_use_tls=payload.smtp_use_tls,
        imap_host=payload.imap_host,
        imap_port=payload.imap_port,
        imap_use_ssl=payload.imap_use_ssl,
        username=payload.username,
        password_encrypted=encrypt_secret(payload.password),
        daily_warmup_limit=payload.daily_warmup_limit,
        ramp_up_days=payload.ramp_up_days,
        status=AccountStatus.INACTIVE,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=EmailAccountOut)
async def get_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)
    return account


@router.put("/{account_id}", response_model=EmailAccountOut)
async def update_account(
    account_id: int,
    payload: EmailAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        account.password_encrypted = encrypt_secret(update_data.pop("password"))
    for key, value in update_data.items():
        setattr(account, key, value)

    await db.flush()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)
    await db.delete(account)


@router.post("/{account_id}/test-connection", response_model=ConnectionTestResult)
async def test_connection(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)
    start = time.monotonic()

    smtp_ok, smtp_err = await test_smtp_connection(account)
    imap_ok, imap_err = await test_imap_connection(account)

    latency = (time.monotonic() - start) * 1000
    success = smtp_ok and imap_ok
    error = smtp_err or imap_err

    account.connection_tested_at = datetime.now(timezone.utc)
    account.last_connection_error = error
    await db.flush()

    return ConnectionTestResult(
        success=success,
        smtp_ok=smtp_ok,
        imap_ok=imap_ok,
        error=error,
        latency_ms=round(latency, 1),
    )


@router.post("/{account_id}/enable-warmup", response_model=EmailAccountOut)
async def enable_warmup(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)

    if account.warming_enabled:
        raise HTTPException(status_code=400, detail="Warming is already enabled")

    account.warming_enabled = True
    account.status = AccountStatus.ACTIVE
    account.warmup_start_date = datetime.now(timezone.utc)
    account.current_warmup_day = 1

    await db.flush()
    await db.refresh(account)
    return account


@router.post("/{account_id}/pause-warmup", response_model=EmailAccountOut)
async def pause_warmup(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)
    account.warming_enabled = False
    account.status = AccountStatus.PAUSED
    await db.flush()
    await db.refresh(account)
    return account


@router.post("/{account_id}/resume-warmup", response_model=EmailAccountOut)
async def resume_warmup(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = await _get_user_account(db, current_user.id, account_id)
    account.warming_enabled = True
    account.status = AccountStatus.ACTIVE
    await db.flush()
    await db.refresh(account)
    return account


async def _get_user_account(db: AsyncSession, user_id: int, account_id: int) -> EmailAccount:
    result = await db.execute(
        select(EmailAccount).where(
            EmailAccount.id == account_id,
            EmailAccount.user_id == user_id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
