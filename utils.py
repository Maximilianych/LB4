import json
import os
from datetime import datetime

def log_action(action, user=None, details=None):
    """Логирует действие в консоль с временной меткой"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_str = f"[{user}]" if user else ""
    details_str = f"- {details}" if details else ""
    log_message = f"[{timestamp}] {user_str} {action} {details_str}"
    print(log_message)
    
    # Опционально: запись в файл
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

def load_json(filepath):
    """
    Загружает данные из JSON файла
    Если файл не существует, возвращает пустой словарь
    """
    if not os.path.exists(filepath):
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_json(filepath, data):
    """Сохраняет данные в JSON файл"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)