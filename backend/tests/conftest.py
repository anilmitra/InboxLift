"""Test configuration and fixtures."""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.email_account import EmailAccount, EmailProvider, AccountStatus

# Use StaticPool so all connections share the same in-memory SQLite DB
TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = TestSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db):
    async def override_get_db():
        yield db
        await db.flush()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession) -> User:
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("adminpassword123"),
        is_active=True,
        is_admin=True,
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_headers(client, test_user) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client, test_admin) -> dict:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpassword123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_account(db: AsyncSession, test_user: User) -> EmailAccount:
    from app.core.security import encrypt_secret
    account = EmailAccount(
        user_id=test_user.id,
        email="warmup@example.com",
        display_name="Warmup Account",
        provider=EmailProvider.CUSTOM,
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_use_tls=True,
        imap_host="imap.example.com",
        imap_port=993,
        imap_use_ssl=True,
        username="warmup@example.com",
        password_encrypted=encrypt_secret("testpass"),
        warming_enabled=False,
        status=AccountStatus.INACTIVE,
        daily_warmup_limit=50,
        ramp_up_days=30,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account
