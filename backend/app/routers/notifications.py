# routers/notifications.py

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.utils.logger import logger, log_with_context

router = APIRouter()

# ═══════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════

class NotificationPayload(BaseModel):
    message: str
    type: str
    severity: str

# ═══════════════════════════════════════════════════════
# SECURITY
# ═══════════════════════════════════════════════════════

# Dummy security function for now
async def verify_api_key(x_api_key: str = Header(...)):
    # In a real app, this would be a secure comparison against secrets
    if x_api_key != "super-secret-admin":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# ═══════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════

@router.post("/api/notifications/inventory", dependencies=[Depends(verify_api_key)])
async def handle_inventory_notification(payload: NotificationPayload):
    """
    Receives inventory alert notifications from n8n.
    For now, it just logs the alert.
    """
    log_with_context(
        logger,
        "warning",  # Using warning level to make it stand out
        "Received inventory alert",
        severity=payload.severity,
        notification_type=payload.type,
        message=payload.message
    )
    
    # In a real-world scenario, you would trigger actions here, like:
    # - Sending an email to the procurement team
    # - Creating a ticket in a management system (Jira, etc.)
    # - Sending a push notification to an admin app
    
    return {"status": "notification_received", "payload": payload} 