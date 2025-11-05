from utils import log_action

class NotificationService:
    """Отправка уведомлений пользователям"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        event_type = data.get("_event_type")
        
        # Реагируем на различные события
        if event_type in [
            "profile_created", 
            "delivery_scheduled", 
            "item_added", 
            "item_reserved",
            "item_updated",
            "item_removed",
            "payment_done",
            "all_items_reserved"
        ]:
            self._send_notification(data)
    
    def _send_notification(self, data):
        """
        Отправляет уведомление пользователю.
        """
        username = data.get("username", "Система")
        message = data.get("message", "Системное уведомление")
        event_type = data.get("_event_type", "unknown")
        order_id = data.get("order_id", "")
        
        # Формируем красивое сообщение в зависимости от типа события
        emoji = "📧"
        if event_type == "item_added":
            emoji = "📦"
        elif event_type == "item_reserved":
            emoji = "🔒"
        elif event_type == "payment_done":
            emoji = "💰"
        elif event_type == "delivery_scheduled":
            emoji = "🚚"
        elif event_type == "profile_created":
            emoji = "👤"
        
        log_action("УВЕДОМЛЕНИЕ", user=username, details=f"{event_type}: {message}")
        
        print(f"\n{'='*60}")
        print(f"{emoji} УВЕДОМЛЕНИЕ для {username}")
        print(f"Тип события: {event_type}")
        if order_id:
            print(f"Заказ: {order_id}")
        print(f"Сообщение: {message}")
        print(f"{'='*60}\n")