from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_agent import (
    router as agent_router,
)
from app.api.routes_audit import (
    router as audit_router,
)
from app.api.routes_customer import (
    router as customer_router,
)
from app.api.routes_dashboard import (
    router as dashboard_router,
)
from app.api.routes_payments import (
    router as payments_router,
)
from app.api.routes_policy import (
    router as policy_router,
)
from app.api.routes_webhook import (
    router as webhook_router,
)
from app.core.config import get_settings
from app.services.agent_service import (
    is_huggingface_configured,
)


settings = get_settings()

allowed_origins = [
    origin.strip()
    for origin in settings.frontend_url.split(",")
    if origin.strip()
]

if settings.app_env == "development":
    for local_origin in [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8502",
        "http://127.0.0.1:8502",
    ]:
        if local_origin not in allowed_origins:
            allowed_origins.append(local_origin)


app = FastAPI(
    title="StudioPay API",
    description=(
        "AI-powered revenue recovery platform"
    ),
    version="0.3.0",
)

app.include_router(dashboard_router)
app.include_router(policy_router)
app.include_router(agent_router)
app.include_router(payments_router)
app.include_router(webhook_router)
app.include_router(audit_router)
app.include_router(customer_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "StudioPay API",
        "version": "0.3.0",
        "environment": settings.app_env,
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "studiopay-backend",
    }


@app.get("/api/integrations/status")
def integration_status():
    return {
        "huggingface": {
            "configured": (
                is_huggingface_configured()
            ),
        },
        "clickhouse": {
            "configured": bool(
                settings.clickhouse_host
                and settings.clickhouse_password
            ),
        },
        "razorpay": {
            "configured": bool(
                settings.razorpay_key_id
                and settings.razorpay_key_secret
            ),
        },
    }