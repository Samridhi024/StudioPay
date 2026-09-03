from fastapi import APIRouter, Query

from app.services.audit_service import (
    get_recent_audit_events,
)


router = APIRouter(
    prefix="/api/audit",
    tags=["Audit Trail"],
)


@router.get("/recent")
def recent_audit_events(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
):
    events = get_recent_audit_events(limit)

    return {
        "count": len(events),
        "events": events,
    }