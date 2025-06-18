# routers/inventory.py

from fastapi import APIRouter, Header, Depends, HTTPException
from typing import List
from app.services.postgres import get_all_products
from app.services.notification_service import NotificationService
from app.utils.logger import logger, log_with_context

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Dependencia de seguridad para proteger el endpoint
async def verify_admin_key(x_api_key: str = Header(...)):
    # Usaremos una clave simple por ahora. En producción, debería ser un secreto.
    # Esta clave podría ser diferente de la de notificaciones si quisiéramos.
    if x_api_key != "super-secret-admin":
        raise HTTPException(status_code=401, detail="Invalid Admin API Key")
    return x_api_key

@router.post("/check", dependencies=[Depends(verify_admin_key)])
def check_inventory_and_alert():
    """
    Endpoint to check product inventory, identify low-stock or out-of-stock items,
    and generate a log alert. This encapsulates the logic previously in n8n.
    """
    log_with_context(logger, "info", "Starting scheduled inventory check...")

    try:
        all_products = get_all_products()
        if not all_products:
            log_with_context(logger, "info", "Inventory check ran, but no products found.")
            return {"status": "ok", "message": "No products found."}

        low_stock_threshold = 10
        out_of_stock_threshold = 0

        low_stock_products = []
        out_of_stock_products = []

        for product in all_products:
            stock = product.get('stock', 0)
            if stock <= out_of_stock_threshold:
                out_of_stock_products.append(product)
            elif stock <= low_stock_threshold:
                low_stock_products.append(product)

        if not low_stock_products and not out_of_stock_products:
            log_with_context(logger, "info", f"Inventory check completed. All {len(all_products)} products have sufficient stock.")
            return {"status": "ok", "message": "All products have sufficient stock."}

        # Si hay alertas, generar el mensaje
        alert_message = '🚨 *ALERTA DE INVENTARIO* 🚨\\n\\n'

        if out_of_stock_products:
            alert_message += f"❌ *PRODUCTOS AGOTADOS ({len(out_of_stock_products)}):*\\n"
            for product in out_of_stock_products:
                alert_message += f"• {product.get('name')} (SKU: {product.get('sku')})\\n"
            alert_message += '\\n'

        if low_stock_products:
            alert_message += f"⚠️ *STOCK BAJO ({len(low_stock_products)}):*\\n"
            for product in low_stock_products:
                alert_message += f"• {product.get('name')} - Stock: {product.get('stock')} (SKU: {product.get('sku')})\\n"
            alert_message += '\\n'
        
        # Usar el servicio de notificaciones
        notification_service = NotificationService(context={"source": "inventory_check"})
        
        # 1. Enviar siempre al log
        notification_service.send_log_alert(
            subject="Inventory Alert Generated",
            details=alert_message,
            severity="warning"
        )
        
        # 2. Simular envío por otros canales
        notification_service.send_email_alert(
            recipient="admin@hardwarestore.com",
            subject="Alerta de Inventario",
            body=alert_message
        )
        
        notification_service.send_telegram_alert(
            chat_id="admin_group_chat",
            message=alert_message
        )
        
        return {
            "status": "alert_generated",
            "delivery_status": {
                "log": "sent",
                "email": "simulated",
                "telegram": "simulated"
            },
            "out_of_stock_count": len(out_of_stock_products),
            "low_stock_count": len(low_stock_products)
        }

    except Exception as e:
        logger.error(f"Failed to run inventory check: {e}", exc_info=True)
        # Devolvemos un error 500 si algo falla
        raise HTTPException(status_code=500, detail="Internal server error during inventory check.") 