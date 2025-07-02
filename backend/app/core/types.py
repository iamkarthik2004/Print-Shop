from enum import Enum

class RoleTypes(str, Enum):
    user = "user"
    admin = "admin"

class SidesTypes(str, Enum):
    single = "single"
    double = "double"

class OrientationTypes(str, Enum):
    portrait = "portrait"
    landscape = "landscape"

class StatusTypes(str, Enum):
    waiting = "waiting"
    completed = "completed"

class PaymentStatusTypes(str, Enum):
    pending = "pending"
    paid = "paid"

class PaymentMethodTypes(str, Enum):
    online = "online"
    pickup = "pickup"
