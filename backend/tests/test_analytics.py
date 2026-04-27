"""Tests for analytics service and endpoints."""
import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsSnapshot
from app.models.email_account import EmailAccount
from app.services.analytics_service import (
    build_account_report,
    get_analytics_overview,
    update_daily_snapshot,
    _compute_deliverability_score,
)


class TestDeliverabilityScore:
    def test_zero_sent(self):
        assert _compute_deliverability_score(0, 0, 0, 0, 0, 0) == 0.0

    def test_all_inbox(self):
        assert _compute_deliverability_score(10, 10, 0, 0, 0, 0) == 100.0

    def test_all_spam(self):
        assert _compute_deliverability_score(10, 0, 0, 10, 0, 0) == 0.0

    def test_all_spam_rescued(self):
        assert _compute_deliverability_score(10, 0, 10, 0, 0, 0) == 70.0

    def test_mixed(self):
        # 5 inbox (100), 3 rescued (70), 2 other (50) out of 10
        score = _compute_deliverability_score(10, 5, 3, 0, 2, 0)
        assert score == (5 * 100 + 3 * 70 + 2 * 50) / 10

    def test_all_undelivered(self):
        assert _compute_deliverability_score(10, 0, 0, 0, 0, 10) == 0.0


@pytest.mark.asyncio
async def test_build_account_report_empty(db: AsyncSession, test_account: EmailAccount):
    report = await build_account_report(db, test_account, days=7)
    assert report.account_id == test_account.id
    assert report.total_sent == 0
    assert report.deliverability_score == 0.0
    assert len(report.daily_stats) == 7
    assert len(report.esp_stats) == 3


@pytest.mark.asyncio
async def test_build_account_report_with_data(db: AsyncSession, test_account: EmailAccount):
    today = date.today()
    snapshot = AnalyticsSnapshot(
        account_id=test_account.id,
        snapshot_date=today,
        emails_sent=10,
        emails_inbox=7,
        emails_spam_rescued=2,
        emails_spam=1,
        google_sent=5,
        google_inbox=4,
        microsoft_sent=5,
        microsoft_inbox=3,
    )
    db.add(snapshot)
    await db.flush()

    report = await build_account_report(db, test_account, days=7)
    assert report.total_sent == 10
    assert report.placement.inbox == 7
    assert report.placement.spam_rescued == 2
    assert report.deliverability_score > 0


@pytest.mark.asyncio
async def test_overview_empty(db: AsyncSession, test_user):
    overview = await get_analytics_overview(db, test_user.id)
    assert overview.total_accounts == 0
    assert overview.active_accounts == 0
    assert overview.avg_deliverability_score == 0.0


@pytest.mark.asyncio
async def test_overview_with_accounts(db: AsyncSession, test_user, test_account):
    overview = await get_analytics_overview(db, test_user.id)
    assert overview.total_accounts == 1
    assert len(overview.accounts_summary) == 1


@pytest.mark.asyncio
async def test_analytics_overview_endpoint(client: AsyncClient, auth_headers, test_account):
    resp = await client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_accounts" in data
    assert "avg_deliverability_score" in data


@pytest.mark.asyncio
async def test_account_report_endpoint(client: AsyncClient, auth_headers, test_account):
    resp = await client.get(
        f"/api/v1/analytics/accounts/{test_account.id}/report?days=7",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["account_id"] == test_account.id
    assert data["period_days"] == 7
    assert "daily_stats" in data
    assert "esp_stats" in data
    assert "placement" in data


@pytest.mark.asyncio
async def test_account_report_wrong_user(client: AsyncClient, auth_headers, test_account, db):
    from app.core.security import hash_password
    from app.models.user import User

    other_user = User(
        email="other@example.com",
        full_name="Other",
        hashed_password=hash_password("password123"),
    )
    db.add(other_user)
    await db.flush()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = await client.get(
        f"/api/v1/analytics/accounts/{test_account.id}/report",
        headers=other_headers,
    )
    assert resp.status_code == 404
