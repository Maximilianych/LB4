from utils import log_action, load_json, save_json
import uuid

ORDERS_FILE = "data/orders.json"
INVENTORY_FILE = "data/inventory.json"

class OrderService:
    """Создание и управление заказами"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        
        if action == "create_order":
            self._create_order(data)
    
    def _create_order(self, data):
        """Создает новый заказ."""
        username = data.get("username")
        items = data.get("items", [])
        
        if not items:
            log_action("ОШИБКА СОЗДАНИЯ ЗАКАЗА", user=username, details="Список товаров пуст")
            return
        
        order_id = str(uuid.uuid4())[:8]
        
        # Вычисляем общую стоимость
        inventory = load_json(INVENTORY_FILE)
        total = 0
        for item in items:
            if item["item_name"] in inventory:
                price = inventory[item["item_name"]].get("price", 0)
                total += price * item["quantity"]
        
        # Создаем заказ
        orders = load_json(ORDERS_FILE)
        orders[order_id] = {
            "username": username,
            "items": items,
            "status": "created",
            "total": total
        }
        save_json(ORDERS_FILE, orders)
        
        log_action("СОЗДАНИЕ ЗАКАЗА", user=username, details=f"ID: {order_id}, Сумма: {total} руб.")
        
        if self.bus:
            self.bus.publish("order_created", {
                "order_id": order_id,
                "username": username,
                "items": items,
                "total": total
            })


class PaymentService:
    """Обработка платежей"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        event_type = data.get("_event_type")
        action = data.get("action")
        
        if event_type == "order_created" or action == "process_payment":
            self._process_payment(data)
    
    def _process_payment(self, data):
        """Обрабатывает платеж для заказа."""
        order_id = data.get("order_id")
        username = data.get("username")
        total = data.get("total", 0)
        
        log_action("ОБРАБОТКА ПЛАТЕЖА", user=username, details=f"Заказ {order_id}, Сумма: {total} руб.")
        
        # Обновляем статус заказа
        orders = load_json(ORDERS_FILE)
        if order_id in orders:
            orders[order_id]["status"] = "paid"
            save_json(ORDERS_FILE, orders)
        
        if self.bus:
            self.bus.publish("payment_done", {
                "order_id": order_id,
                "username": username,
                "total": total
            })


class DeliveryService:
    """Организация доставки"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        event_type = data.get("_event_type")
        action = data.get("action")
        
        if event_type == "payment_done" or action == "schedule_delivery":
            self._schedule_delivery(data)
    
    def _schedule_delivery(self, data):
        """Планирует доставку заказа."""
        order_id = data.get("order_id")
        username = data.get("username")
        
        log_action("ПЛАНИРОВАНИЕ ДОСТАВКИ", user=username, details=f"Заказ {order_id}")
        
        # Обновляем статус
        orders = load_json(ORDERS_FILE)
        if order_id in orders:
            orders[order_id]["status"] = "in_delivery"
            save_json(ORDERS_FILE, orders)
        
        if self.bus:
            self.bus.publish("delivery_scheduled", {
                "order_id": order_id,
                "username": username,
                "message": f"Заказ {order_id} отправлен в доставку"
            })