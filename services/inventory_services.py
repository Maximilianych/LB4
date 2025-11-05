from utils import log_action, load_json, save_json

INVENTORY_FILE = "data/inventory.json"
USERS_FILE = "data/users.json"

class InventoryService:
    """Управление складом"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        event_type = data.get("_event_type")
        
        if action == "check_item":
            return self._check_item(data)
        elif action == "reserve_item":
            return self._reserve_item(data)
        elif action == "release_item":
            return self._release_item(data)
        elif event_type == "order_created":
            self._reserve_items_for_order(data)
    
    def _check_item(self, data):
        """Проверяет наличие товара на складе."""
        item_name = data.get("item_name")
        quantity = data.get("quantity", 1)
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name not in inventory:
            log_action("ПРОВЕРКА СКЛАДА", details=f"Товар '{item_name}' не найден")
            return False
        
        available = inventory[item_name].get("quantity", 0)
        
        if available < quantity:
            log_action("ПРОВЕРКА СКЛАДА", details=f"Недостаточно '{item_name}': есть {available}, нужно {quantity}")
            return False
        
        log_action("ПРОВЕРКА СКЛАДА", details=f"Товар '{item_name}' доступен: {available} шт.")
        return True
    
    def _reserve_item(self, data):
        """Резервирует товар для заказа."""
        item_name = data.get("item_name")
        quantity = data.get("quantity", 1)
        order_id = data.get("order_id")
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name not in inventory or inventory[item_name]["quantity"] < quantity:
            return False
        
        inventory[item_name]["quantity"] -= quantity
        
        if "reserved" not in inventory[item_name]:
            inventory[item_name]["reserved"] = []
        
        inventory[item_name]["reserved"].append({
            "order_id": order_id,
            "quantity": quantity
        })
        
        save_json(INVENTORY_FILE, inventory)
        log_action("РЕЗЕРВИРОВАНИЕ", details=f"Заказ {order_id}: {item_name} x{quantity}")
        
        if self.bus:
            self.bus.publish("item_reserved", {
                "order_id": order_id,
                "item_name": item_name,
                "quantity": quantity,
                "username": data.get("username"),
                "message": f"Зарезервировано: {item_name} x{quantity}"
            })
        
        return True
    
    def _reserve_items_for_order(self, data):
        """Резервирует все товары для заказа."""
        order_id = data.get("order_id")
        items = data.get("items", [])
        username = data.get("username")
        
        log_action("НАЧАЛО РЕЗЕРВИРОВАНИЯ", user=username, details=f"Заказ {order_id}, товаров: {len(items)}")
        
        all_reserved = True
        
        for item in items:
            success = self._reserve_item({
                "item_name": item["item_name"],
                "quantity": item["quantity"],
                "order_id": order_id,
                "username": username
            })
            
            if not success:
                all_reserved = False
                break
        
        if all_reserved:
            log_action("РЕЗЕРВИРОВАНИЕ ЗАВЕРШЕНО", user=username, details=f"Заказ {order_id}")
            if self.bus:
                self.bus.publish("all_items_reserved", {
                    "order_id": order_id,
                    "username": username
                })
    
    def _release_item(self, data):
        """Освобождает зарезервированный товар."""
        item_name = data.get("item_name")
        quantity = data.get("quantity", 1)
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name in inventory:
            inventory[item_name]["quantity"] += quantity
            save_json(INVENTORY_FILE, inventory)
            log_action("ОСВОБОЖДЕНИЕ ТОВАРА", details=f"{item_name} x{quantity}")


class PurchaseService:
    """Пополнение и управление складом (только для admin)"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        
        if action == "add_item":
            self._add_item(data)
        elif action == "update_item":
            self._update_item(data)
        elif action == "remove_item":
            self._remove_item(data)
    
    def _check_admin(self, username):
        """Проверяет права администратора."""
        users = load_json(USERS_FILE)
        
        if username not in users or users[username].get("role") != "admin":
            log_action("ОТКАЗ В ДОСТУПЕ", user=username, details="Требуются права admin")
            return False
        
        return True
    
    def _add_item(self, data):
        """Добавляет новый товар на склад."""
        username = data.get("username")
        item_name = data.get("item_name")
        quantity = data.get("quantity", 0)
        price = data.get("price", 0)
        
        if not self._check_admin(username):
            return
        
        # Простая валидация
        try:
            quantity = int(quantity)
            price = float(price)
            if quantity <= 0 or price <= 0:
                log_action("ОШИБКА ВАЛИДАЦИИ", user=username, details="Количество и цена должны быть положительными")
                return
        except (ValueError, TypeError):
            log_action("ОШИБКА ВАЛИДАЦИИ", user=username, details="Некорректные числовые значения")
            return
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name in inventory:
            log_action("ОШИБКА ДОБАВЛЕНИЯ", user=username, details=f"Товар '{item_name}' уже существует")
            return
        
        inventory[item_name] = {
            "quantity": quantity,
            "price": price,
            "reserved": []
        }
        
        save_json(INVENTORY_FILE, inventory)
        log_action("ДОБАВЛЕНИЕ ТОВАРА", user=username, details=f"{item_name}: {quantity} шт. по {price} руб.")
        
        if self.bus:
            self.bus.publish("item_added", {
                "username": username,
                "item_name": item_name,
                "quantity": quantity,
                "price": price,
                "message": f"На склад добавлен товар: {item_name} ({quantity} шт.)"
            })
    
    def _update_item(self, data):
        """Обновляет количество товара на складе."""
        username = data.get("username")
        item_name = data.get("item_name")
        quantity = data.get("quantity")
        price = data.get("price")
        
        if not self._check_admin(username):
            return
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name not in inventory:
            log_action("ОШИБКА ОБНОВЛЕНИЯ", user=username, details=f"Товар '{item_name}' не найден")
            return
        
        # Простая валидация и обновление
        try:
            if quantity is not None:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
                inventory[item_name]["quantity"] = quantity
            
            if price is not None:
                price = float(price)
                if price <= 0:
                    raise ValueError
                inventory[item_name]["price"] = price
        except (ValueError, TypeError):
            log_action("ОШИБКА ВАЛИДАЦИИ", user=username, details="Некорректные значения")
            return
        
        save_json(INVENTORY_FILE, inventory)
        log_action("ОБНОВЛЕНИЕ ТОВАРА", user=username, details=f"{item_name}")
        
        if self.bus:
            self.bus.publish("item_updated", {
                "username": username,
                "item_name": item_name,
                "message": f"Товар '{item_name}' обновлен"
            })
    
    def _remove_item(self, data):
        """Удаляет товар со склада."""
        username = data.get("username")
        item_name = data.get("item_name")
        
        if not self._check_admin(username):
            return
        
        inventory = load_json(INVENTORY_FILE)
        
        if item_name not in inventory:
            log_action("ОШИБКА УДАЛЕНИЯ", user=username, details=f"Товар '{item_name}' не найден")
            return
        
        del inventory[item_name]
        save_json(INVENTORY_FILE, inventory)
        log_action("УДАЛЕНИЕ ТОВАРА", user=username, details=f"{item_name}")
        
        if self.bus:
            self.bus.publish("item_removed", {
                "username": username,
                "item_name": item_name,
                "message": f"Товар '{item_name}' удален"
            })