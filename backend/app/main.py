"""
Main FastAPI application with security features.
"""
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.security import rate_limit_middleware, require_auth, create_demo_tokens, UserRoles
from app.db.database import init_db
from app.api.scans import router as scans_router
from app.engine.semgrep import SemgrepRunner
from app.engine.gitleaks import GitleaksRunner

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    init_db()
    logger.info("DiffGuard initialized")
    yield
    logger.info("DiffGuard shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="DiffGuard: Security-focused code review and vulnerability analysis engine",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.enable_docs else None,
    redoc_url="/api/redoc" if settings.enable_docs else None,
    openapi_url="/api/openapi.json" if settings.enable_docs else None,
)

# Add security middleware
app.middleware("http")(rate_limit_middleware)

# CORS configuration - restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Health check (no auth required)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    semgrep_status = SemgrepRunner().is_available()
    gitleaks_status = GitleaksRunner().is_available()
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
        "scanners": {
            "semgrep_installed": semgrep_status,
            "gitleaks_installed": gitleaks_status
        },
        "ai_provider_configured": settings.ai_provider
    }


# Demo tokens for testing (disable in production)
@app.get("/api/auth/demo-tokens")
async def get_demo_tokens():
    """Get demo tokens for testing (should be removed in production)."""
    return {
        "tokens": create_demo_tokens(),
        "warning": "This endpoint should be disabled in production",
        "roles": {
            "VIEWER": "Can view reports only",
            "ANALYST": "Can initiate scans and view reports",
            "ADMIN": "Full access including user management"
        }
    }


# Authentication verification
@app.get("/api/auth/verify")
async def verify_auth(current_user=Depends(require_auth())):
    """Verify authentication."""
    return {
        "authenticated": True,
        "user": {
            "sub": current_user.sub,
            "role": current_user.role
        }
    }


# Include routers with authentication requirements
# Scans API requires at least ANALYST role
app.include_router(scans_router, dependencies=[Depends(require_auth(UserRoles.ANALYST))])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )