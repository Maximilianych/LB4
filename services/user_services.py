from utils import log_action, load_json, save_json
from datetime import datetime

USERS_FILE = "data/users.json"

class AuthService:
    """Регистрация и аутентификация пользователей"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        
        if action == "register":
            self._register_user(data)
        elif action == "login":
            self._login_user(data)
    
    def _register_user(self, data):
        """Регистрирует нового пользователя."""
        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "user")
        
        users = load_json(USERS_FILE)
        
        if username in users:
            log_action("ОШИБКА РЕГИСТРАЦИИ", details=f"Пользователь '{username}' уже существует")
            return
        
        users[username] = {
            "password": password,
            "role": role,
            "email": data.get("email", f"{username}@example.com"),
            "profile_created": False
        }
        
        save_json(USERS_FILE, users)
        log_action("РЕГИСТРАЦИЯ", user=username, details=f"Роль: {role}")
        
        if self.bus:
            self.bus.publish("user_registered", {
                "username": username,
                "email": users[username]["email"],
                "role": role
            })
    
    def _login_user(self, data):
        """Вход пользователя в систему."""
        username = data.get("username")
        password = data.get("password")
        
        users = load_json(USERS_FILE)
        
        if username not in users:
            log_action("ОШИБКА ВХОДА", details=f"Пользователь '{username}' не найден")
            return None
        
        if password != users[username]["password"]:
            log_action("ОШИБКА ВХОДА", user=username, details="Неверный пароль")
            return None
        
        log_action("ВХОД В СИСТЕМУ", user=username, details=f"Роль: {users[username]['role']}")
        
        if self.bus:
            self.bus.publish("user_logged_in", {
                "username": username,
                "role": users[username]["role"]
            })
        
        return users[username]


class VerificationService:
    """Подтверждение почты и проверка данных"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        event_type = data.get("_event_type")
        
        if action == "verify_email" or event_type == "user_registered":
            self._verify_email(data)
    
    def _verify_email(self, data):
        """Симулирует проверку email."""
        username = data.get("username")
        email = data.get("email")
        
        log_action("ВЕРИФИКАЦИЯ EMAIL", user=username, details=f"Email: {email}")
        
        if self.bus:
            self.bus.publish("email_verified", {
                "username": username,
                "email": email,
                "role": data.get("role")
            })


class ProfileService:
    """Создание и обновление профиля пользователя"""
    
    def __init__(self):
        self.bus = None
    
    def handle(self, data):
        action = data.get("action")
        event_type = data.get("_event_type")
        
        if action == "create_profile" or event_type == "email_verified":
            self._create_profile(data)
        elif action == "update_profile":
            self._update_profile(data)
    
    def _create_profile(self, data):
        """Создает профиль пользователя после верификации."""
        username = data.get("username")
        
        users = load_json(USERS_FILE)
        
        if username in users and not users[username].get("profile_created"):
            users[username]["profile_created"] = True
            users[username]["created_at"] = str(datetime.now())
            save_json(USERS_FILE, users)
            
            log_action("СОЗДАНИЕ ПРОФИЛЯ", user=username, details="Профиль создан")
            
            if self.bus:
                self.bus.publish("profile_created", {
                    "username": username,
                    "message": f"Профиль пользователя {username} создан"
                })
    
    def _update_profile(self, data):
        """Обновляет профиль пользователя."""
        username = data.get("username")
        updates = data.get("updates", {})
        
        users = load_json(USERS_FILE)
        
        if username in users:
            users[username].update(updates)
            save_json(USERS_FILE, users)
            log_action("ОБНОВЛЕНИЕ ПРОФИЛЯ", user=username, details=str(updates))