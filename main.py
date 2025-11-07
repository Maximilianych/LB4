from service_bus import ServiceBus
from services.order_services import OrderService, PaymentService, DeliveryService
from services.inventory_services import InventoryService, PurchaseService
from services.user_services import AuthService, VerificationService, ProfileService
from services.notification_services import NotificationService
from utils import log_action, load_json

current_user = None

def main():
    global current_user
    
    bus = ServiceBus()
    
    # Регистрация сервисов
    bus.register_service("order", OrderService())
    bus.register_service("payment", PaymentService())
    bus.register_service("delivery", DeliveryService())
    bus.register_service("inventory", InventoryService())
    bus.register_service("purchase", PurchaseService())
    bus.register_service("auth", AuthService())
    bus.register_service("verify", VerificationService())
    bus.register_service("profile", ProfileService())
    bus.register_service("notify", NotificationService())
    
    # Подписки на события
    bus.subscribe("user_registered", "verify")
    bus.subscribe("email_verified", "profile")
    bus.subscribe("profile_created", "notify")
    
    bus.subscribe("order_created", "inventory")
    bus.subscribe("order_created", "payment")
    
    bus.subscribe("all_items_reserved", "notify")
    bus.subscribe("item_reserved", "notify")
    
    bus.subscribe("payment_done", "notify")
    bus.subscribe("payment_done", "delivery")
    
    bus.subscribe("delivery_scheduled", "notify")
    
    bus.subscribe("item_added", "notify")
    bus.subscribe("item_updated", "notify")
    bus.subscribe("item_removed", "notify")
    
    print("="*60)
    print("СИСТЕМА УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ И СКЛАДОМ")
    print("="*60)
    
    while True:
        print("\n" + "="*60)
        if current_user:
            print(f"Текущий пользователь: {current_user['username']} ({current_user['role']})")
        else:
            print("Вы не авторизованы")
        print("="*60)
        print("\nВыберите действие:")
        
        if not current_user: # Без роли
            print("1. Зарегистрировать нового пользователя")
            print("2. Войти в систему")
            print("0. Выход")
            
            choice = input("\nВведите номер действия: ").strip()
            
            if choice == "1":
                register_user(bus)
            elif choice == "2":
                login_user(bus)
            elif choice == "0":
                print("\n" + "="*60)
                print("Выход из системы... До свидания!")
                print("="*60)
                break
            else:
                print("Некорректный выбор")
        
        elif current_user["role"] == "admin": # Admin
            print("1. Просмотреть склад")
            print("2. Управлять складом")
            print("3. Создать заказ")
            print("4. Выйти из аккаунта")
            print("0. Выход")
            
            choice = input("\nВведите номер действия: ").strip()
            
            if choice == "1":
                view_inventory()
            elif choice == "2":
                manage_inventory(bus)
            elif choice == "3":
                create_order(bus)
            elif choice == "4":
                log_action("ВЫХОД", user=current_user['username'])
                print(f"Пользователь {current_user['username']} вышел из системы")
                current_user = None
            elif choice == "0":
                print("\n" + "="*60)
                print("Выход из системы... До свидания!")
                print("="*60)
                break
            else:
                print("Некорректный выбор")
        
        else: # User
            print("1. Просмотреть склад")
            print("2. Создать заказ")
            print("3. Выйти из аккаунта")
            print("0. Выход")
            
            choice = input("\nВведите номер действия: ").strip()
            
            if choice == "1":
                view_inventory()
            elif choice == "2":
                create_order(bus)
            elif choice == "3":
                log_action("ВЫХОД", user=current_user['username'])
                print(f"Пользователь {current_user['username']} вышел из системы")
                current_user = None
            elif choice == "0":
                print("\n" + "="*60)
                print("Выход из системы... До свидания!")
                print("="*60)
                break
            else:
                print("Некорректный выбор, попробуйте снова.")

def register_user(bus):
    print("\n" + "-"*60)
    print("РЕГИСТРАЦИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ")
    print("-"*60)
    
    username = input("Введите имя пользователя: ").strip()
    if not username:
        return
    
    password = input("Введите пароль: ").strip()
    if not password:
        print("Ошибка: Пароль не может быть пустым.")
        return
    
    print("\nВыберите роль:")
    print("1. admin (администратор)")
    print("2. user (пользователь)")
    role_choice = input("Введите номер (по умолчанию 2): ").strip()
    
    role = "admin" if role_choice == "1" else "user"
    
    email = input("Введите email (опционально): ").strip()
    
    bus.send("auth", {
        "action": "register",
        "username": username,
        "password": password,
        "role": role,
        "email": email if email else f"-@-.-"
    })


def login_user(bus):
    global current_user
    
    print("\n" + "-"*60)
    print("ВХОД В СИСТЕМУ")
    print("-"*60)
    
    username = input("Введите имя пользователя: ").strip()
    password = input("Введите пароль: ").strip()
    
    users = load_json("data/users.json")
    
    if username not in users:
        print(f"Ошибка: Пользователь '{username}' не найден.")
        return
    
    if password != users[username]["password"]:
        print("Ошибка: Неверный пароль.")
        return
    
    current_user = {
        "username": username,
        "role": users[username]["role"],
        "email": users[username].get("email")
    }
    
    bus.send("auth", {
        "action": "login",
        "username": username,
        "password": password
    })
    
    print(f"\n Добро пожаловать, {username}! Роль: {current_user['role']}")


def manage_inventory(bus):
    if current_user["role"] != "admin":
        print("Ошибка: Управление складом доступно только администраторам.")
        return
    
    print("\n" + "-"*60)
    print("УПРАВЛЕНИЕ СКЛАДОМ")
    print("-"*60)
    print("1. Добавить товар")
    print("2. Обновить товар")
    print("3. Удалить товар")
    print("0. Назад")
    
    choice = input("\nВведите номер действия: ").strip()
    
    if choice == "1":
        add_item(bus)
    elif choice == "2":
        update_item(bus)
    elif choice == "3":
        remove_item(bus)
    elif choice == "0":
        return
    else:
        print("Некорректный выбор.")


def add_item(bus):
    print("\n--- Добавление товара ---")
    
    item_name = input("Введите название товара: ").strip()
    if not item_name:
        print("Ошибка: Название товара не может быть пустым.")
        return
    
    try:
        quantity = int(input("Введите количество: ").strip())
        price = float(input("Введите цену за единицу: ").strip())
    except ValueError:
        print("Некорректные данные")
        return
    
    bus.send("purchase", {
        "action": "add_item",
        "username": current_user["username"],
        "item_name": item_name,
        "quantity": quantity,
        "price": price
    })


def update_item(bus):
    print("\n--- Обновление товара ---")
    
    # Показываем текущий склад
    inventory = load_json("data/inventory.json")
    if not inventory:
        print("Склад пуст")
        return
    
    print("\nТекущий склад:")
    for item_name, details in inventory.items():
        print(f"  - {item_name}: {details['quantity']} шт., {details['price']} руб.")
    
    item_name = input("\nВведите название товара для обновления: ").strip()
    
    if item_name not in inventory:
        print(f"Ошибка: Товар '{item_name}' не найден.")
        return
    
    print(f"\nТекущие данные: {inventory[item_name]['quantity']} шт., {inventory[item_name]['price']} руб.")
    
    try:
        quantity = input("Введите новое количество (Enter - не менять): ").strip()
        price = input("Введите новую цену (Enter - не менять): ").strip()
        
        data = {
            "action": "update_item",
            "username": current_user["username"],
            "item_name": item_name
        }
        
        if quantity:
            data["quantity"] = int(quantity)
        
        if price:
            data["price"] = float(price)
        
        bus.send("purchase", data)
        
    except ValueError:
        print("Ошибка: Введите корректные значения.")


def remove_item(bus):
    print("\n--- Удаление товара ---")
    
    inventory = load_json("data/inventory.json")
    if not inventory:
        print("Склад пуст")
        return
    
    print("\nТекущий склад:")
    for item_name, details in inventory.items():
        print(f"  - {item_name}: {details['quantity']} шт.")
    
    item_name = input("\nВведите название товара для удаления: ").strip()
    
    confirm = input(f"Вы уверены, что хотите удалить '{item_name}'? (да/нет): ").strip().lower()
    
    if confirm in ["да", "yes", "y"]:
        bus.send("purchase", {
            "action": "remove_item",
            "username": current_user["username"],
            "item_name": item_name
        })
    else:
        print("Удаление отменено")


def view_inventory():
    print("\n" + "-"*60)
    print("ТЕКУЩИЙ СКЛАД")
    print("-"*60)
    
    inventory = load_json("data/inventory.json")
    
    if not inventory:
        print("Склад пуст")
        return
    
    print(f"\n{'Товар':<30} {'Количество':<15} {'Цена':<15}")
    print("-"*60)
    
    for item_name, details in inventory.items():
        quantity = details.get("quantity", 0)
        price = details.get("price", 0)
        reserved_total = sum([r.get("quantity", 0) for r in details.get("reserved", [])])
        
        status = f"{quantity} шт."
        if reserved_total > 0:
            status += f" ({reserved_total})"
        
        print(f"{item_name:<30} {status:<15} {price:<15.2f} руб.")
    
    print("-"*60)


def create_order(bus):
    print("\n" + "-"*60)
    print("СОЗДАНИЕ ЗАКАЗА")
    print("-"*60)
    
    # Показываем доступные товары
    inventory = load_json("data/inventory.json")
    
    if not inventory:
        print("Склад пуст. Невозможно создать заказ")
        return
    
    print("\nДоступные товары:")
    for item_name, details in inventory.items():
        print(f"  - {item_name}: {details['quantity']} шт., {details['price']} руб.")
    
    items = []
    
    while True:
        print("\n--- Добавление товара в заказ ---")
        item_name = input("Введите название товара (или 'готово' для завершения): ").strip()
        
        if item_name.lower() == 'готово':
            break
        
        if item_name not in inventory:
            print(f"Товар '{item_name}' не найден на складе.")
            continue
        
        try:
            quantity = int(input(f"Введите количество '{item_name}': ").strip())
            
            if quantity <= 0:
                print("Количество должно быть положительным.")
                continue
            
            if quantity > inventory[item_name]["quantity"]:
                print(f"Недостаточно товара. Доступно: {inventory[item_name]['quantity']}")
                continue
            
            items.append({
                "item_name": item_name,
                "quantity": quantity
            })
            
            print(f"Добавлено: {item_name} x{quantity}")
            
        except ValueError:
            print("Введите корректное число")
    
    if not items:
        print("Заказ пуст. Отмена")
        return
    
    # Показываем итоговый заказ
    print("\n" + "-"*60)
    print("ИТОГОВЫЙ ЗАКАЗ:")
    total = 0
    for item in items:
        item_price = inventory[item["item_name"]]["price"]
        item_total = item_price * item["quantity"]
        total += item_total
        print(f"  {item['item_name']}: {item['quantity']} шт. x {item_price} руб. = {item_total} руб.")
    print(f"\nИТОГО: {total} руб.")
    print("-"*60)
    
    confirm = input("\nПодтвердить заказ? (да/нет): ").strip().lower()
    
    if confirm in ["да", "yes", "y"]:
        bus.send("order", {
            "action": "create_order",
            "username": current_user["username"],
            "items": items
        })


if __name__ == "__main__":
    main()