class HomeAssistant:
    def __init__(self):
        self.config = type("Config", (), {"time_zone": "UTC", "language": "en"})()
        self.data = {}
        self.services = type("Services", (), {"has_service": lambda *args: True})()
        self.bus = type("Bus", (), {"async_fire": lambda *args: None})()


class ServiceCall:
    def __init__(self, domain, service, data=None):
        self.domain = domain
        self.service = service
        self.data = data or {}


def callback(func):
    return func
