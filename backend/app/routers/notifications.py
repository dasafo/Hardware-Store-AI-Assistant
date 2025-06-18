# routers/notifications.py

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.notification_service import NotificationService
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
    Receives a generic notification and dispatches it using the NotificationService.
    """
    log_with_context(
        logger,
        "info",
        "Received external notification request",
        severity=payload.severity,
        notification_type=payload.type
    )

    # Crear una instancia del servicio de notificaciones
    notification_service = NotificationService(context={"source": "api_endpoint"})

    # Usar el servicio para enviar las notificaciones
    # Por ahora, solo lo logueamos, pero podríamos añadir más lógica aquí
    notification_service.send_log_alert(
        subject=f"External Alert: {payload.type}",
        details=payload.message,
        severity=payload.severity.lower() if payload.severity.lower() in ["info", "warning", "error"] else "info"
    )

    # Podríamos añadir lógica para enviar a otros canales basados en el payload
    if payload.type == "inventory_alert":
        notification_service.send_email_alert(
            recipient="inventory_team@hardwarestore.com",
            subject=f"External Inventory Alert ({payload.severity})",
            body=payload.message
        )

    return {"status": "notification_dispatched", "payload_received": payload} 