"""Tests for email account management endpoints."""
import pytest
from httpx import AsyncClient


ACCOUNT_PAYLOAD = {
    "email": "myaccount@gmail.com",
    "display_name": "My Gmail",
    "provider": "gmail",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_use_tls": True,
    "imap_host": "imap.gmail.com",
    "imap_port": 993,
    "imap_use_ssl": True,
    "username": "myaccount@gmail.com",
    "password": "app-password-here",
    "daily_warmup_limit": 40,
    "ramp_up_days": 30,
}


@pytest.mark.asyncio
async def test_list_accounts_empty(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/accounts", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient, auth_headers):
    resp = await client.post("/api/v1/accounts", json=ACCOUNT_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "myaccount@gmail.com"
    assert data["display_name"] == "My Gmail"
    assert data["provider"] == "gmail"
    assert data["warming_enabled"] is False
    assert data["status"] == "inactive"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_account_duplicate(client: AsyncClient, auth_headers):
    await client.post("/api/v1/accounts", json=ACCOUNT_PAYLOAD, headers=auth_headers)
    resp = await client.post("/api/v1/accounts", json=ACCOUNT_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_account(client: AsyncClient, auth_headers, test_account):
    resp = await client.get(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "warmup@example.com"


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/accounts/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_account(client: AsyncClient, auth_headers, test_account):
    resp = await client.put(
        f"/api/v1/accounts/{test_account.id}",
        json={"display_name": "Updated Name", "daily_warmup_limit": 60},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Updated Name"
    assert data["daily_warmup_limit"] == 60


@pytest.mark.asyncio
async def test_delete_account(client: AsyncClient, auth_headers, test_account):
    resp = await client.delete(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_enable_warmup(client: AsyncClient, auth_headers, test_account):
    resp = await client.post(
        f"/api/v1/accounts/{test_account.id}/enable-warmup",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["warming_enabled"] is True
    assert data["status"] == "active"
    assert data["warmup_start_date"] is not None


@pytest.mark.asyncio
async def test_enable_warmup_twice(client: AsyncClient, auth_headers, test_account):
    await client.post(f"/api/v1/accounts/{test_account.id}/enable-warmup", headers=auth_headers)
    resp = await client.post(f"/api/v1/accounts/{test_account.id}/enable-warmup", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_pause_warmup(client: AsyncClient, auth_headers, test_account):
    # Enable first
    await client.post(f"/api/v1/accounts/{test_account.id}/enable-warmup", headers=auth_headers)
    # Then pause
    resp = await client.post(
        f"/api/v1/accounts/{test_account.id}/pause-warmup",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["warming_enabled"] is False
    assert data["status"] == "paused"


@pytest.mark.asyncio
async def test_list_accounts_shows_created(client: AsyncClient, auth_headers):
    await client.post("/api/v1/accounts", json=ACCOUNT_PAYLOAD, headers=auth_headers)
    resp = await client.get("/api/v1/accounts", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_account_isolation_between_users(client: AsyncClient, test_account, db):
    """User B should not see User A's accounts."""
    from app.core.security import hash_password
    from app.models.user import User

    user_b = User(
        email="userb@example.com",
        full_name="User B",
        hashed_password=hash_password("passwordB123"),
    )
    db.add(user_b)
    await db.flush()

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.com", "password": "passwordB123"},
    )
    headers_b = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.get("/api/v1/accounts", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json() == []

    resp = await client.get(f"/api/v1/accounts/{test_account.id}", headers=headers_b)
    assert resp.status_code == 404
