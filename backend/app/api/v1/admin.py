from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.core.security import encrypt_secret, decrypt_secret
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.ai_settings import AISettings, AIProvider
from app.models.email_account import EmailAccount
from app.schemas.ai_settings import AISettingsOut, AISettingsUpdate, AvailableModel
from app.schemas.user import UserOut
from app.services.ai_service import AVAILABLE_MODELS

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ai-settings", response_model=AISettingsOut)
async def get_ai_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AI settings - user-specific first, then global."""
    # Try user-specific settings
    result = await db.execute(
        select(AISettings).where(AISettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Fall back to global settings
        result = await db.execute(
            select(AISettings).where(AISettings.user_id == None)
        )
        settings = result.scalar_one_or_none()

    if not settings:
        # Return defaults
        return AISettingsOut(
            id=0,
            user_id=None,
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
            temperature=0.8,
            max_tokens=500,
            is_active=True,
            has_api_key=False,
            updated_at=__import__("datetime").datetime.utcnow(),
        )

    return AISettingsOut(
        id=settings.id,
        user_id=settings.user_id,
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_active=settings.is_active,
        has_api_key=bool(settings.api_key_encrypted),
        updated_at=settings.updated_at,
    )


@router.put("/ai-settings", response_model=AISettingsOut)
async def update_ai_settings(
    payload: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update AI settings for current user."""
    result = await db.execute(
        select(AISettings).where(AISettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AISettings(user_id=current_user.id)
        db.add(settings)

    if payload.provider is not None:
        settings.provider = payload.provider
    if payload.model is not None:
        settings.model = payload.model
    if payload.api_key is not None:
        settings.api_key_encrypted = encrypt_secret(payload.api_key) if payload.api_key else None
    if payload.temperature is not None:
        settings.temperature = payload.temperature
    if payload.max_tokens is not None:
        settings.max_tokens = payload.max_tokens

    await db.flush()
    await db.refresh(settings)

    return AISettingsOut(
        id=settings.id,
        user_id=settings.user_id,
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_active=settings.is_active,
        has_api_key=bool(settings.api_key_encrypted),
        updated_at=settings.updated_at,
    )


@router.get("/ai-settings/models", response_model=List[AvailableModel])
async def get_available_models(
    current_user: User = Depends(get_current_user),
):
    """List all available AI models."""
    models = []
    for provider, model_list in AVAILABLE_MODELS.items():
        for m in model_list:
            models.append(
                AvailableModel(
                    id=m["id"],
                    name=m["name"],
                    provider=provider,
                    context_length=m["context_length"],
                    description=m["description"],
                )
            )
    return models


@router.get("/global-ai-settings", response_model=AISettingsOut)
async def get_global_ai_settings(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin: get global AI settings."""
    result = await db.execute(select(AISettings).where(AISettings.user_id == None))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="No global AI settings configured")
    return AISettingsOut(
        id=settings.id,
        user_id=None,
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_active=settings.is_active,
        has_api_key=bool(settings.api_key_encrypted),
        updated_at=settings.updated_at,
    )


@router.put("/global-ai-settings", response_model=AISettingsOut)
async def update_global_ai_settings(
    payload: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin: update global AI settings."""
    result = await db.execute(select(AISettings).where(AISettings.user_id == None))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = AISettings(user_id=None)
        db.add(settings)

    if payload.provider is not None:
        settings.provider = payload.provider
    if payload.model is not None:
        settings.model = payload.model
    if payload.api_key is not None:
        settings.api_key_encrypted = encrypt_secret(payload.api_key) if payload.api_key else None
    if payload.temperature is not None:
        settings.temperature = payload.temperature
    if payload.max_tokens is not None:
        settings.max_tokens = payload.max_tokens

    await db.flush()
    await db.refresh(settings)

    return AISettingsOut(
        id=settings.id,
        user_id=None,
        provider=settings.provider,
        model=settings.model,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        is_active=settings.is_active,
        has_api_key=bool(settings.api_key_encrypted),
        updated_at=settings.updated_at,
    )


@router.get("/users", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    total_users = await db.execute(select(func.count(User.id)))
    total_accounts = await db.execute(select(func.count(EmailAccount.id)))
    active_accounts = await db.execute(
        select(func.count(EmailAccount.id)).where(EmailAccount.warming_enabled == True)
    )
    return {
        "total_users": total_users.scalar(),
        "total_accounts": total_accounts.scalar(),
        "active_accounts": active_accounts.scalar(),
    }
