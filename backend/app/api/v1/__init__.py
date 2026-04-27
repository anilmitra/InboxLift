from fastapi import APIRouter
from app.api.v1 import auth, accounts, analytics, admin, users

router = APIRouter()
router.include_router(auth.router)
router.include_router(accounts.router)
router.include_router(analytics.router)
router.include_router(admin.router)
router.include_router(users.router)
