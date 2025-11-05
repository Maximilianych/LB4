class ServiceBus:
    """
    - services: словарь зарегистрированных сервисов {name: service_instance}
    - subscribers: словарь подписок на события {event_name: [service_name1, service_name2]}
    """

    def __init__(self):
        self.services = {}
        self.subscribers = {}

    def register_service(self, name, service):
        """
        Регистрирует сервис в шине и передает ссылку на шину сервису.
        """
        self.services[name] = service
        service.bus = self  # сервис может публиковать события через шину

    def subscribe(self, event_name, service_name):
        """
        Подписывает сервис на событие.
        """
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(service_name)

    def publish(self, event_name, data):
        """
        Публикует событие: уведомляет все подписанные сервисы.
        Добавляет имя события в данные для контекста (_event_type).
        """
        # Создаем обогащенный payload с именем события
        payload = data.copy()
        payload['_event_type'] = event_name

        print(f"\n[ServiceBus] Событие '{event_name}' опубликовано с данными: {data}")
        if event_name in self.subscribers:
            for service_name in self.subscribers[event_name]:
                # Отправляем обогащенный payload
                self.send(service_name, payload)

    def send(self, target_service, data):
        """
        Отправляет данные конкретному сервису (вызывает handle).
        """
        if target_service not in self.services:
            print(f"[ServiceBus] Ошибка: сервис '{target_service}' не найден.")
            return
        self.services[target_service].handle(data)