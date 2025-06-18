# services/notification_service.py

from app.utils.logger import logger, log_with_context

class NotificationService:
    """
    A centralized service for handling all outgoing notifications.
    Each method corresponds to a different notification channel.
    """

    def __init__(self, context: dict = None):
        """
        Initialize the service with optional context for logging.
        """
        self.context = context or {}

    def send_log_alert(self, subject: str, details: str, severity: str = "info"):
        """
        Sends a notification to the system logs. This is the default and always active.
        """
        log_with_context(
            logger,
            severity,
            subject,
            details=details,
            **self.context
        )

    def send_email_alert(self, recipient: str, subject: str, body: str):
        """
        Sends an email notification.
        (Currently a placeholder).
        """
        log_with_context(
            logger,
            "info",
            "Simulating email notification",
            recipient=recipient,
            subject=subject,
            # In a real implementation, we would not log the body unless necessary.
            # body_preview=body[:50] + "..." 
        )
        # TODO: Implement actual email sending logic using a library like smtplib or an external API (SendGrid, etc.)
        pass

    def send_telegram_alert(self, chat_id: str, message: str):
        """
        Sends a Telegram notification.
        (Currently a placeholder).
        """
        log_with_context(
            logger,
            "info",
            "Simulating Telegram notification",
            chat_id=chat_id,
            # message_preview=message[:50] + "..."
        )
        # TODO: Implement Telegram Bot API call here.
        pass
        
    def send_whatsapp_alert(self, phone_number: str, message: str):
        """
        Sends a WhatsApp notification.
        (Currently a placeholder).
        """
        log_with_context(
            logger,
            "info",
            "Simulating WhatsApp notification",
            phone_number=phone_number,
            # message_preview=message[:50] + "..."
        )
        # TODO: Implement WhatsApp Business API call here (e.g., via Twilio).
        pass

# Global instance for convenience
notification_service = NotificationService() 